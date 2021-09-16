/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * device attribute handler implementation for bf sysled driver
 */

#define pr_fmt(fmt) "%s:%s: " fmt, KBUILD_MODNAME,  __func__

#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/hwmon-sysfs.h>
#include "bf_module_util.h"
#include "bf_sysled_driver.h"

#define IPMI_SYSLED_READ_CMD 0x1a
#define IPMI_SYSLED_WRITE_CMD 0x1b


extern struct bf_sysled_drv_data *g_data;

//SEAN TODO
ATTR_SHOW_STR_FUNC(debug,
    "+++DUMMY content+++\n"
    "psu present:\n"
    "  0-->present\n"
    "  1-->unpresent\n"
    "  bit0-->psu1, bit4-->psu2\n"
    "  eg:\n"
    "  1.show present info: i2cget -f -y 2 0x1d 0x34\n"
    "\n"
    "psu data:\n"
    "                    path\n"
    "  psu1             81-0058\n"
    "  psu2             82-0058\n"
    "                    sysfs\n"
    "  temp     :    temp1_input\n"
    "  fan_speed:    fan1_input\n"
    "  i_in     :    curr1_input\n"
    "  v_in     :    in1_input\n"
    "  p_in     :    power1_input\n"
    "  i_out    :    curr2_input\n"
    "  v_out    :    in2_input\n"
    "  p_out    :    power2_input\n"
    "  eg:\n"
    "  1.show data info: cat /sys/bus/i2c/devices/$path/hwmon/hwmon*/$sysfs\n"
    "psu vendor, model, serial, version:\n"
    "  psu1-->$bus = 81, $addr = 0x50\n"
    "  psu2-->$bus = 82, $addr = 0x50\n"
    "  eg:\n"
    "  1.show all info: i2cdump -f -y $bus $addr\n"
    "---DUMMY content---\n"
)

static inline int get_color_by_state(unsigned char val)
{
    switch(val){
    case 1: return COLOR_BLUE;
    case 2: return COLOR_GREEN;
    case 4: return COLOR_RED;
    case 9: return COLOR_BLUE_BLINK;
    case 10: return COLOR_GREEN_BLINK;
    case 12: return COLOR_RED_BLINK;
    default: return COLOR_FAILED;
    }
}

static inline int get_status_by_color(unsigned char val)
{
    switch(val){
    case COLOR_BLUE: return 0x1; /*Bit0*/
    case COLOR_GREEN: return 0x2; /*Bit1*/
    case COLOR_RED: return 0x4; /*Bit2*/
    case COLOR_BLUE_BLINK: return 0x9; /*Bit0+Bit3*/
    case COLOR_GREEN_BLINK: return 0xa; /*Bit1+Bit3*/
    case COLOR_RED_BLINK: return 0xc; /*Bit2+Bit3*/
    default: return 0x0;
    }
}


static struct bf_sysled_drv_data *update_sysled_status(void)
{
    int status = 0;

    if (time_before(jiffies, g_data->last_updated + HZ * 5) && g_data->valid)
        return g_data;

    g_data->valid = 0;

    /* Get status from ipmi */
    status = ipmi_send_message(&g_data->ipmi, IPMI_SYSLED_READ_CMD, NULL, 0,
                               g_data->ipmi_resp, sizeof(g_data->ipmi_resp));
    if (unlikely(status != 0))
        goto exit;

    if (unlikely(g_data->ipmi.rx_result != 0)) {
        status = -EIO;
        goto exit;
    }

    g_data->last_updated = jiffies;
    g_data->valid = 1;

exit:
    return g_data;
}

ssize_t sysled_show(struct device *dev, struct device_attribute *da, char *buf)
{
    struct platform_device *pdev = to_platform_device(dev);
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);

    int val = 0, error = 0;
    unsigned char * const read_status = g_data->ipmi_resp;

    bf_print("pdev_id=%d, attr_name(%s) attr_idx=%d\n", pdev->id, da->attr.name, attr->index);//SEAN TODO

    mutex_lock(&g_data->update_lock);

    g_data = update_sysled_status();
    if (!g_data->valid) {
        error = -EIO;
        goto exit;
    }

    switch(attr->index) {
    case SYSLED_SYS_STATUS_ATTR_ID:
        val = get_color_by_state(read_status[0]);
        break;
    case SYSLED_LOC_STATUS_ATTR_ID:
        val = get_color_by_state(read_status[1]);
        break;
    default:
        error = -EINVAL;
        goto exit;
    }

    mutex_unlock(&g_data->update_lock);
    return sprintf(buf, "%d\n", val);

exit:
    mutex_unlock(&g_data->update_lock);
    return error;
}

ssize_t sysled_store(struct device *dev, struct device_attribute *da,
                            const char *buf, size_t count)
{
    struct platform_device *pdev = to_platform_device(dev);
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);

    int status;
    long led_status;
    unsigned char * const read_status = g_data->ipmi_resp;

    bf_print("dev_id=%d, attr_name(%s) attr_idx=%d\n", pdev->id, da->attr.name, attr->index); //SEAN TODO

     /* This function now only handle SYSLED_SYS_STATUS_ATTR_ID and SYSLED_LOC_STATUS_ATTR_ID */
    if( (attr->index != SYSLED_SYS_STATUS_ATTR_ID) &&
        (attr->index != SYSLED_LOC_STATUS_ATTR_ID) )
        return -EINVAL;

    status = kstrtol(buf, 10, &led_status);
    if (status)
        return status;

    mutex_lock(&g_data->update_lock);
    g_data = update_sysled_status();

    switch(attr->index) {
    case SYSLED_SYS_STATUS_ATTR_ID:
        g_data->ipmi_tx_data[0] = get_status_by_color(led_status);
        g_data->ipmi_tx_data[1] = read_status[1];
        break;
    case SYSLED_LOC_STATUS_ATTR_ID:
        g_data->ipmi_tx_data[0] = read_status[0];
        g_data->ipmi_tx_data[1] = get_status_by_color(led_status);
        break;
    default:
        status = -EINVAL;
        goto exit;
    }

    /* Send IPMI write command */
    status = ipmi_send_message(&g_data->ipmi, IPMI_SYSLED_WRITE_CMD,
                                g_data->ipmi_tx_data, sizeof(g_data->ipmi_tx_data),
                                NULL, 0);
    if (unlikely(status != 0))
        goto exit;

    if (unlikely(g_data->ipmi.rx_result != 0)) {
        status = -EIO;
        goto exit;
    }

    /* Update pwm to ipmi_resp buffer to prevent from the impact of lazy update */
    if( attr->index == SYSLED_SYS_STATUS_ATTR_ID)
        read_status[0] = g_data->ipmi_tx_data[0];
    if( attr->index == SYSLED_LOC_STATUS_ATTR_ID)
        read_status[1] = g_data->ipmi_tx_data[1];

    status = count;

exit:
    mutex_unlock(&g_data->update_lock);
    return status;
}
