/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * kernel driver module for bf xcvr
 */

#include <linux/module.h>
#include <linux/slab.h>
#include <linux/platform_device.h>
#include "bf_switch_sysfs.h"
#include "bf_xcvr_driver.h"
#include "bf_xcvr_api.h"

#define DRVNAME "bf_xcvr"
#define DIRNAME "eth%d"
#define ROOT_DIRNAME "transceiver"

static struct bf_xcvr_drv_data *g_data = NULL;

//////////////////////////////////////////////
// --- root attrs ---
BF_DEV_ATTR_RW_2(power_on, _r, root, POWERON_ATTR_ID);
BF_DEV_ATTR_RW_2(present, _r, root, PRESENT_ATTR_ID);
BF_DEV_ATTR_RW(debug, root, DEBUG_ATTR_ID);
BF_DEV_ATTR_RW(loglevel, root, LOGLEVEL_ATTR_ID);
BF_DEV_ATTR_RO(num, root, NUM_ATTR_ID);

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

// // --- dev attrs ---
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

/////////////////////////////////////////////////////


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
        return -EINVAL;
    return 0;
}

static void bf_xcvr_remove_root_attr(void)
{
    remove_sysfs_dir_and_attr(g_data->root_kobj, &root_attr_group);
}

///////////////////////////////////////////////////////////////

static int bf_xcvr_probe(struct platform_device *pdev)
{
    dev_info(&pdev->dev, "bf_xcvr_probe, pdev id=%d\n", pdev->id);
    return bf_xcvr_create_symlink(pdev);
    return 0;
}

static int bf_xcvr_remove(struct platform_device *pdev)
{
    bf_xcvr_remove_symlink(pdev);
    return 0;
}

DECL_PLATFORM_DRIVER(bf_xcvr, DRVNAME);

////////////////////////////////////////////////////

static void blanked_device_release(struct device *dev){ }

static inline void init_pdev(struct platform_device *pdev, char *name, int id,
        const struct attribute_group **groups)
{
    pdev->name = name;
    pdev->id = id;
    pdev->dev.groups = groups;
    pdev->dev.release = blanked_device_release;
    dev_set_drvdata(&pdev->dev, g_data);
}

static int xcvr_init(void)
{
    int i, j, ret;

    ret = platform_driver_register(&bf_xcvr_driver);
    if (ret < 0)
        goto dri_reg_err;

    for (i = 0 ; i < NUM_DEV ; i++) {
        struct platform_device *pdev = &g_data->pdev[i];
        init_pdev(pdev, DRVNAME, i, dev_attr_groups);
        ret = platform_device_register(pdev);
        if (ret != 0)
            goto dev_reg_err;
    }
    return 0;

dev_reg_err:
    for(j=0 ; j<i ; j++)
        platform_device_unregister(&g_data->pdev[j]);
    platform_driver_unregister(&bf_xcvr_driver);
dri_reg_err:
    return ret;
}

static void xcvr_exit(void)
{
    int i;
    for (i = 0 ; i < NUM_DEV ; i++)
        platform_device_unregister(&g_data->pdev[i]);
    platform_driver_unregister(&bf_xcvr_driver);
}


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

    ret = xcvr_init();
    if (ret < 0)
        goto dev_init_err;


    return 0;

dev_init_err:
    bf_xcvr_remove_root_attr();
create_root_sysfs_err:
    kfree(g_data);
alloc_err:
    return ret;
}

static void __exit bf_xcvr_exit(void)
{
    xcvr_exit();
    bf_xcvr_remove_root_attr();
    kfree(g_data);
}


MODULE_AUTHOR("Edgecore");
MODULE_DESCRIPTION("BF XCVR Driver");
MODULE_LICENSE("GPL");

module_init(bf_xcvr_init);
module_exit(bf_xcvr_exit);
