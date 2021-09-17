/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * kernel driver module for bf cpld
 */

#define pr_fmt(fmt) "%s:%s: " fmt, KBUILD_MODNAME,  __func__

#include <linux/module.h>
#include <linux/slab.h>
#include <linux/platform_device.h>
#include "bf_switch_sysfs.h"
#include "bf_module_util.h"
#include "bf_cpld_driver.h"
#include "bf_cpld_api.h"

#define CPLD_DRVNAME "bf_cpld"
#define CPLD_DIRNAME "cpld%d"
#define ROOT_DIRNAME "cpld"

struct bf_cpld_drv_data *g_data = NULL;

/* Root Attributes */
BF_DEV_ATTR_RO(debug, debug, DEBUG_ATTR_ID);
BF_DEV_ATTR_RW(loglevel, loglevel, LOGLEVEL_ATTR_ID);
BF_DEV_ATTR_RO(num, devnum, NUM_ATTR_ID);
BF_DEV_ATTR_RO(reboot_cause, cpld, REBOOT_CAUSE_ATTR_ID);

static struct attribute *root_attrs[] = {
    &sensor_dev_attr_debug.dev_attr.attr,
    &sensor_dev_attr_loglevel.dev_attr.attr,
    &sensor_dev_attr_num.dev_attr.attr,
    &sensor_dev_attr_reboot_cause.dev_attr.attr,
    NULL
};

static struct attribute_group root_attr_group = {
    .attrs = root_attrs,
};

/* CPLD Attributes */
BF_DEV_ATTR_RO(alias, cpld, CPLD_ALIAS_ATTR_ID);
BF_DEV_ATTR_RO(hw_version, cpld, CPLD_HW_VER_ATTR_ID);
BF_DEV_ATTR_RO(board_version, cpld, CPLD_BD_VER_ATTR_ID);
BF_DEV_ATTR_RO(type, cpld, CPLD_TYPE_ATTR_ID);
BF_DEV_ATTR_RW(reset_cpu, reset, CPLD_RST_CPU_ATTR_ID);
BF_DEV_ATTR_RW(reset_mac, reset, CPLD_RST_MAC_ATTR_ID);

static struct attribute *dev_attrs[] = {
    &sensor_dev_attr_alias.dev_attr.attr,
    &sensor_dev_attr_hw_version.dev_attr.attr,
    &sensor_dev_attr_board_version.dev_attr.attr,
    &sensor_dev_attr_type.dev_attr.attr,
    &sensor_dev_attr_reset_cpu.dev_attr.attr,
    &sensor_dev_attr_reset_mac.dev_attr.attr,
    NULL
};

static struct attribute_group dev_attr_group = {
    .attrs = dev_attrs,
};
static const struct attribute_group *dev_attr_groups[] = {
    &dev_attr_group,
    NULL
};

static int bf_cpld_create_symlink(struct platform_device *pdev)
{
    char name[6];
    sprintf(name, CPLD_DIRNAME, pdev->id + 1);
    return sysfs_create_link(g_data->root_kobj, &pdev->dev.kobj, name);
}

static void bf_cpld_remove_symlink(struct platform_device *pdev)
{
    char name[6];
    sprintf(name, CPLD_DIRNAME, pdev->id + 1);
    return sysfs_remove_link(g_data->root_kobj, name);
}

static int bf_cpld_create_root_attr(void)
{
    g_data->root_kobj = create_sysfs_dir_and_attr(ROOT_DIRNAME,
            bf_get_switch_kobj(), &root_attr_group);
    if(g_data->root_kobj == NULL)
        return -EIO;
    return 0;
}

static void bf_cpld_remove_root_attr(void)
{
    remove_sysfs_dir_and_attr(g_data->root_kobj, &root_attr_group);
}

static int bf_cpld_probe(struct platform_device *pdev)
{
    bf_print("found dev id=%d\n", pdev->id);
    g_data->reboot_cause_id[pdev->id] = REBOOT_CAUSE_CPU_COLD_RESET;
    update_cpld_status(pdev->id);
    return bf_cpld_create_symlink(pdev);
}

static int bf_cpld_remove(struct platform_device *pdev)
{
    bf_cpld_remove_symlink(pdev);
    return 0;
}

DECL_PLATFORM_DRIVER(bf_cpld, CPLD_DRVNAME);

static int __init bf_cpld_init(void)
{
    int ret;

    g_data = kzalloc(sizeof(struct bf_cpld_drv_data), GFP_KERNEL);
    if (!g_data) {
        ret = -ENOMEM;
        goto alloc_err;
    }
    init_bf_print(KBUILD_MODNAME, &g_data->loglevel);
    mutex_init(&g_data->update_lock);

    ret = bf_cpld_create_root_attr();
    if (ret < 0)
        goto create_root_sysfs_err;

    /* Set up IPMI interface */
    ret = init_ipmi_data(&g_data->ipmi, 0);
    if (ret)
        goto ipmi_err;

    ret = register_device_and_driver(&bf_cpld_driver, CPLD_DRVNAME,
            g_data->cpld_pdev, ARRAY_SIZE(g_data->cpld_pdev), dev_attr_groups);
    if (ret < 0)
        goto reg_dev_err;

    return 0;

reg_dev_err:
    ipmi_destroy_user(g_data->ipmi.user);
ipmi_err:
    bf_cpld_remove_root_attr();
create_root_sysfs_err:
    deinit_bf_print();
    kfree(g_data);
alloc_err:
    return ret;
}

static void __exit bf_cpld_exit(void)
{
    unregister_device_and_driver(&bf_cpld_driver, g_data->cpld_pdev,
                                 ARRAY_SIZE(g_data->cpld_pdev));
    ipmi_destroy_user(g_data->ipmi.user);
    bf_cpld_remove_root_attr();
    deinit_bf_print();
    kfree(g_data);
}


MODULE_AUTHOR("Edgecore");
MODULE_DESCRIPTION("BF CPLD Driver");
MODULE_LICENSE("GPL");

module_init(bf_cpld_init);
module_exit(bf_cpld_exit);
