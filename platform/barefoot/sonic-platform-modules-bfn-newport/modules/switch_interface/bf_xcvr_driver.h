/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * xcvr driver related data structures and enum
 */

#ifndef __BF_XCVR_DRIVER_H__
#define __BF_XCVR_DRIVER_H__

#define NUM_DEV 32

enum xcvr_sysfs_attributes
{
    ETH_POWERON_ATTR_ID,
    ETH_RESET_ATTR_ID,
    ETH_LPMODE_ATTR_ID,
    ETH_PRESENT_ATTR_ID,
    ETH_INTR_ATTR_ID,
    ETH_EEPROM_ATTR_ID,
    POWERON_ATTR_ID,
    PRESENT_ATTR_ID,
    DEBUG_ATTR_ID,
    LOGLEVEL_ATTR_ID,
    NUM_ATTR_ID,
    XCVR_MAX_ATTR_ID
};

struct bf_xcvr_drv_data {
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

#endif //__BF_XCVR_DRIVER_H__
