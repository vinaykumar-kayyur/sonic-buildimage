/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * watchdog driver related data structures and enum
 */

#ifndef __BF_WATCHDOG_DRIVER_H__
#define __BF_WATCHDOG_DRIVER_H__

enum wdt_sysfs_attributes
{
    IDENTIFY_ATTR_ID,
    STATE_ATTR_ID,
    TIMELEFT_ATTR_ID,
    TIMEOUT_ATTR_ID,
    RESET_ATTR_ID,
    ENABLE_ATTR_ID,
    DEBUG_ATTR_ID,
    LOGLEVEL_ATTR_ID,
    WDT_MAX_ATTR_ID
};

struct bf_wdt_drv_data {
    struct kobject *root_kobj;
    int loglevel;
    struct mutex update_lock;
    char valid; /* != 0 if registers are valid */
    unsigned long last_updated;    /* In jiffies */
    struct ipmi_data ipmi;
    uint8_t wdt_enable;
    uint8_t wdt_timeout;
    uint8_t wdt_timeleft;
    unsigned char ipmi_tx_data[2];
};

#endif //__BF_WATCHDOG_DRIVER_H__
