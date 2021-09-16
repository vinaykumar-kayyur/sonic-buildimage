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

#define NUM_TEMP_SENSORS 8
#define NUM_IN_SENSORS 0
#define NUM_CURR_SENSORS 0
#define EACH_DEV_STATUS_BYTE 4
#define SENSOR_ONCPU_NUM 2 /*0x33-1, 0x33-2*/
#define SENSOR_ONBOARD_NUM 6 /*0x48~0x4d*/
#define IPMI_CPU_SENSOR_TYPE1_LEN 8 /*COMe CPU*/
#define IPMI_CPU_SENSOR_TYPE2_LEN 9 /*COMe DIMM*/
#define IPMI_SENSOR_ALIAS_LEN 20

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
    NUM_IN_ATTR_ID,
    NUM_CURR_ATTR_ID,
    SENSOR_MAX_ATTR_ID
};

enum ipmi_sensor_resp_index {
    SENSOR_ADDR = 0,
    SENSOR_STATUS,
    SENSOR_TEMP_LOW_BYTE,
    SENSOR_TEMP_HIGH_BYTE,
    SENSOR_STATUS_COUNT
};

struct ipmi_sensor_resp_data {
    char type[IPMI_CPU_SENSOR_TYPE2_LEN+1];
    char alias[IPMI_SENSOR_ALIAS_LEN+1];
    unsigned char temp_max;
    unsigned char temp_max_hyst;
    unsigned char temp_min;
    unsigned char temp_input;
};

struct bf_sensor_drv_data {
    struct kobject *root_kobj;
    int loglevel;
    struct platform_device pdev[NUM_TEMP_SENSORS];
    struct mutex update_lock;
    char valid[NUM_TEMP_SENSORS]; /* != 0 if registers are valid */
    unsigned long last_updated[NUM_TEMP_SENSORS];    /* In jiffies */
    struct ipmi_data ipmi;
    unsigned char ipmi_resp[NUM_TEMP_SENSORS*EACH_DEV_STATUS_BYTE];
    struct ipmi_sensor_resp_data ipmi_resp_data[NUM_TEMP_SENSORS]; /*0:temp0~7:temp7*/
    unsigned char ipmi_tx_data[3];
};

#endif //__BF_SENSOR_DRIVER_H__
