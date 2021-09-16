/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * device attribute handler implementation for bf psu driver
 */

#define pr_fmt(fmt) "%s:%s: " fmt, KBUILD_MODNAME,  __func__

#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/hwmon-sysfs.h>
#include "bf_module_util.h"
#include "bf_psu_driver.h"

#define IPMI_PSU_READ_CMD 0x16
#define IPMI_PSU_MODEL_NAME_CMD 0x10
#define IPMI_PSU_SERIAL_NUM_CMD 0x11
#define IPMI_PSU_VENDOR_CMD 0x12
#define IPMI_PSU_DATE_CMD 0x14
#define IPMI_PSU_PART_NUM__CMD 0x15
#define IPMI_PSU_HW_VER_CMD 0x16
#define IPMI_PSU_ALARM_CMD 0x17
#define IPMI_PSU_ALARM_THRESHOLD 0x18

extern struct bf_psu_drv_data *g_data;

ATTR_SHOW_STR_FUNC(debug,
    "PSU Info:\n"
    "    num of PSUs = 2\n"
    "    num of temp sensors per PSU = 3\n"
    "\n"
    "Get PSU status:\n"
    "    $ ipmitool raw 0x34 0x16 <PSU_ID>\n"
    "    Output format:\n"
    "        OFFSET SIZE FIELD         DESCRIPTION\n"
    "        -------------------------------------------------------------\n"
    "        0      1    present       0:Plugged, 1:Unplugged\n"
    "        1      1    temp_fault    0:Normal, 1:temp fault\n"
    "        2      1    power_good    0:Failed, 1:OK\n"
    "        4      1    over_voltage  0:Normal, 1:voltage over threshold\n"
    "        5      1    over_current  0:Normal, 1:current over threshold\n"
    "        7      3    VIN           input voltage in milliVolt.\n"
    "        10     3    VOUT          output voltage in milliVolt.\n"
    "        13     3    IIN           input current in milliAmpere.\n"
    "        16     3    IOUT          output current in milliAmpere.\n"
    "        19     4    PIN           input power in microWatt.\n"
    "        23     4    POUT          output power in microWatt.\n"
    "        27     2    TEMP1         Temperture sensor1 in milliDegree.\n"
    "        29     2    TEMP2         Temperture sensor2 in milliDegree.\n"
    "        31     2    TEMP3         Temperture sensor3 in milliDegree.\n"
    "        33     2    fan_speed     Fan speed in RPM.\n"
    "        36     1    fan_fault     0:Normal, 1:fan fault\n"
    "    NOTE: all numbers are represnted in littel-endian.\n"
    "\n"
    "Get PSU model name:\n"
    "    $ ipmitool raw 0x34 0x16 <PSU_ID> 0x10\n"
    "\n"
    "Get PSU serial number:\n"
    "    $ ipmitool raw 0x34 0x16 <PSU_ID> 0x11\n"
    "\n"
    "Get PSU vendor:\n"
    "    $ ipmitool raw 0x34 0x16 <PSU_ID> 0x12\n"
    "\n"
    "Get PSU date:\n"
    "    $ ipmitool raw 0x34 0x16 <PSU_ID> 0x14\n"
    "        Format: YYMM in ASCII.\n"
    "\n"
    "Get PSU part number:\n"
    "    $ ipmitool raw 0x34 0x16 <PSU_ID> 0x15\n"
    "\n"
    "Get PSU hardware version:\n"
    "    $ ipmitool raw 0x34 0x16 <PSU_ID> 0x16\n"
    "\n"
    "Get PSU alarm:\n"
    "    $ ipmitool raw 0x34 0x16 <PSU_ID> 0x17\n"
    "\n"
    "Get PSU voltage/current thresholds:\n"
    "    $ ipmitool raw 0x34 0x16 <PSU_ID> 0x18\n"
    "    Output format:\n"
    "        OFFSET SIZE FIELD    DESCRIPTION\n"
    "        -------------------------------------------------------------\n"
    "        0      3    VIN_MAX  0:Plugged, 1:Unplugged\n"
    "        3      3    IIN_MAX  0:Normal, 1:temp fault\n"
)

