/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * device attribute handler implementation for bf sensor driver
 */

#define pr_fmt(fmt) "%s:%s: " fmt, KBUILD_MODNAME,  __func__

#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/hwmon-sysfs.h>
#include "bf_module_util.h"
#include "bf_sensor_driver.h"

#define IPMI_SENSOR_READ_CMD 0x12
#define IPMI_SENSOR_TYPE_CMD 0x01
#define IPMI_SENSOR_TEMP_MAX_CMD 0x02
#define IPMI_SENSOR_TEMP_MAX_HYST_CMD 0x03
#define IPMI_SENSOR_TEMP_MIN_CMD 0x04
#define IPMI_SENSOR_TEMP_ALIAS_CMD 0x05

extern struct bf_sensor_drv_data *g_data;


ATTR_SHOW_STR_FUNC(debug,
    "+++DUMMY content+++\n"
    "sensor present:\n"
    "  0-->present\n"
    "  1-->unpresent\n"
    "  bit0-->sensor1, bit4-->sensor2\n"
    "  eg:\n"
    "  1.show present info: i2cget -f -y 2 0x1d 0x34\n"
    "\n"
    "sensor data:\n"
    "                    path\n"
    "  sensor1             81-0058\n"
    "  sensor2             82-0058\n"
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
    "sensor vendor, model, serial, version:\n"
    "  sensor1-->$bus = 81, $addr = 0x50\n"
    "  sensor2-->$bus = 82, $addr = 0x50\n"
    "  eg:\n"
    "  1.show all info: i2cdump -f -y $bus $addr\n"
    "---DUMMY content---\n"
)

ATTR_SHOW_NUM_FUNC(devnum, NUM_TEMP_SENSORS)
ATTR_SHOW_NUM_FUNC(num_in, NUM_IN_SENSORS)
ATTR_SHOW_NUM_FUNC(num_curr, NUM_CURR_SENSORS)

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

static inline int get_sensor_addr(unsigned char p_id)
{
    int thermal_i2c_reg[NUM_TEMP_SENSORS] = {0x48, 0x49, 0x4a, 0x4b, 0x4c, 0x4d,
                                             0x33, 0x33};
    return thermal_i2c_reg[p_id];
}

static struct bf_sensor_drv_data *update_sensor_status(unsigned char p_id)
{
    int status = 0;
    unsigned short tx_cmd_num = 2;

    if(time_before(jiffies, g_data->last_updated[p_id] + HZ * 5) &&
            g_data->valid[p_id])
        return g_data;

    g_data->valid[p_id] = 0;

    /* Get status from ipmi */
    status = ipmi_send_message(&g_data->ipmi, IPMI_SENSOR_READ_CMD, NULL, 0,
                            g_data->ipmi_resp, sizeof(g_data->ipmi_resp));
    if (unlikely(status != 0))
        goto exit;

    if (unlikely(g_data->ipmi.rx_result != 0)) {
        status = -EIO;
        goto exit;
    }

    /*Common*/
    g_data->ipmi_tx_data[1] = get_sensor_addr(p_id);
    if(p_id >= SENSOR_ONBOARD_NUM) {
        tx_cmd_num =3;
        g_data->ipmi_tx_data[2] = p_id - 5;
    }

    /* Get type from ipmi */
    g_data->ipmi_tx_data[0] = IPMI_SENSOR_TYPE_CMD;
    status = ipmi_send_message(&g_data->ipmi, IPMI_SENSOR_READ_CMD,
                                g_data->ipmi_tx_data, tx_cmd_num,
                                g_data->ipmi_resp_data[p_id].type,
                                sizeof(g_data->ipmi_resp_data[p_id].type) - 1);
    if (unlikely(status != 0))
        goto exit;

    if (unlikely(g_data->ipmi.rx_result != 0)) {
        status = -EIO;
        goto exit;
    }

    /* Get alias from ipmi */
    g_data->ipmi_tx_data[0] = IPMI_SENSOR_TEMP_ALIAS_CMD;
    status = ipmi_send_message(&g_data->ipmi, IPMI_SENSOR_READ_CMD,
                                g_data->ipmi_tx_data, tx_cmd_num,
                                g_data->ipmi_resp_data[p_id].alias,
                                sizeof(g_data->ipmi_resp_data[p_id].alias) - 1);
    if (unlikely(status != 0))
        goto exit;

    if (unlikely(g_data->ipmi.rx_result != 0)) {
        status = -EIO;
        goto exit;
    }

