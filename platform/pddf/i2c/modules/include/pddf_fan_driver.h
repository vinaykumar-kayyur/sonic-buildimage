/*
 * Copyright 2019 Broadcom. All rights reserved.
 * The term “Broadcom” refers to Broadcom Inc. and/or its subsidiaries.
 *
 * Description
 *  FAN driver related data structures
 */
#ifndef __PDDF_FAN_DRIVER_H__
#define __PDDF_FAN_DRIVER_H__

enum fan_sysfs_attributes {
    FAN1_PRESENT,
    FAN2_PRESENT,
    FAN3_PRESENT,
    FAN4_PRESENT,
    FAN5_PRESENT,
    FAN6_PRESENT,
    FAN1_DIRECTION,
    FAN2_DIRECTION,
    FAN3_DIRECTION,
    FAN4_DIRECTION,
    FAN5_DIRECTION,
    FAN6_DIRECTION,
    FAN1_FRONT_RPM,
    FAN2_FRONT_RPM,
    FAN3_FRONT_RPM,
    FAN4_FRONT_RPM,
    FAN5_FRONT_RPM,
    FAN6_FRONT_RPM,
    FAN1_REAR_RPM,
    FAN2_REAR_RPM,
    FAN3_REAR_RPM,
    FAN4_REAR_RPM,
    FAN5_REAR_RPM,
    FAN6_REAR_RPM,
    FAN1_PWM,
    FAN2_PWM,
    FAN3_PWM,
    FAN4_PWM,
    FAN5_PWM,
    FAN6_PWM,
    FAN1_FAULT,
    FAN2_FAULT,
    FAN3_FAULT,
    FAN4_FAULT,
    FAN5_FAULT,
    FAN6_FAULT,
    FAN_MAX_ATTR 
};
/* Each client has this additional data */
struct fan_attr_info {
    char                name[ATTR_NAME_LEN];
    struct mutex        update_lock;
    char                valid;           /* != 0 if registers are valid */
    unsigned long       last_updated;    /* In jiffies */
    union {
        char strval[STR_ATTR_SIZE];
        int  intval;
        u16  shortval;
        u8   charval;
    }val;
};

struct fan_data {
    struct device           *hwmon_dev;
    int                     num_attr;
    struct attribute        *fan_attribute_list[MAX_FAN_ATTRS];
    struct attribute_group  fan_attribute_group;
    struct fan_attr_info    attr_info[MAX_FAN_ATTRS];
};

#endif //__PDDF_FAN_DRIVER_H__
