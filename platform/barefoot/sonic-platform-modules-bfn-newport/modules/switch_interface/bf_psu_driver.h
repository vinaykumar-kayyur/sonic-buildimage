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
#define IPMI_MODEL_SERIAL_LEN 21
#define IPMI_PSU_DATE_LEN 4
#define IPMI_PSU_VOLT_AM_DATA_LEN 3

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

enum ipmi_psu_resp_index {
    PSU_PRESENT = 0,
    PSU_TEMP_FAULT,
    PSU_POWER_GOOD_CPLD,
    PSU_POWER_GOOD_PMBUS,
    PSU_OVER_VOLTAGE,
    PSU_OVER_CURRENT,
    PSU_POWER_ON,
    PSU_VIN0,
    PSU_VIN1,
    PSU_VIN2,
    PSU_VOUT0,
    PSU_VOUT1,
    PSU_VOUT2,
    PSU_IIN0,
    PSU_IIN1,
    PSU_IIN2,
    PSU_IOUT0,
    PSU_IOUT1,
    PSU_IOUT2,
    PSU_PIN0,
    PSU_PIN1,
    PSU_PIN2,
    PSU_PIN3,
    PSU_POUT0,
    PSU_POUT1,
    PSU_POUT2,
    PSU_POUT3,
    PSU_TEMP1_0,
    PSU_TEMP1_1,
    PSU_TEMP2_0,
    PSU_TEMP2_1,
    PSU_TEMP3_0,
    PSU_TEMP3_1,
    PSU_FAN0,
    PSU_FAN1,
    PSU_VOUT_MODE,
    PSU_FAN_FAULT,
    PSU_STATUS_COUNT,
    PSU_MODEL = 0,
    PSU_SERIAL = 0,
    PSU_VENDOR = 0
};

struct ipmi_psu_resp_data {
    unsigned char status[PSU_STATUS_COUNT];
    char serial[IPMI_MODEL_SERIAL_LEN+1];
    char model[IPMI_MODEL_SERIAL_LEN+1];
    char vendor[IPMI_MODEL_SERIAL_LEN+1];
    char part_num[IPMI_MODEL_SERIAL_LEN+1];
    char date[IPMI_PSU_DATE_LEN+1];
    unsigned char hw_ver;
    unsigned char alarm_threshold[IPMI_PSU_VOLT_AM_DATA_LEN*2];
};

struct bf_psu_drv_data {
    struct kobject *root_kobj;
    int loglevel;
    struct platform_device psu_pdev[NUM_DEV];
    struct platform_device temp_pdev[NUM_TEMP];
    struct mutex update_lock;
    char valid[NUM_DEV]; /* != 0 if registers are valid */
    unsigned long last_updated[NUM_DEV];    /* In jiffies */
    struct ipmi_data ipmi;
    struct ipmi_psu_resp_data ipmi_resp[NUM_DEV]; /* 0: PSU1, 1: PSU2 */
    unsigned char ipmi_tx_data[2];
};

#endif //__BF_PSU_DRIVER_H__
