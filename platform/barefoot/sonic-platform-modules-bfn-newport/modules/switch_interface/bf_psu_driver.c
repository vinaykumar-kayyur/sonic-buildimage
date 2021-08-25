/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * kernel driver module for bf psu
 */

#define pr_fmt(fmt) "%s:%s: " fmt, KBUILD_MODNAME,  __func__

#include <linux/module.h>
#include <linux/slab.h>
#include <linux/platform_device.h>
#include "bf_switch_sysfs.h"
#include "bf_psu_driver.h"
#include "bf_psu_api.h"

#define PSU_DRVNAME "bf_psu"
#define TEMP_DRVNAME "bf_psu_temp"
#define PSU_DIRNAME "psu%d"
#define TEMP_DIRNAME "temp%d"
#define ROOT_DIRNAME "psu"

struct bf_psu_drv_data *g_data = NULL;

/* Root Attributes */
BF_DEV_ATTR_RO(debug, debug, DEBUG_ATTR_ID);
BF_DEV_ATTR_RW(loglevel, loglevel, LOGLEVEL_ATTR_ID);
BF_DEV_ATTR_RO(num, devnum, NUM_ATTR_ID);

static struct attribute *root_attrs[] = {
    &sensor_dev_attr_debug.dev_attr.attr,
    &sensor_dev_attr_loglevel.dev_attr.attr,
    &sensor_dev_attr_num.dev_attr.attr,
    NULL
};

static struct attribute_group root_attr_group = {
    .attrs = root_attrs,
};

/* PSU Attributes */
BF_DEV_ATTR_RO(model_name, psu, PSU_MODEL_ATTR_ID);
BF_DEV_ATTR_RO(serial_number, psu, PSU_SERIAL_ATTR_ID);
BF_DEV_ATTR_RO(date, psu, PSU_DATE_ATTR_ID);
BF_DEV_ATTR_RO(vendor, psu, PSU_VENDOR_ATTR_ID);
BF_DEV_ATTR_RO(hardware_version, psu, PSU_HW_VER_ATTR_ID);
BF_DEV_ATTR_RO(alarm, psu, PSU_ALARM_ATTR_ID);
BF_DEV_ATTR_RO(alarm_threshold_curr, psu, PSU_ALARM_TH_CURR_ATTR_ID);
BF_DEV_ATTR_RO(alarm_threshold_vol, psu, PSU_ALARM_TH_VOL_ATTR_ID);
BF_DEV_ATTR_RO(part_number, psu, PSU_PART_NUM_ATTR_ID);
BF_DEV_ATTR_RO(max_output_power, psu, PSU_POUT_MAX_ATTR_ID);
BF_DEV_ATTR_RO(in_curr, psu, PSU_IIN_ATTR_ID);
BF_DEV_ATTR_RO(in_vol, psu, PSU_VIN_ATTR_ID);
BF_DEV_ATTR_RO(in_power, psu, PSU_PIN_ATTR_ID);
BF_DEV_ATTR_RO(out_curr, psu, PSU_IOUT_ATTR_ID);
BF_DEV_ATTR_RO(out_vol, psu, PSU_VOUT_ATTR_ID);
BF_DEV_ATTR_RO(out_power, psu, PSU_POUT_ATTR_ID);
BF_DEV_ATTR_RO(status, psu, PSU_STATUS_ATTR_ID);
BF_DEV_ATTR_RO(led_status, psu, PSU_LED_STATUS_ATTR_ID);
BF_DEV_ATTR_RO(type, psu, PSU_TYPE_ATTR_ID);
BF_DEV_ATTR_RO(num_temp_sensors, num_temp, PSU_NUM_TEMP_ATTR_ID);
BF_DEV_ATTR_RO(fan_speed, psu, PSU_FAN_SPEED_ATTR_ID);

