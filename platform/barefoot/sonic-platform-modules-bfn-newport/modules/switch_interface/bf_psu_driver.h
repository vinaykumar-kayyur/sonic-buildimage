/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * psu driver related data structures and enum
 */

#ifndef __BF_PSU_DRIVER_H__
#define __BF_PSU_DRIVER_H__

#define NUM_DEV 2
#define NUM_TEMP_PER_DEV 3
#define NUM_TEMP (NUM_DEV * NUM_TEMP_PER_DEV)

enum psu_sysfs_attributes
{
    TEMP_ALIAS_ATTR_ID,
    TEMP_TYPE_ATTR_ID,
    TEMP_MAX_ATTR_ID,
    TEMP_MAX_HYST_ATTR_ID,
    TEMP_MIN_ATTR_ID,
    TEMP_INPUT_ATTR_ID,
    PSU_MODEL_ATTR_ID,
    PSU_SERIAL_ATTR_ID,
    PSU_DATE_ATTR_ID,
    PSU_VENDOR_ATTR_ID,
    PSU_HW_VER_ATTR_ID,
    PSU_ALARM_ATTR_ID,
    PSU_ALARM_TH_CURR_ATTR_ID,
    PSU_ALARM_TH_VOL_ATTR_ID,
    PSU_PART_NUM_ATTR_ID,
    PSU_POUT_MAX_ATTR_ID,
    PSU_IIN_ATTR_ID,
    PSU_VIN_ATTR_ID,
    PSU_PIN_ATTR_ID,
    PSU_IOUT_ATTR_ID,
    PSU_VOUT_ATTR_ID,
    PSU_POUT_ATTR_ID,
    PSU_STATUS_ATTR_ID,
    PSU_LED_STATUS_ATTR_ID,
    PSU_TYPE_ATTR_ID,
    PSU_NUM_TEMP_ATTR_ID,
    PSU_FAN_SPEED_ATTR_ID,
    DEBUG_ATTR_ID,
    LOGLEVEL_ATTR_ID,
    NUM_ATTR_ID,
    PSU_MAX_ATTR_ID
};

struct bf_psu_drv_data {
    struct kobject *root_kobj;
    int loglevel;
    struct platform_device psu_pdev[NUM_DEV];
    struct platform_device temp_pdev[NUM_TEMP];
    // struct mutex update_lock;
    // char valid; /* != 0 if registers are valid */
    // unsigned long last_updated;    /* In jiffies */
    // /* 4 bytes for each fan, the last 2 bytes is fan dir */
    // unsigned char ipmi_resp[NUM_OF_FAN * FAN_DATA_COUNT + 2];
    // unsigned char ipmi_resp_cpld;
    // struct ipmi_data ipmi;
    // unsigned char ipmi_tx_data[3];  /* 0: FAN id, 1: 0x02, 2: PWM */
};

#endif //__BF_PSU_DRIVER_H__