ATTR_SHOW_NUM_FUNC(devnum, NUM_DEV)
ATTR_SHOW_NUM_FUNC(num_temp, NUM_TEMP_PER_DEV)

static inline ssize_t sprintf_float(char *buf, int num, int present)
{
    if(present)
        return sprintf(buf, "%d.%03d\n", num / 1000, num % 1000);
    else
        return sprintf(buf, "0.000\n");
}

static inline u32 carray_to_u32(unsigned char *array, size_t bytelen)
{
    u32 val = 0;
    size_t i;
    BUILD_BUG_ON(bytelen > 4);

    for(i = 0 ; i < bytelen ; i++){
        val |= ((u32)*(array+i)) << i*8;
    }
    return val;
}

static struct bf_psu_drv_data *update_psu_status(unsigned char p_id)
{
    int status = 0;

    if(time_before(jiffies, g_data->last_updated[p_id] + HZ * 5) &&
            g_data->valid[p_id])
        return g_data;

    g_data->valid[p_id] = 0;
    /* To be compatible for older BMC firmware */
    g_data->ipmi_resp[p_id].status[PSU_VOUT_MODE] = 0xff;

    /* Get status from ipmi */
    g_data->ipmi_tx_data[0] = p_id + 1; /* id for ipmi start from 1 */
    status = ipmi_send_message(&g_data->ipmi, IPMI_PSU_READ_CMD,
                                g_data->ipmi_tx_data, 1,
                                g_data->ipmi_resp[p_id].status,
                                sizeof(g_data->ipmi_resp[p_id].status));
    if (unlikely(status != 0))
        goto exit;

    if (unlikely(g_data->ipmi.rx_result != 0)) {
        status = -EIO;
        goto exit;
    }

    /* Get model name from ipmi */
    g_data->ipmi_tx_data[1] = IPMI_PSU_MODEL_NAME_CMD;
    status = ipmi_send_message(&g_data->ipmi, IPMI_PSU_READ_CMD,
                                g_data->ipmi_tx_data, 2,
                                g_data->ipmi_resp[p_id].model,
                                sizeof(g_data->ipmi_resp[p_id].model) - 1);
    if (unlikely(status != 0))
        goto exit;

    if (unlikely(g_data->ipmi.rx_result != 0)) {
        status = -EIO;
        goto exit;
    }

    /* Get serial number from ipmi */
    g_data->ipmi_tx_data[1] = IPMI_PSU_SERIAL_NUM_CMD;
    status = ipmi_send_message(&g_data->ipmi, IPMI_PSU_READ_CMD,
                                g_data->ipmi_tx_data, 2,
                                g_data->ipmi_resp[p_id].serial,
                                sizeof(g_data->ipmi_resp[p_id].serial) - 1);
    if (unlikely(status != 0))
        goto exit;

    if (unlikely(g_data->ipmi.rx_result != 0)) {
        status = -EIO;
        goto exit;
    }

    /* Get vendor from ipmi */
    g_data->ipmi_tx_data[1] = IPMI_PSU_VENDOR_CMD;
    status = ipmi_send_message(&g_data->ipmi, IPMI_PSU_READ_CMD,
                                g_data->ipmi_tx_data, 2,
                                g_data->ipmi_resp[p_id].vendor,
                                sizeof(g_data->ipmi_resp[p_id].vendor) - 1);
    if (unlikely(status != 0))
        goto exit;

    if (unlikely(g_data->ipmi.rx_result != 0)) {
        status = -EIO;
        goto exit;
    }
    /* Get date from ipmi */
    g_data->ipmi_tx_data[1] = IPMI_PSU_DATE_CMD;
    status = ipmi_send_message(&g_data->ipmi, IPMI_PSU_READ_CMD,
                                g_data->ipmi_tx_data, 2,
                                g_data->ipmi_resp[p_id].date,
                                sizeof(g_data->ipmi_resp[p_id].date) - 1);
    if (unlikely(status != 0))
        goto exit;

