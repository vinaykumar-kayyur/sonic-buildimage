/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * eeprom driver related data structures and enum
 */

#ifndef __BF_EEPROM_DRIVER_H__
#define __BF_EEPROM_DRIVER_H__


enum eeprom_sysfs_attributes
{
    EEPROM_ATTR_ID,
    BSP_VER_ATTR_ID,
    DEBUG_ATTR_ID,
    LOGLEVEL_ATTR_ID,
    EEPROM_MAX_ATTR_ID
};

struct bf_eeprom_drv_data {
    struct kobject *root_kobj;
    int loglevel;
    // struct mutex update_lock;
    // char valid; /* != 0 if registers are valid */
    // unsigned long last_updated;    /* In jiffies */
    // /* 4 bytes for each fan, the last 2 bytes is fan dir */
    // unsigned char ipmi_resp[NUM_OF_FAN * FAN_DATA_COUNT + 2];
    // unsigned char ipmi_resp_cpld;
    // struct ipmi_data ipmi;
    // unsigned char ipmi_tx_data[3];  /* 0: FAN id, 1: 0x02, 2: PWM */
};

#endif //__BF_EEPROM_DRIVER_H__
