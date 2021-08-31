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
#define IPMI_PSU_ALARM_CMD 0x17

extern struct bf_psu_drv_data *g_data;

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
    char *str = NULL;
    int divisor = 1;
    unsigned char * const read_status = g_data->ipmi_resp[p_id].status;
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
    default:
        error = -EINVAL;
        goto exit;
    }

    if(bytelen <= 0x4)
    {
        val = carray_to_u32(&read_status[index], bytelen);
        val /= divisor;
    }

    mutex_unlock(&g_data->update_lock);

    if(str != NULL)
        return sprintf(buf, "%s\n", present? str : "");
    if(is_show_int)
        return sprintf(buf, "%d\n", present? val : 0);
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