    /* Get temp_max from ipmi */
    g_data->ipmi_tx_data[0] = IPMI_SENSOR_TEMP_MAX_CMD;
    status = ipmi_send_message(&g_data->ipmi, IPMI_SENSOR_READ_CMD,
                                g_data->ipmi_tx_data, tx_cmd_num,
                                &g_data->ipmi_resp_data[p_id].temp_max,
                                sizeof(g_data->ipmi_resp_data[p_id].temp_max));
    if (unlikely(status != 0))
        goto exit;

    if (unlikely(g_data->ipmi.rx_result != 0)) {
        status = -EIO;
        goto exit;
    }

    /* Get temp_max_hyst from ipmi */
    g_data->ipmi_tx_data[0] = IPMI_SENSOR_TEMP_MAX_HYST_CMD;
    status = ipmi_send_message(&g_data->ipmi, IPMI_SENSOR_READ_CMD,
                                g_data->ipmi_tx_data, tx_cmd_num,
                                &g_data->ipmi_resp_data[p_id].temp_max_hyst,
                                sizeof(g_data->ipmi_resp_data[p_id].temp_max_hyst));
    if (unlikely(status != 0))
        goto exit;

    if (unlikely(g_data->ipmi.rx_result != 0)) {
        status = -EIO;
        goto exit;
    }

    /* Get temp_min from ipmi */
    g_data->ipmi_tx_data[0] = IPMI_SENSOR_TEMP_MIN_CMD;
    status = ipmi_send_message(&g_data->ipmi, IPMI_SENSOR_READ_CMD,
                                g_data->ipmi_tx_data, tx_cmd_num,
                                &g_data->ipmi_resp_data[p_id].temp_min,
                                sizeof(g_data->ipmi_resp_data[p_id].temp_min));
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

ssize_t temp_show(struct device *dev, struct device_attribute *da,
                            char *buf)
{
    struct platform_device *pdev = to_platform_device(dev);
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
    u32 val = 0;
    unsigned char p_id = pdev->id;
    size_t bytelen = 0xFF;
    size_t index = 0;
    int error = 0;
    int divisor = 1;
    bool is_show_int = false;
    char *str = NULL;
    unsigned char * const read_status = g_data->ipmi_resp;
    bf_print("pdev_id=%d, attr_name(%s) attr_idx=%d\n", pdev->id, da->attr.name, attr->index);

    mutex_lock(&g_data->update_lock);

    g_data = update_sensor_status(p_id);
    if (!g_data->valid[p_id]) {
        error = -EIO;
        goto exit;
    }

    switch(attr->index) {
    case TEMP_INPUT_ATTR_ID:
        index = (EACH_DEV_STATUS_BYTE * p_id) + 2;
        bytelen = 2;
        bf_print("pdev_id=%d, low=%x high=%x\n", pdev->id, read_status[index], read_status[index+1]);
        break;
    case TEMP_TYPE_ATTR_ID:
        str = g_data->ipmi_resp_data[p_id].type;
        break;
    case TEMP_ALIAS_ATTR_ID:
        str = g_data->ipmi_resp_data[p_id].alias;
        break;
    case TEMP_MAX_ATTR_ID:
        is_show_int = true;
        val = g_data->ipmi_resp_data[p_id].temp_max;
        break;
    case TEMP_MAX_HYST_ATTR_ID:
        is_show_int = true;
        val = g_data->ipmi_resp_data[p_id].temp_max_hyst;
        break;
    case TEMP_MIN_ATTR_ID:
        is_show_int = true;
        val = g_data->ipmi_resp_data[p_id].temp_min;
        break;
    default:
        error = -EINVAL;
        goto exit;
    }
    if(bytelen <= 0x2)
    {
        val = carray_to_u32(&read_status[index], bytelen);
        val /= divisor;
    }

    mutex_unlock(&g_data->update_lock);
    if(str != NULL)
        return sprintf(buf, "%s\n", str);
    if(is_show_int)
        return sprintf(buf, "%d\n", val*1000);
    return sprintf(buf, "%d\n", val);

exit:
    mutex_unlock(&g_data->update_lock);
    return error;
}
ssize_t temp_store(struct device *dev, struct device_attribute *da,
                            const char *buf, size_t count)
{
    struct platform_device *pdev = to_platform_device(dev);
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
    bf_print("pdev_id=%d, attr_name(%s) attr_idx=%d\n", pdev->id, da->attr.name, attr->index);
    return count;
}
