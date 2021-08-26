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
#include <linux/platform_device.h>

struct kobject * bf_get_switch_kobj(void);
struct kobject * create_sysfs_dir_and_attr(char *dir_name,
        struct kobject *parent, struct attribute_group *attrs);
void remove_sysfs_dir_and_attr(struct kobject *kobj,
        struct attribute_group *attr);

#endif //__BF_SWITCH_SYSFS_H__
