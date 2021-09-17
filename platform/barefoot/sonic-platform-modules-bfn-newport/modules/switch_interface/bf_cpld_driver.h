/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * cpld driver related data structures and enum
 */

#ifndef __BF_CPLD_DRIVER_H__
#define __BF_CPLD_DRIVER_H__

#define NUM_DEV 1
#define IPMI_CPLD_TYPE_LEN 28
#define I2C_CPLD_ADDRESS 0x31

enum cpld_sysfs_attributes
{
    CPLD_ALIAS_ATTR_ID,
    CPLD_TYPE_ATTR_ID,
    CPLD_HW_VER_ATTR_ID,
    CPLD_BD_VER_ATTR_ID,
    CPLD_RST_CPU_ATTR_ID,
    CPLD_RST_MAC_ATTR_ID,
    DEBUG_ATTR_ID,
    LOGLEVEL_ATTR_ID,
    NUM_ATTR_ID,
    REBOOT_CAUSE_ATTR_ID
};

enum reboot_cause_id_enum {
    REBOOT_CAUSE_NON_HARDWARE = 0,
    REBOOT_CAUSE_POWER_LOSS,
    REBOOT_CAUSE_THERMAL_OVERLOAD_CPU,
    REBOOT_CAUSE_THERMAL_OVERLOAD_ASIC,
    REBOOT_CAUSE_THERMAL_OVERLOAD_OTHER,
    REBOOT_CAUSE_INSUFFICIENT_FAN_SPEED,
    REBOOT_CAUSE_WATCHDOG,
    REBOOT_CAUSE_HARDWARE_OTHER,
    REBOOT_CAUSE_CPU_COLD_RESET,
    REBOOT_CAUSE_CPU_WARM_RESET,
    REBOOT_CAUSE_BIOS_RESET,
    REBOOT_CAUSE_PSU_SHUTDOWN,
    REBOOT_CAUSE_BMC_SHUTDOWN,
    REBOOT_CAUSE_RESET_BUTTON_SHUTDOWN,
    REBOOT_CAUSE_RESET_BUTTON_COLD_SHUTDOWN,
    REBOOT_CAUSE_INVALID = -1
};

struct ipmi_cpld_resp_data {
    unsigned char hw_version[2];
    unsigned char bd_version[1];
    unsigned char reboot_cause[1];
    unsigned char reset_status[2];
    char type[IPMI_CPLD_TYPE_LEN+1];
};

struct bf_cpld_drv_data {
    struct kobject *root_kobj;
    int loglevel;
    struct platform_device cpld_pdev[NUM_DEV];
    struct mutex update_lock;
    char valid[NUM_DEV]; /* != 0 if registers are valid */
    unsigned long last_updated[NUM_DEV];    /* In jiffies */
    struct ipmi_data ipmi;
    struct ipmi_cpld_resp_data ipmi_resp[NUM_DEV];
    unsigned char ipmi_tx_data[1];
    unsigned char ipmi_tx_reset_data[2];
    int reboot_cause_id[NUM_DEV];
};

#endif //__BF_CPLD_DRIVER_H__
