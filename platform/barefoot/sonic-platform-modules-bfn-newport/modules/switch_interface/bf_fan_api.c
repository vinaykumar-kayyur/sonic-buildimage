/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * device attribute handler implementation for bf fan driver
 */

#define pr_fmt(fmt) "%s:%s: " fmt, KBUILD_MODNAME,  __func__

#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/hwmon-sysfs.h>
#include "bf_module_util.h"
#include "bf_fan_driver.h"

extern struct bf_fan_drv_data *g_data;

#define IPMI_FAN_READ_CMD 0x14
#define IPMI_FAN_READ_CPLD_VER_CMD 0x1
#define B2F (1)
#define F2B (0)

ATTR_SHOW_STR_FUNC(debug,  //SEAN TODO
    "+++DUMMY content+++\n"
    "fan present:\n"
    "  0-->present\n"
    "  1-->unpresent\n"
    "  bit0-->fan1, bit4-->fan2\n"
    "  eg:\n"
    "  1.show present info: i2cget -f -y 2 0x1d 0x34\n"
    "\n"
    "fan data:\n"
    "                    path\n"
    "  fan1             81-0058\n"
    "  fan2             82-0058\n"
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
    "fan vendor, model, serial, version:\n"
    "  fan1-->$bus = 81, $addr = 0x50\n"
    "  fan2-->$bus = 82, $addr = 0x50\n"
    "  eg:\n"
    "  1.show all info: i2cdump -f -y $bus $addr\n"
    "---DUMMY content---\n"
)

ATTR_SHOW_NUM_FUNC(num_fan, NUM_FAN)
ATTR_SHOW_NUM_FUNC(num_motor, MOTOR_PER_FAN)

static struct bf_fan_drv_data *update_fan_update_device(void)
{
    int status = 0;

    if (time_before(jiffies, g_data->last_updated + HZ * 5) && g_data->valid)
        return g_data;

    g_data->valid = 0;
    status = ipmi_send_message(&g_data->ipmi, IPMI_FAN_READ_CMD, NULL, 0,
                               g_data->ipmi_resp, sizeof(g_data->ipmi_resp));
    if (unlikely(status != 0))
        goto exit;

    if (unlikely(g_data->ipmi.rx_result != 0)) {
        status = -EIO;
        goto exit;
    }

    //SEAN TODO :get g_data->ipmi_resp_cpld_ver;
    g_data->ipmi_tx_data[0] = IPMI_FAN_READ_CPLD_VER_CMD;
    status = ipmi_send_message(&g_data->ipmi, IPMI_FAN_READ_CMD,
                                g_data->ipmi_tx_data, 1,
                                &g_data->ipmi_resp_cpld_ver,
                                sizeof(g_data->ipmi_resp_cpld_ver));
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

    ////////SEAN TODO: delete experimental data.
    // char dummy_data[] = {
    //     0x01, 0x07, 0xb4, 0x2d,
    //     0x01, 0x07, 0x50, 0x2d,
    //     0x01, 0x07, 0x50, 0x2d,
    //     0x01, 0x07, 0xec, 0x2c,
    //     0x01, 0x07, 0xec, 0x2c,
    //     0x01, 0x07, 0x7c, 0x2e,
    //     0xff, 0xff, 0x48, 0x26,
    //     0xff, 0xff, 0xe4, 0x25,
    //     0xff, 0xff, 0x48, 0x26,
    //     0xff, 0xff, 0xe4, 0x25,
    //     0xff, 0xff, 0x80, 0x25,
    //     0xff, 0xff, 0xac, 0x26,
    //     0x00, 0x00
    // };
    // int i;


    // for(i = 0 ; i < sizeof(dummy_data) ; i++){
    //     g_data->ipmi_resp[i] = dummy_data[i];
    // }
    // g_data->ipmi_resp_cpld_ver = 0x30;
    // g_data->valid = 1;

    // return g_data;
}

ssize_t fan_num_show(struct device *dev, struct device_attribute *da,
                            char *buf)
{
    struct platform_device *pdev = to_platform_device(dev);
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
    int f_id = pdev->id;
    int value = 0;
    int index = 0;
    int error = 0;
    int present = 0;
    bf_print("dev_id=%d, attr_name(%s) attr_idx=%d\n", pdev->id, da->attr.name, attr->index); //SEAN TODO

    mutex_lock(&g_data->update_lock);

    g_data = update_fan_update_device();
    if (!g_data->valid) {
        error = -EIO;
        goto exit;
    }

    index = f_id * FAN_DATA_COUNT;
    present = !!g_data->ipmi_resp[index + FAN_PRESENT];

    switch (attr->index) {
    case FAN_HWVER_ATTR_ID:
        value = g_data->ipmi_resp_cpld_ver;
        break;
    case FAN_LED_ATTR_ID:
        value = 0;//SEAN TODO , also need to check if it depend on present status.
        break;
    case FAN_STATUS_ATTR_ID:
        value = present;
        break;
    default:
        error = -EINVAL;
        goto exit;
    }

    mutex_unlock(&g_data->update_lock);
    return sprintf(buf, "%d\n", present ? value : 0);

exit:
    mutex_unlock(&g_data->update_lock);
    return error;
}

ssize_t motor_num_show(struct device *dev, struct device_attribute *da,
                            char *buf)
{
    struct platform_device *pdev = to_platform_device(dev);
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
    int m_id = pdev->id % MOTOR_PER_FAN;
    int f_id = pdev->id / MOTOR_PER_FAN;
    int value = 0;
    int index = 0;
    int error = 0;
    int present = 0;
    bf_print("dev_id=%d, attr_name(%s) attr_idx=%d\n", pdev->id, da->attr.name, attr->index); //SEAN TODO

    mutex_lock(&g_data->update_lock);

    g_data = update_fan_update_device();
    if (!g_data->valid) {
        error = -EIO;
        goto exit;
    }

    index = f_id * FAN_DATA_COUNT;
    present = !!g_data->ipmi_resp[index + FAN_PRESENT];

    switch (attr->index) {
    case MOTOR_RATIO_ATTR_ID:
        value = (g_data->ipmi_resp[index + FAN_PWM] + 1) * 625 / 100;
        break;
    case MOTOR_DIR_ATTR_ID:
        index = NUM_MOTOR * FAN_DATA_COUNT;
        value = g_data->ipmi_resp[index] | (g_data->ipmi_resp[index+1] << 8);
        value = (value & BIT(f_id))? B2F : F2B;
        break;
    case MOTOR_SPEED_ATTR_ID:
        index += (m_id)? (NUM_FAN * FAN_DATA_COUNT): 0;
        value = (int)g_data->ipmi_resp[index + FAN_SPEED0] |
                (int)g_data->ipmi_resp[index + FAN_SPEED1] << 8;
        break;
    default:
        error = -EINVAL;
        goto exit;
    }

    mutex_unlock(&g_data->update_lock);
    return sprintf(buf, "%d\n", present ? value : 0);

exit:
    mutex_unlock(&g_data->update_lock);
    return error;
}

ssize_t motor_num_store(struct device *dev, struct device_attribute *da,
                            const char *buf, size_t count)
{
    struct platform_device *pdev = to_platform_device(dev);
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
    bf_print("dev_id=%d, attr_name(%s) attr_idx=%d\n", pdev->id, da->attr.name, attr->index); //SEAN TODO
    //SEAN TODO:
    return count;
}
