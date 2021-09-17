/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * device attribute handler implementation for bf cpld driver
 */

#define pr_fmt(fmt) "%s:%s: " fmt, KBUILD_MODNAME,  __func__

#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/hwmon-sysfs.h>
#include "bf_module_util.h"
#include "bf_cpld_driver.h"

#define IPMI_CPLD_READ_CMD 0x20
#define IPMI_RESET_READ_CMD 0x64
#define IPMI_RESET_WRITE_CMD 0x65
#define IPMI_CPLD_READ_BD_VER_PARM 0x01
#define IPMI_CPLD_READ_TYPE_PARM 0x02
#define IPMI_CPLD_READ_REBOOT_CAUSE_PARM 0x03

#define SET_RESET_DISABLE 0
#define SET_RESET_ENABLE 1

extern struct bf_cpld_drv_data *g_data;

ATTR_SHOW_STR_FUNC(debug,
    "CPLD info:\n"
    "    Num of CPLD = 1\n"
    "\n"
    "Dump CPLD hardware version:\n"
    "    $ ipmitool raw 0x34 0x20 0x31\n"
    "        Output: major_version 1 byte, then minor_version 1 byte.\n"
    "\n"
    "Dump CPLD board version:\n"
    "    $ ipmitool raw 0x34 0x20 0x1\n"
    "        Output: board_version 1 byte.\n"
    "\n"
    "Dump CPLD type:\n"
    "    $ ipmitool raw 0x34 0x20 0x2\n"
    "        Output: type name in ASCII.\n"
    "\n"
    "Dump reboot cause:\n"
    "    $ ipmitool raw 0x34 0x20 0x3\n"
    "        Restart cause:\n"
    "            0x00: no reset/unknown\n"
    "            0x01: power domain standby reset\n"
    "            0x02: power domain main reset\n"
    "            0x03: front panel push button reset\n"
    "            0x04: on board debug push button reset\n"
    "            0x05: debug header reset\n"
    "            0x10: SW reg 0x31_bit4 hot-reset\n"
    "            0x11: SW reg 0x31_bit5 warm-reset\n"
    "            0x12: SW reg 0x31_bit6 cold-reset\n"
    "            0x13: SW reg 0x31_bit7 power-reset\n"
    "            0x20: BMC request reset\n"
    "            0x21: BMC request to reset Tofino\n"
    "            0x22: BMC request to reset COME\n"
    "            0x23: BMC request to reset main power domain\n"
    "            0x24: BMC request to reset all\n"
    "            0x25: BMC watchdog timer-1 reset\n"
    "            0x26: BMC watchdog timer-2 reset\n"
    "\n"
    "Dump reset status:\n"
    "    $ ipmitool raw 0x34 0x64\n"
    "        Output: reset_cpu 1 byte, then reset_mac 1 byte.\n"
    "                0=Normal, 1=Reset on.\n"
    "\n"
    "Set reset status:\n"
    "    $ ipmitool raw 0x34 0x65 <cpu_reset:{0|1}> <mac_reset:{0|1}>\n"
    "        where 1=Trigger reset, 0=Normal.\n"
)

ATTR_SHOW_NUM_FUNC(devnum, NUM_DEV);

static inline int get_cause_id_by_val(uint8_t val)
{
    switch(val){
    case 0x5:
        return REBOOT_CAUSE_NON_HARDWARE;
    case 0x1:
    case 0x2:
        return REBOOT_CAUSE_POWER_LOSS;
    case 0x0:
    case 0x12:
    case 0x13:
        return REBOOT_CAUSE_CPU_COLD_RESET;
    case 0x10:
    case 0x11:
        return REBOOT_CAUSE_CPU_WARM_RESET;
    case 0x20:
    case 0x22:
    case 0x23:
    case 0x24:
        return REBOOT_CAUSE_BMC_SHUTDOWN;
    case 0x3:
    case 0x4:
        return REBOOT_CAUSE_RESET_BUTTON_COLD_SHUTDOWN;
    default:
        return REBOOT_CAUSE_INVALID;
    }
}

struct bf_cpld_drv_data *update_cpld_status(unsigned char p_id)
{
    int reboot_cause_id, status = 0;

    if(time_before(jiffies, g_data->last_updated[p_id] + HZ * 5) &&
            g_data->valid[p_id])
        return g_data;

