/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * device attribute handler implementation for bf watchdog driver
 */

#define pr_fmt(fmt) "%s:%s: " fmt, KBUILD_MODNAME,  __func__

#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/hwmon-sysfs.h>
#include "bf_module_util.h"
#include "bf_watchdog_driver.h"

extern struct bf_wdt_drv_data *g_data;

#define IPMI_WDT_READ_CMD 0x9E
#define IPMI_WDT_WRITE_CMD 0x9F
#define IPMI_WDT_READ_ENABLE_CMD 0x1
#define IPMI_WDT_READ_TIMELEFT_CMD 0x3
#define IPMI_WDT_WRITE_ENABLE_CMD 0x1
#define IPMI_WDT_WRITE_TIMELEFT_CMD 0x2

ATTR_SHOW_STR_FUNC(identify, "EC_Watchdog");

ATTR_SHOW_STR_FUNC(debug,  //SEAN TODO
    "+++DUMMY content+++\n"
    "wdt present:\n"
    "  0-->present\n"
    "  1-->unpresent\n"
    "  bit0-->wdt1, bit4-->wdt2\n"
    "  eg:\n"
    "  1.show present info: i2cget -f -y 2 0x1d 0x34\n"
    "\n"
    "wdt data:\n"
    "                    path\n"
    "  wdt1             81-0058\n"
    "  wdt2             82-0058\n"
    "                    sysfs\n"
    "  temp     :    temp1_input\n"
    "  wdt_speed:    wdt1_input\n"
    "  i_in     :    curr1_input\n"
    "  v_in     :    in1_input\n"
    "  p_in     :    power1_input\n"
    "  i_out    :    curr2_input\n"
    "  v_out    :    in2_input\n"
    "  p_out    :    power2_input\n"
    "  eg:\n"
    "  1.show data info: cat /sys/bus/i2c/devices/$path/hwmon/hwmon*/$sysfs\n"
    "wdt vendor, model, serial, version:\n"
    "  wdt1-->$bus = 81, $addr = 0x50\n"
    "  wdt2-->$bus = 82, $addr = 0x50\n"
    "  eg:\n"
    "  1.show all info: i2cdump -f -y $bus $addr\n"
    "---DUMMY content---\n"
)

static int wdt_set_enable(bool enable)
{
    int status;
    uint8_t *tx_data = g_data->ipmi_tx_data;

    tx_data[0] = IPMI_WDT_WRITE_ENABLE_CMD;
    tx_data[1] = (enable)? 1 : 0;
    status = ipmi_send_message(&g_data->ipmi, IPMI_WDT_WRITE_CMD,
                            tx_data, 2, NULL, 0);
    if (unlikely(status != 0))
        goto exit;

    if (unlikely(g_data->ipmi.rx_result != 0)) {
        status = -EIO;
        goto exit;
    }

    g_data->wdt_enable = (enable)? 1 : 0;
    return 0;
exit:
    return status;
}

static int wdt_set_timeleft(uint8_t time)
{
    int status;
    uint8_t *tx_data = g_data->ipmi_tx_data;

    tx_data[0] = IPMI_WDT_WRITE_TIMELEFT_CMD;
    tx_data[1] = time;
    status = ipmi_send_message(&g_data->ipmi, IPMI_WDT_WRITE_CMD,
                            tx_data, 2, NULL, 0);
    if (unlikely(status != 0))
        goto exit;

    if (unlikely(g_data->ipmi.rx_result != 0)) {
        status = -EIO;
        goto exit;
    }

    g_data->wdt_timeleft = time;
    return 0;
exit:
    return status;
}


static struct bf_wdt_drv_data *update_wdt_status(void)
{
    uint8_t sub_cmd[] = {IPMI_WDT_READ_ENABLE_CMD, IPMI_WDT_READ_TIMELEFT_CMD};
    uint8_t *rx_data[] = {&g_data->wdt_enable, &g_data->wdt_timeleft};
    int i, status;

    if (time_before(jiffies, g_data->last_updated + HZ * 1) && g_data->valid)
        return g_data;

    g_data->valid = 0;

    for(i = 0 ; i < ARRAY_SIZE(sub_cmd) ; i++) {
        status = ipmi_send_message(&g_data->ipmi, IPMI_WDT_READ_CMD,
                                &sub_cmd[i], sizeof(sub_cmd[i]),
                                rx_data[i], sizeof(*rx_data[i]));
        if (unlikely(status != 0))
            goto exit;

        if (unlikely(g_data->ipmi.rx_result != 0)) {
            status = -EIO;
            goto exit;
        }
    }

    g_data->last_updated = jiffies;
    g_data->valid = 1;
exit:
    return g_data;
}

ssize_t wdt_show(struct device *dev, struct device_attribute *da,
                            char *buf)
{
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
    ssize_t error;

    const char * str = NULL;
    int val;

    mutex_lock(&g_data->update_lock);

    g_data = update_wdt_status();
    if (!g_data->valid) {
        error = -EIO;
        goto exit;
    }

    switch (attr->index) {
    case ENABLE_ATTR_ID:
        val = (g_data->wdt_enable == 0)? 0 : 1;
        break;
    case STATE_ATTR_ID:
        str = (g_data->wdt_enable == 0)? "inactive" : "active";
        break;
    case TIMELEFT_ATTR_ID:
        val = g_data->wdt_timeleft;
        break;
    case TIMEOUT_ATTR_ID:
        val = g_data->wdt_timeout;
        break;
    default:
        error = -EINVAL;
        goto exit;
    }

    mutex_unlock(&g_data->update_lock);
    if(str)
        return sprintf(buf, "%s\n", str);
    return sprintf(buf, "%d\n", val);
exit:
    mutex_unlock(&g_data->update_lock);
    return error;
}

ssize_t wdt_store(struct device *dev, struct device_attribute *da,
                            const char *buf, size_t count)
{
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
    int error;
    long val;

    error = kstrtol(buf, 10, &val);
    if (error)
        return error;

    mutex_lock(&g_data->update_lock);

    switch (attr->index) {
    case ENABLE_ATTR_ID:
        error = wdt_set_enable((val==0)? false : true);
        if(error < 0)
            goto exit;
        break;
    case TIMEOUT_ATTR_ID:
        g_data->wdt_timeout = (uint8_t) val;
        /* NOTE: no break statement here by purpose. */
    case RESET_ATTR_ID:
        error = wdt_set_timeleft(g_data->wdt_timeout);
        if(error < 0)
            goto exit;
        break;
    default:
        error = -EINVAL;
        break;
    }

    mutex_unlock(&g_data->update_lock);
    return count;

exit:
    mutex_unlock(&g_data->update_lock);
    return error;
}
