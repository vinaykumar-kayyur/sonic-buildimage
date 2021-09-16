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

ATTR_SHOW_STR_FUNC(debug,
    "Dump watchdog enable status:\n"
    "    $ ipmitool raw 0x34 0x9e 0x1\n"
    "        Output: 0=disable, 1=enable.\n"
    "\n"
    "Dump watchdog timeleft:\n"
    "    $ ipmitool raw 0x34 0x9e 0x3\n"
    "        Output: current countdown value, 1 byte only.\n"
    "\n"
    "Set watchdog enable/disable:\n"
    "    $ ipmitool raw 0x34 0x9f 0x1 <status{0|1}>\n"
    "        where 0=disable, 1=enable\n"
    "\n"
    "Set watchdog timeleft:\n"
    "    $ ipmitool raw 0x34 0x9f 0x2 <timeleft>\n"
    "        where timeleft = 0~0xFF\n"
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
