/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * kernel driver module for bf xcvr
 */

#define pr_fmt(fmt) "%s:%s: " fmt, KBUILD_MODNAME,  __func__

#include <linux/module.h>
#include <linux/slab.h>
#include <linux/platform_device.h>
#include "bf_switch_sysfs.h"
#include "bf_module_util.h"
#include "bf_xcvr_driver.h"
#include "bf_xcvr_api.h"

#define DRVNAME "bf_xcvr"
#define DIRNAME "eth%d"
#define ROOT_DIRNAME "transceiver"

struct bf_xcvr_drv_data *g_data = NULL;

/* Root Attributes */
BF_DEV_ATTR_RW_2(power_on, _r, root, POWERON_ATTR_ID);
BF_DEV_ATTR_RW_2(present, _r, root, PRESENT_ATTR_ID);
BF_DEV_ATTR_RO(debug, debug, DEBUG_ATTR_ID);
BF_DEV_ATTR_RW(loglevel, loglevel, LOGLEVEL_ATTR_ID);
BF_DEV_ATTR_RO(num, devnum, NUM_ATTR_ID);

static struct attribute *root_attrs[] = {
    &sensor_dev_attr_power_on_r.dev_attr.attr,
    &sensor_dev_attr_present_r.dev_attr.attr,
    &sensor_dev_attr_debug.dev_attr.attr,
    &sensor_dev_attr_loglevel.dev_attr.attr,
    &sensor_dev_attr_num.dev_attr.attr,
    NULL
};

static struct attribute_group root_attr_group = {
    .attrs = root_attrs,
};

/* XCVR Attributes */
BF_DEV_ATTR_RW(power_on, xcvr, ETH_POWERON_ATTR_ID);
BF_DEV_ATTR_RW(reset, xcvr, ETH_RESET_ATTR_ID);
BF_DEV_ATTR_RW(lpmode, xcvr, ETH_LPMODE_ATTR_ID);
BF_DEV_ATTR_RO(present, xcvr, ETH_PRESENT_ATTR_ID);
BF_DEV_ATTR_RO(interrupt, xcvr, ETH_INTR_ATTR_ID);
BF_DEV_ATTR_RW(eeprom, xcvr, ETH_EEPROM_ATTR_ID);

static struct attribute *dev_attrs[] = {
    &sensor_dev_attr_power_on.dev_attr.attr,
    &sensor_dev_attr_reset.dev_attr.attr,
    &sensor_dev_attr_lpmode.dev_attr.attr,
    &sensor_dev_attr_present.dev_attr.attr,
    &sensor_dev_attr_interrupt.dev_attr.attr,
    &sensor_dev_attr_eeprom.dev_attr.attr,
    NULL
};

static struct attribute_group dev_attr_group = {
    .attrs = dev_attrs,
};
static const struct attribute_group *dev_attr_groups[] = {
    &dev_attr_group,
    NULL
};


static int bf_xcvr_create_symlink(struct platform_device *pdev)
{
    char name[6];
    sprintf(name, DIRNAME, pdev->id + 1);
    return sysfs_create_link(g_data->root_kobj, &pdev->dev.kobj, name);
}

static void bf_xcvr_remove_symlink(struct platform_device *pdev)
{
    char name[6];
    sprintf(name, DIRNAME, pdev->id + 1);
    return sysfs_remove_link(g_data->root_kobj, name);
}

static int bf_xcvr_create_root_attr(void)
{
    g_data->root_kobj = create_sysfs_dir_and_attr(ROOT_DIRNAME,
            bf_get_switch_kobj(), &root_attr_group);
    if(g_data->root_kobj == NULL)
        return -EIO;
    return 0;
}

static void bf_xcvr_remove_root_attr(void)
{
    remove_sysfs_dir_and_attr(g_data->root_kobj, &root_attr_group);
}


static int bf_xcvr_probe(struct platform_device *pdev)
{
    bf_print("found dev id=%d\n", pdev->id);
    return bf_xcvr_create_symlink(pdev);
}

static int bf_xcvr_remove(struct platform_device *pdev)
{
    bf_xcvr_remove_symlink(pdev);
    return 0;
}

DECL_PLATFORM_DRIVER(bf_xcvr, DRVNAME);


static int __init bf_xcvr_init(void)
{
    int ret;

    g_data = kzalloc(sizeof(struct bf_xcvr_drv_data), GFP_KERNEL);
    if (!g_data) {
        ret = -ENOMEM;
        goto alloc_err;
    }

    ret = bf_xcvr_create_root_attr();
    if (ret < 0)
        goto create_root_sysfs_err;

    ret = register_device_and_driver(&bf_xcvr_driver, DRVNAME,
            g_data->pdev, ARRAY_SIZE(g_data->pdev), dev_attr_groups);
    if (ret < 0)
        goto reg_dev_err;

    return 0;

reg_dev_err:
    bf_xcvr_remove_root_attr();
create_root_sysfs_err:
    kfree(g_data);
alloc_err:
    return ret;
}

static void __exit bf_xcvr_exit(void)
{
    unregister_device_and_driver(&bf_xcvr_driver, g_data->pdev,
                                 ARRAY_SIZE(g_data->pdev));
    bf_xcvr_remove_root_attr();
    kfree(g_data);
}


MODULE_AUTHOR("Edgecore");
MODULE_DESCRIPTION("BF XCVR Driver");
MODULE_LICENSE("GPL");

module_init(bf_xcvr_init);
module_exit(bf_xcvr_exit);