    g_data->valid[p_id] = 0;

    /* Get hw_version from ipmi */
    g_data->ipmi_tx_data[0] = I2C_CPLD_ADDRESS;
    status = ipmi_send_message(&g_data->ipmi, IPMI_CPLD_READ_CMD,
                                g_data->ipmi_tx_data, 1,
                                g_data->ipmi_resp[p_id].hw_version,
                                sizeof(g_data->ipmi_resp[p_id].hw_version));
    if (unlikely(status != 0))
        goto exit;

    if (unlikely(g_data->ipmi.rx_result != 0)) {
        status = -EIO;
        goto exit;
    }
    /* Get bd_version from ipmi */
    g_data->ipmi_tx_data[0] = IPMI_CPLD_READ_BD_VER_PARM;
    status = ipmi_send_message(&g_data->ipmi, IPMI_CPLD_READ_CMD,
                                g_data->ipmi_tx_data, 1,
                                g_data->ipmi_resp[p_id].bd_version,
                                sizeof(g_data->ipmi_resp[p_id].bd_version));
    if (unlikely(status != 0))
        goto exit;

    if (unlikely(g_data->ipmi.rx_result != 0)) {
        status = -EIO;
        goto exit;
    }
    /* Get bd_version from ipmi */
    g_data->ipmi_tx_data[0] = IPMI_CPLD_READ_TYPE_PARM;
    status = ipmi_send_message(&g_data->ipmi, IPMI_CPLD_READ_CMD,
                                g_data->ipmi_tx_data, 1,
                                g_data->ipmi_resp[p_id].type,
                                sizeof(g_data->ipmi_resp[p_id].type));
    if (unlikely(status != 0))
        goto exit;

    if (unlikely(g_data->ipmi.rx_result != 0)) {
        status = -EIO;
        goto exit;
    }
    /* Get reboot_cause from ipmi */
    g_data->ipmi_tx_data[0] = IPMI_CPLD_READ_REBOOT_CAUSE_PARM;
    status = ipmi_send_message(&g_data->ipmi, IPMI_CPLD_READ_CMD,
                                g_data->ipmi_tx_data, 1,
                                g_data->ipmi_resp[p_id].reboot_cause,
                                sizeof(g_data->ipmi_resp[p_id].reboot_cause));
    if (unlikely(status != 0))
        goto exit;

    if (unlikely(g_data->ipmi.rx_result != 0)) {
        status = -EIO;
        goto exit;
    }
    /* Translate fetched value to reboot_cause_id */
    reboot_cause_id = get_cause_id_by_val(g_data->ipmi_resp[p_id].reboot_cause[0]);
    if(reboot_cause_id != REBOOT_CAUSE_INVALID)
        g_data->reboot_cause_id[p_id] = reboot_cause_id;
    /* Get reset_status from ipmi */
    status = ipmi_send_message(&g_data->ipmi, IPMI_RESET_READ_CMD, NULL, 0,
                               g_data->ipmi_resp[p_id].reset_status,
                               sizeof(g_data->ipmi_resp[p_id].reset_status));
    if (unlikely(status != 0))
        goto exit;

    if (unlikely(g_data->ipmi.rx_result != 0)) {
        status = -EIO;
        goto exit;
    }

    g_data->last_updated[p_id] = jiffies;
    g_data->valid[p_id] = 1;

exit:
    return g_data;
}

