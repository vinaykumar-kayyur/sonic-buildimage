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
    "Sensors Info:\n"
    "    num of thermal sensors = 8\n"
    "    num of voltage sensors = 0\n"
    "    num of current sensors = 0\n"
    "\n"
    "Dump all thermal sensors' status:\n"
    "    $ ipmitool raw 0x34 0x12\n"
    "    Output format:\n"
    "        OFFSET SIZE FIELD           DESCRIPTION\n"
    "        ------------------------------------------------------------------\n"
    "        0      1    temp0_i2c_addr  I2C address of the sensor\n"
    "        1      1    temp0_status    0:Fail to read, 1:Normal\n"
    "        2      2    temp0_input     Current thermal reading in milliDegree\n"
    "        4      1    temp1_i2c_addr  I2C address of the sensor\n"
    "        5      1    temp1_status    0:Fail to read, 1:Normal\n"
    "        6      2    temp1_input     Current thermal reading in milliDegree\n"
    "        8      1    temp2_i2c_addr  I2C address of the sensor\n"
    "        9      1    temp2_status    0:Fail to read, 1:Normal\n"
    "        10     2    temp2_input     Current thermal reading in milliDegree\n"
    "        12     1    temp3_i2c_addr  I2C address of the sensor\n"
    "        13     1    temp3_status    0:Fail to read, 1:Normal\n"
    "        14     2    temp3_input     Current thermal reading in milliDegree\n"
    "        16     1    temp4_i2c_addr  I2C address of the sensor\n"
    "        17     1    temp4_status    0:Fail to read, 1:Normal\n"
    "        18     2    temp4_input     Current thermal reading in milliDegree\n"
    "        20     1    temp5_i2c_addr  I2C address of the sensor\n"
    "        21     1    temp5_status    0:Fail to read, 1:Normal\n"
    "        22     2    temp5_input     Current thermal reading in milliDegree\n"
    "        24     1    temp6_i2c_addr  I2C address of the sensor\n"
    "        25     1    temp6_status    0:Fail to read, 1:Normal\n"
    "        26     2    temp6_input     Current thermal reading in milliDegree\n"
    "        28     1    temp7_i2c_addr  I2C address of the sensor\n"
    "        29     1    temp7_status    0:Fail to read, 1:Normal\n"
    "        30     2    temp7_input     Current thermal reading in milliDegree\n"
    "\n"
    "Dump thermal sensor type:\n"
    "    $ ipmitool raw 0x34 0x12 0x1 <SENSOR_ADDR> [<CPU_SENSOR_ID>]\n"
    "        where SENSOR_ADDR=0x48~0x4d, or 0x33(CPU). CPU_SENSOR_ID=1~2\n"
    "\n"
    "Dump thermal sensor temp_max :\n"
    "    $ ipmitool raw 0x34 0x12 0x2 <SENSOR_ADDR> [<CPU_SENSOR_ID>]\n"
    "        where SENSOR_ADDR=0x48~0x4d, or 0x33(CPU). CPU_SENSOR_ID=1~2\n"
    "        Output: In degree. 1 byte only.\n"
    "\n"
    "Dump thermal sensor temp_max_hyst :\n"
    "    $ ipmitool raw 0x34 0x12 0x3 <SENSOR_ADDR> [<CPU_SENSOR_ID>]\n"
    "        where SENSOR_ADDR=0x48~0x4d, or 0x33(CPU). CPU_SENSOR_ID=1~2\n"
    "        Output: In degree. 1 byte only.\n"
    "\n"
    "Dump thermal sensor temp_min :\n"
    "    $ ipmitool raw 0x34 0x12 0x4 <SENSOR_ADDR> [<CPU_SENSOR_ID>]\n"
    "        where SENSOR_ADDR=0x48~0x4d, or 0x33(CPU). CPU_SENSOR_ID=1~2\n"
    "        Output: In degree. 1 byte only.\n"
    "\n"
    "Dump thermal sensor alias :\n"
    "    $ ipmitool raw 0x34 0x12 0x5 <SENSOR_ADDR> [<CPU_SENSOR_ID>]\n"
    "        where SENSOR_ADDR=0x48~0x4d, or 0x33(CPU). CPU_SENSOR_ID=1~2\n"
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
