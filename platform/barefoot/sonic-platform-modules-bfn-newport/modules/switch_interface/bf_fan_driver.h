/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * FAN driver related data structures and enum
 */

#ifndef __BF_FAN_DRIVER_H__
#define __BF_FAN_DRIVER_H__

#define NUM_FAN 6
#define MOTOR_PER_FAN 2
#define NUM_MOTOR (NUM_FAN * MOTOR_PER_FAN)

enum fan_sysfs_attributes
{
    MOTOR_SPEED_ATTR_ID,
    MOTOR_SPEED_TOL_ATTR_ID,
    MOTOR_SPEED_TARGET_ATTR_ID,
    MOTOR_RATIO_ATTR_ID,
    MOTOR_DIR_ATTR_ID,
    FAN_MODEL_ATTR_ID,
    FAN_SERIAL_ATTR_ID,
    FAN_VENDOR_ATTR_ID,
    FAN_PARTNUM_ATTR_ID,
    FAN_HWVER_ATTR_ID,
    FAN_NUMMOTOR_ATTR_ID,
    FAN_STATUS_ATTR_ID,
    FAN_LED_ATTR_ID,
    DEBUG_ATTR_ID,
    LOGLEVEL_ATTR_ID,
    NUMFAN_ATTR_ID,
    FAN_MAX_ATTR_ID
};

struct bf_fan_drv_data {
    struct kobject *fan_root_kobj;
    int loglevel;
	struct platform_device fan_pdev[NUM_FAN];
    struct platform_device motor_pdev[NUM_MOTOR];
	// struct mutex update_lock;
	// char valid; /* != 0 if registers are valid */
	// unsigned long last_updated;	/* In jiffies */
	// /* 4 bytes for each fan, the last 2 bytes is fan dir */
	// unsigned char ipmi_resp[NUM_OF_FAN * FAN_DATA_COUNT + 2];
	// unsigned char ipmi_resp_cpld;
	// struct ipmi_data ipmi;
	// unsigned char ipmi_tx_data[3];  /* 0: FAN id, 1: 0x02, 2: PWM */
};

#endif //__BF_FAN_DRIVER_H__
