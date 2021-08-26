/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * kernel driver module for bf eeprom
 */

#define pr_fmt(fmt) "%s:%s: " fmt, KBUILD_MODNAME,  __func__

#include <linux/module.h>
#include <linux/slab.h>
#include <linux/platform_device.h>
#include "bf_switch_sysfs.h"
#include "bf_module_util.h"
#include "bf_eeprom_driver.h"
#include "bf_eeprom_api.h"

#define DRVNAME "bf_syseeprom"
#define ROOT_DIRNAME "syseeprom"

struct bf_eeprom_drv_data *g_data = NULL;
int *module_loglevel = NULL;

/* Root Attributes */
BF_DEV_ATTR_RO(eeprom, eeprom, DEBUG_ATTR_ID);
BF_DEV_ATTR_RO(bsp_version, eeprom, DEBUG_ATTR_ID);
BF_DEV_ATTR_RO(debug, debug, DEBUG_ATTR_ID);
BF_DEV_ATTR_RW(loglevel, loglevel, LOGLEVEL_ATTR_ID);

static struct attribute *root_attrs[] = {
    &sensor_dev_attr_debug.dev_attr.attr,
    &sensor_dev_attr_loglevel.dev_attr.attr,
    &sensor_dev_attr_eeprom.dev_attr.attr,
    &sensor_dev_attr_bsp_version.dev_attr.attr,
    NULL
};

static struct attribute_group root_attr_group = {
    .attrs = root_attrs,
};


static int bf_eeprom_create_root_attr(void)
{
    g_data->root_kobj = create_sysfs_dir_and_attr(ROOT_DIRNAME,
            bf_get_switch_kobj(), &root_attr_group);
    if(g_data->root_kobj == NULL)
        return -EIO;
    return 0;
}

static void bf_eeprom_remove_root_attr(void)
{
    remove_sysfs_dir_and_attr(g_data->root_kobj, &root_attr_group);
}


static int __init bf_eeprom_init(void)
{
    int ret;

    g_data = kzalloc(sizeof(struct bf_eeprom_drv_data), GFP_KERNEL);
    if (!g_data) {
        ret = -ENOMEM;
        goto alloc_err;
    }
    module_loglevel = &g_data->loglevel;

    ret = bf_eeprom_create_root_attr();
    if (ret < 0)
        goto create_root_sysfs_err;

    return 0;

create_root_sysfs_err:
    module_loglevel = NULL;
    kfree(g_data);
alloc_err:
    return ret;
}

static void __exit bf_eeprom_exit(void)
{
    bf_eeprom_remove_root_attr();
    module_loglevel = NULL;
    kfree(g_data);
}


MODULE_AUTHOR("Edgecore");
MODULE_DESCRIPTION("BF SYSEEPROM Driver");
MODULE_LICENSE("GPL");

module_init(bf_eeprom_init);
module_exit(bf_eeprom_exit);
