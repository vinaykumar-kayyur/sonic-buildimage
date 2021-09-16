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
#include "bf_module_util.h"
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
BF_DEV_ATTR_RO(max_output_power, na, PSU_POUT_MAX_ATTR_ID);
BF_DEV_ATTR_RO(in_curr, psu, PSU_IIN_ATTR_ID);
BF_DEV_ATTR_RO(in_vol, psu, PSU_VIN_ATTR_ID);
BF_DEV_ATTR_RO(in_power, psu, PSU_PIN_ATTR_ID);
BF_DEV_ATTR_RO(out_curr, psu, PSU_IOUT_ATTR_ID);
BF_DEV_ATTR_RO(out_vol, psu, PSU_VOUT_ATTR_ID);
BF_DEV_ATTR_RO(out_power, psu, PSU_POUT_ATTR_ID);
BF_DEV_ATTR_RO(status, psu, PSU_STATUS_ATTR_ID);
BF_DEV_ATTR_RO(led_status, na, PSU_LED_STATUS_ATTR_ID);
BF_DEV_ATTR_RO(type, na, PSU_TYPE_ATTR_ID);
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
BF_DEV_ATTR_RO(temp_type, na, TEMP_TYPE_ATTR_ID);
BF_DEV_ATTR_RO(temp_max, na, TEMP_MAX_ATTR_ID);
BF_DEV_ATTR_RO(temp_max_hyst, na, TEMP_MAX_HYST_ATTR_ID);
BF_DEV_ATTR_RO(temp_min, na, TEMP_MIN_ATTR_ID);
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


static int __init bf_psu_init(void)
{
    int ret;

    g_data = kzalloc(sizeof(struct bf_psu_drv_data), GFP_KERNEL);
    if (!g_data) {
        ret = -ENOMEM;
        goto alloc_err;
    }
    init_bf_print(KBUILD_MODNAME, &g_data->loglevel);
    mutex_init(&g_data->update_lock);

    ret = bf_psu_create_root_attr();
    if (ret < 0)
        goto create_root_sysfs_err;

    /* Set up IPMI interface */
    ret = init_ipmi_data(&g_data->ipmi, 0);
    if (ret)
        goto ipmi_err;

    ret = register_device_and_driver(&bf_psu_driver, PSU_DRVNAME,
            g_data->psu_pdev, ARRAY_SIZE(g_data->psu_pdev), dev_attr_groups);
    if (ret < 0)
        goto reg_dev_err;

    ret = register_device_and_driver(&bf_temp_driver, TEMP_DRVNAME,
            g_data->temp_pdev, ARRAY_SIZE(g_data->temp_pdev), temp_attr_groups);
    if (ret < 0)
        goto reg_temp_err;

    return 0;

reg_temp_err:
    unregister_device_and_driver(&bf_psu_driver, g_data->psu_pdev,
                                 ARRAY_SIZE(g_data->psu_pdev));
reg_dev_err:
    ipmi_destroy_user(g_data->ipmi.user);
ipmi_err:
    bf_psu_remove_root_attr();
create_root_sysfs_err:
    deinit_bf_print();
    kfree(g_data);
alloc_err:
    return ret;
}

static void __exit bf_psu_exit(void)
{
    unregister_device_and_driver(&bf_temp_driver, g_data->temp_pdev,
                               ARRAY_SIZE(g_data->temp_pdev));
    unregister_device_and_driver(&bf_psu_driver, g_data->psu_pdev,
                                 ARRAY_SIZE(g_data->psu_pdev));
    ipmi_destroy_user(g_data->ipmi.user);
    bf_psu_remove_root_attr();
    deinit_bf_print();
    kfree(g_data);
}


MODULE_AUTHOR("Edgecore");
MODULE_DESCRIPTION("BF PSU Driver");
MODULE_LICENSE("GPL");

module_init(bf_psu_init);
module_exit(bf_psu_exit);
