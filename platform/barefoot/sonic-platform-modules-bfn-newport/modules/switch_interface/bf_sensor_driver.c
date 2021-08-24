/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * kernel driver module for bf sensor
 */

#define pr_fmt(fmt) "%s:%s: " fmt, KBUILD_MODNAME,  __func__

#include <linux/module.h>
#include <linux/slab.h>
#include <linux/platform_device.h>
#include "bf_switch_sysfs.h"
#include "bf_sensor_driver.h"
#include "bf_sensor_api.h"

#define DRVNAME "bf_sensor"
#define DIRNAME "temp%d"
#define ROOT_DIRNAME "sensor"

struct bf_sensor_drv_data *g_data = NULL;

/* Root Attributes */
BF_DEV_ATTR_RO(debug, debug, DEBUG_ATTR_ID);
BF_DEV_ATTR_RW(loglevel, loglevel, LOGLEVEL_ATTR_ID);
BF_DEV_ATTR_RO(num_temp_sensors, devnum, NUM_TEMP_ATTR_ID);

static struct attribute *root_attrs[] = {
    &sensor_dev_attr_debug.dev_attr.attr,
    &sensor_dev_attr_loglevel.dev_attr.attr,
    &sensor_dev_attr_num_temp_sensors.dev_attr.attr,
    NULL
};

static struct attribute_group root_attr_group = {
    .attrs = root_attrs,
};

/* Sensor Attributes */
BF_DEV_ATTR_RO(temp_alias, temp, TEMP_ALIAS_ATTR_ID);
BF_DEV_ATTR_RO(temp_type, temp, TEMP_TYPE_ATTR_ID);
BF_DEV_ATTR_RO(temp_max, temp, TEMP_MAX_ATTR_ID);
BF_DEV_ATTR_RO(temp_max_hyst, temp, TEMP_MAX_HYST_ATTR_ID);
BF_DEV_ATTR_RO(temp_min, temp, TEMP_MIN_ATTR_ID);
BF_DEV_ATTR_RO(temp_input, temp, TEMP_INPUT_ATTR_ID);

static struct attribute *dev_attrs[] = {
    &sensor_dev_attr_temp_alias.dev_attr.attr,
    &sensor_dev_attr_temp_type.dev_attr.attr,
    &sensor_dev_attr_temp_max.dev_attr.attr,
    &sensor_dev_attr_temp_max_hyst.dev_attr.attr,
    &sensor_dev_attr_temp_min.dev_attr.attr,
    &sensor_dev_attr_temp_input.dev_attr.attr,
    NULL
};

static struct attribute_group dev_attr_group = {
    .attrs = dev_attrs,
};
static const struct attribute_group *dev_attr_groups[] = {
    &dev_attr_group,
    NULL
};


static int bf_sensor_create_symlink(struct platform_device *pdev)
{
    char name[7];
    sprintf(name, DIRNAME, pdev->id);
    return sysfs_create_link(g_data->root_kobj, &pdev->dev.kobj, name);
}

static void bf_sensor_remove_symlink(struct platform_device *pdev)
{
    char name[7];
    sprintf(name, DIRNAME, pdev->id);
    return sysfs_remove_link(g_data->root_kobj, name);
}

static int bf_sensor_create_root_attr(void)
{
    g_data->root_kobj = create_sysfs_dir_and_attr(ROOT_DIRNAME,
            bf_get_switch_kobj(), &root_attr_group);
    if(g_data->root_kobj == NULL)
        return -EIO;
    return 0;
}

static void bf_sensor_remove_root_attr(void)
{
    remove_sysfs_dir_and_attr(g_data->root_kobj, &root_attr_group);
}


static int bf_sensor_probe(struct platform_device *pdev)
{
    bf_print("found dev id=%d\n", pdev->id);
    return bf_sensor_create_symlink(pdev);
}

static int bf_sensor_remove(struct platform_device *pdev)
{
    bf_sensor_remove_symlink(pdev);
    return 0;
}

DECL_PLATFORM_DRIVER(bf_sensor, DRVNAME);


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

static int bf_sensor_register(void)
{
    int i, j, ret;

    ret = platform_driver_register(&bf_sensor_driver);
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
    platform_driver_unregister(&bf_sensor_driver);
dri_reg_err:
    return ret;
}

static void bf_sensor_unregister(void)
{
    int i;
    for (i = 0 ; i < NUM_DEV ; i++)
        platform_device_unregister(&g_data->pdev[i]);
    platform_driver_unregister(&bf_sensor_driver);
}


static int __init bf_sensor_init(void)
{
    int ret;

    g_data = kzalloc(sizeof(struct bf_sensor_drv_data), GFP_KERNEL);
    if (!g_data) {
        ret = -ENOMEM;
        goto alloc_err;
    }

    ret = bf_sensor_create_root_attr();
    if (ret < 0)
        goto create_root_sysfs_err;

    ret = bf_sensor_register();
    if (ret < 0)
        goto reg_dev_err;

    return 0;

reg_dev_err:
    bf_sensor_remove_root_attr();
create_root_sysfs_err:
    kfree(g_data);
alloc_err:
    return ret;
}

static void __exit bf_sensor_exit(void)
{
    bf_sensor_unregister();
    bf_sensor_remove_root_attr();
    kfree(g_data);
}


MODULE_AUTHOR("Edgecore");
MODULE_DESCRIPTION("BF Sensor Driver");
MODULE_LICENSE("GPL");

module_init(bf_sensor_init);
module_exit(bf_sensor_exit);
