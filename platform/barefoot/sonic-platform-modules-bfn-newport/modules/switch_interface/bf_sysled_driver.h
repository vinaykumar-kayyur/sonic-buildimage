/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * sysled driver related data structures and enum
 */

#ifndef __BF_SYSLED_DRIVER_H__
#define __BF_SYSLED_DRIVER_H__

#define SYSLED_STATUS_COUNT 2

enum psu_sysfs_attributes
{
    SYSLED_SYS_STATUS_ATTR_ID,
    SYSLED_LOC_STATUS_ATTR_ID,
    SYSLED_BMC_STATUS_ATTR_ID,
    SYSLED_FAN_STATUS_ATTR_ID,
    SYSLED_PSU_STATUS_ATTR_ID,
    DEBUG_ATTR_ID,
    LOGLEVEL_ATTR_ID
};

struct bf_sysled_drv_data {
    struct kobject *root_kobj;
    int loglevel;
    struct platform_device sysled_pdev;
    struct mutex update_lock;
    char valid; /* != 0 if registers are valid */
    unsigned long last_updated;    /* In jiffies */
    struct ipmi_data ipmi;
    unsigned char ipmi_resp[SYSLED_STATUS_COUNT];
    unsigned char ipmi_tx_data[2];
};

#endif //__BF_SYSLED_DRIVER_H__
