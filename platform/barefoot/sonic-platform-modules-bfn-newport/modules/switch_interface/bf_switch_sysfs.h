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


/*
 * Name-Mangled version of SENSOR_ATTR
 */
#define SENSOR_DEVICE_ATTR_M(_name, _mangle, _mode, _show, _store, _index)  \
struct sensor_device_attribute sensor_dev_attr_##_name##_mangle             \
    = SENSOR_ATTR(_name, _mode, _show, _store, _index)

#define BF_DEV_ATTR_RO_2(_name, _mangle, _func, _index)             \
    static SENSOR_DEVICE_ATTR_M(_name, _mangle, 0444, _func##_show, \
            NULL, _index)

#define BF_DEV_ATTR_RW_2(_name, _mangle, _func, _index)             \
    static SENSOR_DEVICE_ATTR_M(_name, _mangle, 0644, _func##_show, \
            _func##_store, _index)

#define BF_DEV_ATTR_RO(_name, _func, _index)            \
    BF_DEV_ATTR_RO_2(_name, , _func, _index)

#define BF_DEV_ATTR_RW(_name, _func, _index)            \
    BF_DEV_ATTR_RW_2(_name, , _func, _index)


#define DECL_PLATFORM_DRIVER(_func, _name)              \
    static struct platform_driver _func##_driver = {    \
        .probe = _func##_probe,                         \
        .remove = _func##_remove,                       \
        .driver = {                                     \
            .name = _name,                              \
            .owner = THIS_MODULE,                       \
        },                                              \
    }

#endif //__BF_SWITCH_SYSFS_H__