static struct attribute *dev_attrs[] = {
    &sensor_dev_attr_model_name.dev_attr.attr,
    &sensor_dev_attr_serial_number.dev_attr.attr,
    &sensor_dev_attr_date.dev_attr.attr,
    &sensor_dev_attr_vendor.dev_attr.attr,
    &sensor_dev_attr_hardware_version.dev_attr.attr,
    &sensor_dev_attr_alarm.dev_attr.attr,
    &sensor_dev_attr_alarm_threshold_curr.dev_attr.attr,
    &sensor_dev_attr_alarm_threshold_vol.dev_attr.attr,
    &sensor_dev_attr_part_number.dev_attr.attr,
    &sensor_dev_attr_max_output_power.dev_attr.attr,
    &sensor_dev_attr_in_curr.dev_attr.attr,
    &sensor_dev_attr_in_vol.dev_attr.attr,
    &sensor_dev_attr_in_power.dev_attr.attr,
    &sensor_dev_attr_out_curr.dev_attr.attr,
    &sensor_dev_attr_out_vol.dev_attr.attr,
    &sensor_dev_attr_out_power.dev_attr.attr,
    &sensor_dev_attr_status.dev_attr.attr,
    &sensor_dev_attr_led_status.dev_attr.attr,
    &sensor_dev_attr_type.dev_attr.attr,
    &sensor_dev_attr_num_temp_sensors.dev_attr.attr,
    &sensor_dev_attr_fan_speed.dev_attr.attr,
    NULL
};

static struct attribute_group dev_attr_group = {
    .attrs = dev_attrs,
};
static const struct attribute_group *dev_attr_groups[] = {
    &dev_attr_group,
    NULL
};


/* Temp Attributes */
BF_DEV_ATTR_RO(temp_alias, temp, TEMP_ALIAS_ATTR_ID);
BF_DEV_ATTR_RO(temp_type, temp, TEMP_TYPE_ATTR_ID);
BF_DEV_ATTR_RO(temp_max, temp, TEMP_MAX_ATTR_ID);
BF_DEV_ATTR_RO(temp_max_hyst, temp, TEMP_MAX_HYST_ATTR_ID);
BF_DEV_ATTR_RO(temp_min, temp, TEMP_MIN_ATTR_ID);
BF_DEV_ATTR_RO(temp_input, temp, TEMP_INPUT_ATTR_ID);

static struct attribute *temp_attrs[] = {
    &sensor_dev_attr_temp_alias.dev_attr.attr,
    &sensor_dev_attr_temp_type.dev_attr.attr,
    &sensor_dev_attr_temp_max.dev_attr.attr,
    &sensor_dev_attr_temp_max_hyst.dev_attr.attr,
    &sensor_dev_attr_temp_min.dev_attr.attr,
    &sensor_dev_attr_temp_input.dev_attr.attr,
    NULL
};

static struct attribute_group temp_attr_group = {
    .attrs = temp_attrs,
};
static const struct attribute_group *temp_attr_groups[] = {
    &temp_attr_group,
    NULL
};


static int bf_psu_create_symlink(struct platform_device *pdev)
{
    char name[6];
    sprintf(name, PSU_DIRNAME, pdev->id + 1);
    return sysfs_create_link(g_data->root_kobj, &pdev->dev.kobj, name);
}

static void bf_psu_remove_symlink(struct platform_device *pdev)
{
    char name[6];
    sprintf(name, PSU_DIRNAME, pdev->id + 1);
    return sysfs_remove_link(g_data->root_kobj, name);
}

static int bf_temp_create_symlink(struct platform_device *pdev)
{
    int t_idx = pdev->id % NUM_TEMP_PER_DEV;
    int p_idx = pdev->id / NUM_TEMP_PER_DEV;
    char name[7];
    struct kobject *kobj = &g_data->psu_pdev[p_idx].dev.kobj;
    sprintf(name, TEMP_DIRNAME, t_idx);
    return sysfs_create_link(kobj, &pdev->dev.kobj, name);
}

static void bf_temp_remove_symlink(struct platform_device *pdev)
{
    int p_idx = pdev->id / NUM_TEMP_PER_DEV;
    int t_idx = pdev->id % NUM_TEMP_PER_DEV;
    char name[7];
    struct kobject *kobj = &g_data->psu_pdev[p_idx].dev.kobj;
    sprintf(name, TEMP_DIRNAME, t_idx);
    return sysfs_remove_link(kobj, name);
}

static int bf_psu_create_root_attr(void)
{
    g_data->root_kobj = create_sysfs_dir_and_attr(ROOT_DIRNAME,
            bf_get_switch_kobj(), &root_attr_group);
    if(g_data->root_kobj == NULL)
        return -EIO;
    return 0;
}