ssize_t cpld_show(struct device *dev, struct device_attribute *da, char *buf)
{
    struct platform_device *pdev = to_platform_device(dev);
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
    unsigned char p_id = pdev->id;
    int val = 0, error = 0;
    char *str = NULL;
    char alias[5] = {0};
    bool is_show_int_hw = false;
    bool is_show_int = false;
    bool is_show_hex = false;
    unsigned char * const read_hw_ver = g_data->ipmi_resp[p_id].hw_version;

    mutex_lock(&g_data->update_lock);

    g_data = update_cpld_status(p_id);
    if (!g_data->valid) {
        error = -EIO;
        goto exit;
    }

    switch(attr->index) {
    case REBOOT_CAUSE_ATTR_ID:
        is_show_int = true;
        val = g_data->reboot_cause_id[p_id];
        break;
    case CPLD_ALIAS_ATTR_ID:
        sprintf(alias, "CPLD%d", (pdev->id)+1);
        str = alias;
        break;
    case CPLD_HW_VER_ATTR_ID:
        is_show_int_hw = true;
        break;
    case CPLD_BD_VER_ATTR_ID:
        is_show_hex = true;
        val = g_data->ipmi_resp[p_id].bd_version[0];
        break;
    case CPLD_TYPE_ATTR_ID:
        str = g_data->ipmi_resp[p_id].type;
        break;
    case CPLD_RST_CPU_ATTR_ID:
        is_show_int = true;
        val = g_data->ipmi_resp[p_id].reset_status[0];
        break;
    case CPLD_RST_MAC_ATTR_ID:
        is_show_int = true;
        val = g_data->ipmi_resp[p_id].reset_status[1];
        break;
    default:
        error = -EINVAL;
        goto exit;
    }

    mutex_unlock(&g_data->update_lock);

    if(str != NULL)
        return sprintf(buf, "%s\n", str);
    if(is_show_int_hw)
        return sprintf(buf, "%d.%d\n", read_hw_ver[0], read_hw_ver[1]);
    if(is_show_int)
        return sprintf(buf, "%d\n", val);
    if(is_show_hex)
        return sprintf(buf, "0x%x\n", val);

exit:
    mutex_unlock(&g_data->update_lock);
    return error;
}

ssize_t reset_show(struct device *dev, struct device_attribute *da, char *buf)
{
    struct platform_device *pdev = to_platform_device(dev);
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
    unsigned char p_id = pdev->id;
    int val = 0, error = 0;
    bool is_show_int = false;

    mutex_lock(&g_data->update_lock);

    g_data = update_cpld_status(p_id);
    if (!g_data->valid) {
        error = -EIO;
        goto exit;
    }

    switch(attr->index) {
    case CPLD_RST_CPU_ATTR_ID:
        is_show_int = true;
        val = g_data->ipmi_resp[p_id].reset_status[0];
        break;
    case CPLD_RST_MAC_ATTR_ID:
        is_show_int = true;
        val = g_data->ipmi_resp[p_id].reset_status[1];
        break;
    default:
        error = -EINVAL;
        goto exit;
    }

    mutex_unlock(&g_data->update_lock);

    if(is_show_int)
        return sprintf(buf, "%d\n", val);


exit:
    mutex_unlock(&g_data->update_lock);
    return error;
}

ssize_t reset_store(struct device *dev, struct device_attribute *da,
                            const char *buf, size_t count)
{
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);

    int status;
    long reset_status;

     /*only handle SYSLED_SYS_STATUS_ATTR_ID and SYSLED_LOC_STATUS_ATTR_ID now*/
    if( (attr->index != CPLD_RST_CPU_ATTR_ID) &&
        (attr->index != CPLD_RST_MAC_ATTR_ID) )
        return -EINVAL;

    status = kstrtol(buf, 10, &reset_status);
    if (status)
        return status;

    if(reset_status == SET_RESET_DISABLE) {
        return -EINVAL;
    }

    mutex_lock(&g_data->update_lock);

    switch(attr->index) {
    case CPLD_RST_CPU_ATTR_ID:
        g_data->ipmi_tx_reset_data[0] = SET_RESET_ENABLE;
        g_data->ipmi_tx_reset_data[1] = SET_RESET_DISABLE;
        break;
    case CPLD_RST_MAC_ATTR_ID:
        g_data->ipmi_tx_reset_data[0] = SET_RESET_DISABLE;
        g_data->ipmi_tx_reset_data[1] = SET_RESET_ENABLE;
        break;
    default:
        status = -EINVAL;
        goto exit;
    }

    /* Send IPMI write command */
    status = ipmi_send_message(&g_data->ipmi, IPMI_RESET_WRITE_CMD,
                                g_data->ipmi_tx_reset_data,
                                sizeof(g_data->ipmi_tx_reset_data),
                                NULL, 0);
    if (unlikely(status != 0))
        goto exit;

    if (unlikely(g_data->ipmi.rx_result != 0)) {
        status = -EIO;
        goto exit;
    }

    status = count;

exit:
    mutex_unlock(&g_data->update_lock);
    return status;
}
