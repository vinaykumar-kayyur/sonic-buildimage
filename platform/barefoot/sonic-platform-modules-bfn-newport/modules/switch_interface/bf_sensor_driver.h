/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * sensor driver related data structures and enum
 */

#ifndef __BF_SENSOR_DRIVER_H__
#define __BF_SENSOR_DRIVER_H__

#define NUM_DEV 6

enum sensor_sysfs_attributes
{
    TEMP_ALIAS_ATTR_ID,
    TEMP_TYPE_ATTR_ID,
    TEMP_MAX_ATTR_ID,
    TEMP_MAX_HYST_ATTR_ID,
    TEMP_MIN_ATTR_ID,
    TEMP_INPUT_ATTR_ID,
    DEBUG_ATTR_ID,
    LOGLEVEL_ATTR_ID,
    NUM_TEMP_ATTR_ID,
    SENSOR_MAX_ATTR_ID
};

struct bf_sensor_drv_data {
    struct kobject *root_kobj;
    int loglevel;
    struct platform_device pdev[NUM_DEV];
    // struct mutex update_lock;
    // char valid; /* != 0 if registers are valid */
    // unsigned long last_updated;    /* In jiffies */
    // /* 4 bytes for each fan, the last 2 bytes is fan dir */
    // unsigned char ipmi_resp[NUM_OF_FAN * FAN_DATA_COUNT + 2];
    // unsigned char ipmi_resp_cpld;
    // struct ipmi_data ipmi;
    // unsigned char ipmi_tx_data[3];  /* 0: FAN id, 1: 0x02, 2: PWM */
};

#endif //__BF_SENSOR_DRIVER_H__
