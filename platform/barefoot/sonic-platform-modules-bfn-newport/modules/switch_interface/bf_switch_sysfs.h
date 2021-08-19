/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * switch sysfs export symbols
 */

#ifndef __BF_SWITCH_SYSFS_H__
#define __BF_SWITCH_SYSFS_H__

#include <linux/hwmon-sysfs.h>

extern struct kobject * bf_get_switch_kobj(void);
extern struct kobject * create_sysfs_dir_and_attr(char *dir_name,
        struct kobject *parent, struct attribute_group *attrs);
extern void remove_sysfs_dir_and_attr(struct kobject *kobj,
        struct attribute_group *attr);

enum bf_log_levels{
    LOG_ERR = 0X1,
    LOG_WARN = 0X2,
    LOG_INFO = 0X4,
    LOG_DEBUG = 0X8
};
#define BF_DEFAULT_LOGLEVEL LOG_WARN

#define BF_DEV_ATTR_RO(_name, _func, _index)		\
	static SENSOR_DEVICE_ATTR(_name, 0444, _func##_show, NULL, _index)

#define BF_DEV_ATTR_RW(_name, _func, _index)		\
	static SENSOR_DEVICE_ATTR(_name, 0644, _func##_show, _func##_store, _index)

#endif //__BF_SWITCH_SYSFS_H__
