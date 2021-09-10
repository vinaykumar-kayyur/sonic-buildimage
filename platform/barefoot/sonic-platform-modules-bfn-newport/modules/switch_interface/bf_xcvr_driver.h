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

struct optoe_data {
    int use_smbus;
    u32 byte_len;

    /*
     * Lock protects against activities from other Linux tasks,
     * but not from changes by other I2C masters.
     */
    struct mutex lock;
    struct bin_attribute bin;
    unsigned int write_max;
    unsigned int num_addresses;

    /* dev_class: ONE_ADDR (QSFP) or TWO_ADDR (SFP) */
    int dev_class;

    struct platform_device *pdev;
};

struct bf_xcvr_drv_data {
    struct kobject *root_kobj;
    int loglevel;
    struct platform_device pdev[NUM_DEV];
    struct optoe_data optoe[NUM_DEV];
    uint32_t power_on;
    uint32_t present;
    uint32_t reset;
    uint32_t lpmode;
    uint32_t interrupt;
    struct mutex update_lock;
    unsigned long last_updated;
    char valid; /* != 0 if registers are valid */
};

#endif //__BF_XCVR_DRIVER_H__