static void bf_psu_remove_root_attr(void)
{
    remove_sysfs_dir_and_attr(g_data->root_kobj, &root_attr_group);
}


static int bf_psu_probe(struct platform_device *pdev)
{
    bf_print("found dev id=%d\n", pdev->id);
    return bf_psu_create_symlink(pdev);
}

static int bf_psu_remove(struct platform_device *pdev)
{
    bf_psu_remove_symlink(pdev);
    return 0;
}

DECL_PLATFORM_DRIVER(bf_psu, PSU_DRVNAME);

static int bf_temp_probe(struct platform_device *pdev)
{
    bf_print("found dev id=%d\n", pdev->id);
    return bf_temp_create_symlink(pdev);
}

static int bf_temp_remove(struct platform_device *pdev)
{
    bf_temp_remove_symlink(pdev);
    return 0;
}

DECL_PLATFORM_DRIVER(bf_temp, TEMP_DRVNAME);


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

static int bf_psu_register(void)
{
    int i, j, ret;

    ret = platform_driver_register(&bf_psu_driver);
    if (ret < 0)
        goto dri_reg_err;

    for (i = 0 ; i < NUM_DEV ; i++) {
        struct platform_device *pdev = &g_data->psu_pdev[i];
        init_pdev(pdev, PSU_DRVNAME, i, dev_attr_groups);
        ret = platform_device_register(pdev);
        if (ret != 0)
            goto dev_reg_err;
    }
    return 0;

dev_reg_err:
    for(j=0 ; j<i ; j++)
        platform_device_unregister(&g_data->psu_pdev[j]);
    platform_driver_unregister(&bf_psu_driver);
dri_reg_err:
    return ret;
}

static void bf_psu_unregister(void)
{
    int i;
    for (i = 0 ; i < NUM_DEV ; i++)
        platform_device_unregister(&g_data->psu_pdev[i]);
    platform_driver_unregister(&bf_psu_driver);
}

static int bf_temp_register(void)
{
    int i, j, ret;

    ret = platform_driver_register(&bf_temp_driver);
    if (ret < 0)
        goto temp_dri_reg_err;

    for (i = 0 ; i < NUM_TEMP ; i++) {
        struct platform_device *pdev = &g_data->temp_pdev[i];
        init_pdev(pdev, TEMP_DRVNAME, i, temp_attr_groups);
        ret = platform_device_register(pdev);
        if (ret != 0)
            goto temp_dev_reg_err;
    }
    return 0;

temp_dev_reg_err:
    for(j=0 ; j<i ; j++)
        platform_device_unregister(&g_data->temp_pdev[j]);
    platform_driver_unregister(&bf_temp_driver);
temp_dri_reg_err:
    return ret;
}

static void bf_temp_unregister(void)
{
    int i;
    for (i = 0 ; i < NUM_TEMP ; i++)
        platform_device_unregister(&g_data->temp_pdev[i]);
    platform_driver_unregister(&bf_temp_driver);
}


static int __init bf_psu_init(void)
{
    int ret;

    g_data = kzalloc(sizeof(struct bf_psu_drv_data), GFP_KERNEL);
    if (!g_data) {
        ret = -ENOMEM;
        goto alloc_err;
    }

    ret = bf_psu_create_root_attr();
    if (ret < 0)
        goto create_root_sysfs_err;

    ret = bf_psu_register();
    if (ret < 0)
        goto reg_dev_err;

    ret = bf_temp_register();
    if (ret < 0)
        goto reg_temp_err;

    return 0;

reg_temp_err:
    bf_psu_unregister();
reg_dev_err:
    bf_psu_remove_root_attr();
create_root_sysfs_err:
    kfree(g_data);
alloc_err:
    return ret;
}

static void __exit bf_psu_exit(void)
{
    bf_temp_unregister();
    bf_psu_unregister();
    bf_psu_remove_root_attr();
    kfree(g_data);
}


MODULE_AUTHOR("Edgecore");
MODULE_DESCRIPTION("BF PSU Driver");
MODULE_LICENSE("GPL");

module_init(bf_psu_init);
module_exit(bf_psu_exit);
