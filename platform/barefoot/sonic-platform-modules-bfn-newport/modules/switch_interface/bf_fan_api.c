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
#define IPMI_FAN_WRITE_CMD 0x15
#define IPMI_FAN_READ_CPLD_VER_CMD 0x1
#define IPMI_FAN_READ_LED_STAT_CMD 0x2
#define IPMI_FAN_READ_SPEED_TARGET 0x3
#define IPMI_FAN_READ_SPEED_TOLERANCE 0x4
#define B2F (1)
#define F2B (0)

ATTR_SHOW_STR_FUNC(debug,
    "Fan Info:\n"
    "    num of fans = 6\n"
    "    num of motors per fan = 2\n"
    "\n"
    "Get all fans' status:\n"
    "    $ ipmitool raw 0x34 0x14\n"
    "    Output format:\n"
    "        "
    "        OFFSET SIZE FIELD         DESCRIPTION\n"
    "        ------------------------------------------------------------\n"
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

static struct bf_fan_drv_data *update_fan_status(void)
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

    g_data->ipmi_tx_data[0] = IPMI_FAN_READ_LED_STAT_CMD;
    status = ipmi_send_message(&g_data->ipmi, IPMI_FAN_READ_CMD,
                                g_data->ipmi_tx_data, 1,
                                g_data->ipmi_resp_led_stat,
                                sizeof(g_data->ipmi_resp_led_stat));
    if (unlikely(status != 0))
        goto exit;

    if (unlikely(g_data->ipmi.rx_result != 0)) {
        status = -EIO;
        goto exit;
    }

    g_data->ipmi_tx_data[0] = IPMI_FAN_READ_SPEED_TARGET;
    status = ipmi_send_message(&g_data->ipmi, IPMI_FAN_READ_CMD,
                                g_data->ipmi_tx_data, 1,
                                g_data->ipmi_resp_speed_target,
                                sizeof(g_data->ipmi_resp_speed_target));
    if (unlikely(status != 0))
        goto exit;

    if (unlikely(g_data->ipmi.rx_result != 0)) {
        status = -EIO;
        goto exit;
    }

    g_data->ipmi_tx_data[0] = IPMI_FAN_READ_SPEED_TOLERANCE;
    status = ipmi_send_message(&g_data->ipmi, IPMI_FAN_READ_CMD,
                                g_data->ipmi_tx_data, 1,
                                g_data->ipmi_resp_speed_tolerance,
                                sizeof(g_data->ipmi_resp_speed_tolerance));
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

static inline int get_color_by_state(unsigned char val)
{
    switch(val){
    case 0: return COLOR_RED;
    case 1: return COLOR_BLUE;
    default: return COLOR_FAILED;
    }
}

ssize_t fan_show(struct device *dev, struct device_attribute *da,
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

    g_data = update_fan_status();
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
        value = get_color_by_state(g_data->ipmi_resp_led_stat[f_id]);
        break;
    case FAN_STATUS_ATTR_ID:
        value = present;
        break;
    default:
        error = -EINVAL;
        goto exit;
    }

    mutex_unlock(&g_data->update_lock);
    if(attr->index == FAN_HWVER_ATTR_ID) {
        return sprintf(buf, "0x%x\n", value);
    } else {
        return sprintf(buf, "%d\n", value);
    }

exit:
    mutex_unlock(&g_data->update_lock);
    return error;
}

ssize_t motor_show(struct device *dev, struct device_attribute *da,
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

    g_data = update_fan_status();
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
    case MOTOR_SPEED_TARGET_ATTR_ID:
        value = (int)g_data->ipmi_resp_speed_target[MOTOR_PER_FAN * m_id] |
                (int)g_data->ipmi_resp_speed_target[(MOTOR_PER_FAN * m_id) + 1] << 8;
        break;
    case MOTOR_SPEED_TOL_ATTR_ID:
        value = (int)g_data->ipmi_resp_speed_tolerance[MOTOR_PER_FAN * m_id] |
                (int)g_data->ipmi_resp_speed_tolerance[(MOTOR_PER_FAN * m_id) + 1] << 8;
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

ssize_t motor_store(struct device *dev, struct device_attribute *da,
                            const char *buf, size_t count)
{
    struct platform_device *pdev = to_platform_device(dev);
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
    long pwm;
    int status;
    int f_id = pdev->id / MOTOR_PER_FAN;

    bf_print("dev_id=%d, attr_name(%s) attr_idx=%d\n", pdev->id, da->attr.name, attr->index); //SEAN TODO

    /* This function now only handle MOTOR_RATIO_ATTR_ID */
    if(attr->index != MOTOR_RATIO_ATTR_ID)
        return -EINVAL;

    status = kstrtol(buf, 10, &pwm);
    if (status)
        return status;

    pwm = (pwm * 100) / 625 - 1; /* Convert pwm to register value */

    mutex_lock(&g_data->update_lock);

    /* Send IPMI write command */
    g_data->ipmi_tx_data[0] = f_id + 1;
    g_data->ipmi_tx_data[1] = 0x02;
    g_data->ipmi_tx_data[2] = pwm;
    status = ipmi_send_message(&g_data->ipmi, IPMI_FAN_WRITE_CMD,
                                g_data->ipmi_tx_data, sizeof(g_data->ipmi_tx_data),
                                NULL, 0);
    if (unlikely(status != 0))
        goto exit;

    if (unlikely(g_data->ipmi.rx_result != 0)) {
        status = -EIO;
        goto exit;
    }

    /* Update pwm to ipmi_resp buffer to prevent from the impact of lazy update */
    g_data->ipmi_resp[f_id * FAN_DATA_COUNT + FAN_PWM] = pwm;
    status = count;

exit:
    mutex_unlock(&g_data->update_lock);
    return status;
}