    if (unlikely(g_data->ipmi.rx_result != 0)) {
        status = -EIO;
        goto exit;
    }
    /*Get hardware version for ipmi*/
    g_data->ipmi_tx_data[1] = IPMI_PSU_HW_VER_CMD;
    status = ipmi_send_message(&g_data->ipmi, IPMI_PSU_READ_CMD,
                                g_data->ipmi_tx_data, 2,
                                &g_data->ipmi_resp[p_id].hw_ver,
                                sizeof(g_data->ipmi_resp[p_id].hw_ver));
    if (unlikely(status != 0))
        goto exit;

    if (unlikely(g_data->ipmi.rx_result != 0)) {
        status = -EIO;
        goto exit;
    }
    /* Get part number from ipmi */
    g_data->ipmi_tx_data[1] = IPMI_PSU_PART_NUM__CMD;
    status = ipmi_send_message(&g_data->ipmi, IPMI_PSU_READ_CMD,
                                g_data->ipmi_tx_data, 2,
                                g_data->ipmi_resp[p_id].part_num,
                                sizeof(g_data->ipmi_resp[p_id].part_num) - 1);
    if (unlikely(status != 0))
        goto exit;

    if (unlikely(g_data->ipmi.rx_result != 0)) {
        status = -EIO;
        goto exit;
    }
    /*Get alarm threshold for ipmi*/
    g_data->ipmi_tx_data[1] = IPMI_PSU_ALARM_THRESHOLD;
    status = ipmi_send_message(&g_data->ipmi, IPMI_PSU_READ_CMD,
                                g_data->ipmi_tx_data, 2,
                                g_data->ipmi_resp[p_id].alarm_threshold,
                                sizeof(g_data->ipmi_resp[p_id].alarm_threshold));
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

ssize_t psu_TBD_show(struct device *dev, struct device_attribute *da, // SEAN TODO
                            char *buf)
{
    struct platform_device *pdev = to_platform_device(dev);
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
    bf_print("pdev_id=%d, attr_name(%s) attr_idx=%d\n", pdev->id, da->attr.name, attr->index);//SEAN TODO
    return 0;
}

ssize_t psu_show(struct device *dev, struct device_attribute *da, char *buf)
{
    struct platform_device *pdev = to_platform_device(dev);
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
    u32 val = 0;
    unsigned char p_id = pdev->id;
    size_t bytelen = 0xFF; /* Need to assign it to assemble bytes to num.*/
    size_t index = 0;
    int present = 0, error = 0;
    bool is_show_int = false;
    bool is_show_hex = false;
    char *str = NULL;
    int divisor = 1;
    unsigned char * const read_status = g_data->ipmi_resp[p_id].status;
    unsigned char * const read_alarm_threshold = g_data->ipmi_resp[p_id].alarm_threshold;
    bf_print("pdev_id=%d, attr_name(%s) attr_idx=%d\n", pdev->id, da->attr.name, attr->index);//SEAN TODO

    mutex_lock(&g_data->update_lock);

    g_data = update_psu_status(p_id);
    if (!g_data->valid[p_id]) {
        error = -EIO;
        goto exit;
    }

    present = !!(read_status[PSU_PRESENT]);

    switch(attr->index) {
    case PSU_MODEL_ATTR_ID:
        str = g_data->ipmi_resp[p_id].model;
        break;
    case PSU_SERIAL_ATTR_ID:
        str = g_data->ipmi_resp[p_id].serial;
        break;
    case PSU_VENDOR_ATTR_ID:
        str = g_data->ipmi_resp[p_id].vendor;
        break;
    case PSU_DATE_ATTR_ID:
        str = g_data->ipmi_resp[p_id].date;
        break;
    case PSU_HW_VER_ATTR_ID:
        is_show_hex = true;
        val = g_data->ipmi_resp[p_id].hw_ver;
        break;
    case PSU_PART_NUM_ATTR_ID:
        str = g_data->ipmi_resp[p_id].part_num;
        break;
    case PSU_ALARM_TH_CURR_ATTR_ID:
        index = 3;
        bytelen = 3;
        break;
    case PSU_ALARM_TH_VOL_ATTR_ID:
        index = 0;
        bytelen = 3;
        break;
    case PSU_IIN_ATTR_ID:
        index = PSU_IIN0;
        bytelen = 3;
        break;
    case PSU_VIN_ATTR_ID:
        index = PSU_VIN0;
        bytelen = 3;
        break;
    case PSU_PIN_ATTR_ID:
        index = PSU_PIN0;
        bytelen = 4;
        divisor = 1000; // to miniwatt
        break;
    case PSU_IOUT_ATTR_ID:
        index = PSU_IOUT0;
        bytelen = 3;
        break;
    case PSU_VOUT_ATTR_ID:
        index = PSU_VOUT0;
        bytelen = 3;
        break;
    case PSU_POUT_ATTR_ID:
        index = PSU_POUT0;
        bytelen = 4;
        divisor = 1000; // to miniwatt
        break;
    case PSU_FAN_SPEED_ATTR_ID:
        is_show_int = true;
        index = PSU_FAN0;
        bytelen = 2;
        break;
    case PSU_STATUS_ATTR_ID:
        is_show_int = true;
        if(present)
            val = (read_status[PSU_POWER_GOOD_CPLD] == 1)? 1 : 2;
        else
            val = 0;
        break;
    case PSU_ALARM_ATTR_ID:
        is_show_int = true;
        if(present) {
            val += (read_status[PSU_TEMP_FAULT] == 1)?   1 : 0;
            val += (read_status[PSU_FAN_FAULT] == 1)?    2 : 0;
            val += (read_status[PSU_OVER_VOLTAGE] == 1)? 4 : 0;
        }
        else
            val = 0;
        break;
    default:
        error = -EINVAL;
        goto exit;
    }

    if(bytelen <= 0x4)
    {
        if( ((attr->index)==PSU_ALARM_TH_VOL_ATTR_ID) || ((attr->index)==PSU_ALARM_TH_CURR_ATTR_ID) ) {
            val = carray_to_u32(&read_alarm_threshold[index], bytelen);
        }
        else {
            val = carray_to_u32(&read_status[index], bytelen);
        }
        val /= divisor;
    }

    mutex_unlock(&g_data->update_lock);

    if(str != NULL)
        return sprintf(buf, "%s\n", present? str : "");
    if(is_show_int)
        return sprintf(buf, "%d\n", present? val : 0);
    if(is_show_hex)
        return sprintf(buf, "0x%x\n", present? val : 0);
    return sprintf_float(buf, val, present);

exit:
    mutex_unlock(&g_data->update_lock);
    return error;
}

ssize_t temp_show(struct device *dev, struct device_attribute *da,
                            char *buf)
{
    struct platform_device *pdev = to_platform_device(dev);
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
    unsigned char p_id = pdev->id / NUM_TEMP_PER_DEV;
    unsigned char t_id = pdev->id % NUM_TEMP_PER_DEV;
    u32 value = 0;
    int present = 0;
    int error = 0;
    char str[12] = "";
    int index = 0;
    const int temp_index[] = {PSU_TEMP1_0, PSU_TEMP2_0, PSU_TEMP3_0};
    unsigned char * const read_status = g_data->ipmi_resp[p_id].status;
    bf_print("pdev_id=%d, attr_name(%s) attr_idx=%d\n", pdev->id, da->attr.name, attr->index); //SEAN TODO

    mutex_lock(&g_data->update_lock);

    g_data = update_psu_status(p_id);
    if (!g_data->valid[p_id]) {
        error = -EIO;
        goto exit;
    }

    present = !!(read_status[PSU_PRESENT]);

    switch (attr->index) {
    case TEMP_ALIAS_ATTR_ID:
        sprintf(str, "PSU%d TEMP%d", p_id + 1, t_id + 1);
        break;
    case TEMP_INPUT_ATTR_ID:
        index = temp_index[t_id];
        value = carray_to_u32(&read_status[index], 2);
        break;
    default:
        error = -EINVAL;
        goto exit;
    }

    mutex_unlock(&g_data->update_lock);

    if(strlen(str) != 0)
        return sprintf(buf, "%s\n", str);
    return sprintf_float(buf, value, present);

exit:
    mutex_unlock(&g_data->update_lock);
    return error;

}
