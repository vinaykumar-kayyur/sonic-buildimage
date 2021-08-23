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
extern int userlevel_to_kernlevel(int level);
extern int kernlevel_to_userlevel(int level);

/*
 * Macro to print kernel message
 * Use g_data->loglevel to prefix the loglevel.
 */
#define bf_print(fmt, ...)                       \
    if(g_data)                              \
        switch(g_data->loglevel){           \
            case 0: printk(KERN_WARNING pr_fmt(fmt), ##__VA_ARGS__); break; \
            case 1: printk(KERN_ERR pr_fmt(fmt), ##__VA_ARGS__); break;     \
            case 2: printk(KERN_INFO pr_fmt(fmt), ##__VA_ARGS__); break;    \
            case 3: printk(KERN_DEBUG pr_fmt(fmt), ##__VA_ARGS__); break;   \
        }

/* Name-Mangled version of SENSOR_ATTR */
#define SENSOR_DEVICE_ATTR_M(_name, _mangle, _mode, _show, _store, _index)  \
struct sensor_device_attribute sensor_dev_attr_##_name##_mangle             \
    = SENSOR_ATTR(_name, _mode, _show, _store, _index)

/* Name-Mangled version of BF_DEV_ATTR */
#define BF_DEV_ATTR_RO_2(_name, _mangle, _func, _index)             \
    static SENSOR_DEVICE_ATTR_M(_name, _mangle, 0444, _func##_show, \
            NULL, _index)

#define BF_DEV_ATTR_RW_2(_name, _mangle, _func, _index)             \
    static SENSOR_DEVICE_ATTR_M(_name, _mangle, 0644, _func##_show, \
            _func##_store, _index)

/* Ordinary BF_DEV_ATTR */
#define BF_DEV_ATTR_RO(_name, _func, _index)            \
    BF_DEV_ATTR_RO_2(_name, , _func, _index)

#define BF_DEV_ATTR_RW(_name, _func, _index)            \
    BF_DEV_ATTR_RW_2(_name, , _func, _index)

/* Declare platform driver one-liner */
#define DECL_PLATFORM_DRIVER(_func, _name)              \
    static struct platform_driver _func##_driver = {    \
        .probe = _func##_probe,                         \
        .remove = _func##_remove,                       \
        .driver = {                                     \
            .name = _name,                              \
            .owner = THIS_MODULE,                       \
        },                                              \
    }

/* loglevel show/store funcs must be implemented for all modules */
ssize_t loglevel_show(struct device *dev, struct device_attribute *da,
                            char *buf);
ssize_t loglevel_store(struct device *dev, struct device_attribute *da,
                            const char *buf, size_t count);

#define ATTR_SHOW_NUM_FUNC(_name, _val)                                          \
    ssize_t _name##_show(struct device *dev, struct device_attribute *da,   \
                                char *buf){                                 \
        return sprintf(buf, "%d\n", _val);                                  \
    }

/* loglevel show/store implementation */
#define LOGLEVEL_SHOW_STORE_FUNC(_gdata_loglevel)                              \
    ATTR_SHOW_NUM_FUNC(loglevel, kernlevel_to_userlevel(_gdata_loglevel))      \
    ssize_t loglevel_store(struct device *dev, struct device_attribute *da,    \
                                const char *buf, size_t count)                 \
    {                                                                          \
        long val = 0;                                                          \
        int status;                                                            \
        status = kstrtol(buf, 10, &val);                                       \
        if (status)                                                            \
            return status;                                                     \
        _gdata_loglevel = userlevel_to_kernlevel(val);                         \
        return count;                                                          \
    }

/* debug show funcs must be implemented for all modules */
ssize_t debug_show(struct device *dev, struct device_attribute *da,
                            char *buf);

/* debug show implementation */
#define DEBUG_SHOW_TXT(_debug_txt)                                      \
    ssize_t debug_show(struct device *dev, struct device_attribute *da, \
                                char *buf)                              \
    {                                                                   \
        char *str =                                                     \
            _debug_txt                                                  \
            ;                                                           \
        return sprintf(buf, "%s\n", str);                               \
    }

#endif //__BF_SWITCH_SYSFS_H__
