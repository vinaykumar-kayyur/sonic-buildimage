/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * kernel driver module for bf fan
 */

#include <linux/module.h>
#include <linux/slab.h>
#include <linux/platform_device.h>
#include "bf_switch_sysfs.h"
#include "bf_fan_driver.h"

#define FAN_DRVNAME "bf_fan"
#define MOTOR_DRVNAME "bf_fan_motor"

static struct bf_fan_drv_data *g_data = NULL;
/////////////////////////////////////////////////////

// dummy placeholder function for temp +++++++++++++
static ssize_t placeholder_show(struct device *dev, struct device_attribute *da,
                            char *buf)
{
    struct platform_device *pdev = to_platform_device(dev);
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
    printk("show fan, id=%d, name(%s) attr_idx=%d\n", pdev->id, da->attr.name, attr->index);
    // printk("--- IS_ERR dev(%d)\n", IS_ERR(dev));
    // printk("--- PTR_ERR dev(%ld)\n", PTR_ERR(dev));
    // printk("--- IS_ERR dev->init_name(%d)\n", IS_ERR(dev->init_name));
    // printk("--- PTR_ERR dev->init_name(%ld)\n", PTR_ERR(dev->init_name));
    // printk("--- IS_ERR kobj_name(%d)\n", IS_ERR(dev->kobj.name));
    // printk("--- PTR_ERR kobj_name(%ld)\n", PTR_ERR(dev->kobj.name));
    printk("--- dev->kobj.name(%s)\n", dev->kobj.name);
    return 0;
}
static ssize_t placeholder_store(struct device *dev, struct device_attribute *da,
                            const char *buf, size_t count)
{
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
    printk("set fan attr_idx=%d\n", attr->index);
    return 0;
}
// dummy placeholder function for temp +-------------------

// --- root attrs ---
BF_DEV_ATTR_RW(debug, placeholder, DEBUG_ATTR_ID);
BF_DEV_ATTR_RW(loglevel, placeholder, LOGLEVEL_ATTR_ID);
BF_DEV_ATTR_RO(num, placeholder, NUMFAN_ATTR_ID);

static struct attribute *root_attrs[] = {
    &sensor_dev_attr_debug.dev_attr.attr,
    &sensor_dev_attr_loglevel.dev_attr.attr,
    &sensor_dev_attr_num.dev_attr.attr,
    NULL
};

static struct attribute_group root_attr_group = {
    .attrs = root_attrs,
};
// --- fan attrs ---
BF_DEV_ATTR_RO(model_name, placeholder, FAN_MODEL_ATTR_ID);
BF_DEV_ATTR_RO(serial_number, placeholder, FAN_SERIAL_ATTR_ID);
BF_DEV_ATTR_RO(vendor, placeholder, FAN_VENDOR_ATTR_ID);
BF_DEV_ATTR_RO(part_number, placeholder, FAN_PARTNUM_ATTR_ID);
BF_DEV_ATTR_RO(hardware_version, placeholder, FAN_HWVER_ATTR_ID);
BF_DEV_ATTR_RO(num_motors, placeholder, FAN_NUMMOTOR_ATTR_ID);
BF_DEV_ATTR_RO(status, placeholder, FAN_STATUS_ATTR_ID);
BF_DEV_ATTR_RO(led_status, placeholder, FAN_LED_ATTR_ID);

static struct attribute *fan_attrs[] = {
    &sensor_dev_attr_model_name.dev_attr.attr,
    &sensor_dev_attr_serial_number.dev_attr.attr,
    &sensor_dev_attr_vendor.dev_attr.attr,
    &sensor_dev_attr_part_number.dev_attr.attr,
    &sensor_dev_attr_hardware_version.dev_attr.attr,
    &sensor_dev_attr_num_motors.dev_attr.attr,
    &sensor_dev_attr_status.dev_attr.attr,
    &sensor_dev_attr_led_status.dev_attr.attr,
    NULL
};

static struct attribute_group fan_attr_group = {
    .attrs = fan_attrs,
};
static const struct attribute_group *fan_attr_groups[] = {
    &fan_attr_group,
    NULL
};

// --- motor attrs ---
BF_DEV_ATTR_RO(speed, placeholder, MOTOR_SPEED_ATTR_ID);
BF_DEV_ATTR_RO(speed_tolerance, placeholder, MOTOR_SPEED_TOL_ATTR_ID);
BF_DEV_ATTR_RO(speed_target, placeholder, MOTOR_SPEED_TARGET_ATTR_ID);
BF_DEV_ATTR_RW(ratio, placeholder, MOTOR_RATIO_ATTR_ID);
BF_DEV_ATTR_RO(direction, placeholder, MOTOR_DIR_ATTR_ID);

static struct attribute *motor_attrs[] = {
    &sensor_dev_attr_speed.dev_attr.attr,
    &sensor_dev_attr_speed_tolerance.dev_attr.attr,
    &sensor_dev_attr_speed_target.dev_attr.attr,
    &sensor_dev_attr_ratio.dev_attr.attr,
    &sensor_dev_attr_direction.dev_attr.attr,
    NULL
};

static struct attribute_group motor_attr_group = {
    .attrs = motor_attrs,
};
static const struct attribute_group *motor_attr_groups[] = {
    &motor_attr_group,
    NULL
};

/////////////////////////////////////////////////////


static int bf_fan_create_symlink(struct platform_device *pdev)
{
    int id = pdev->id;
    char name[6];
    struct kobject *kobj = g_data->fan_root_kobj;
    struct kobject *target = &g_data->fan_pdev[id].dev.kobj;
    sprintf(name, "fan%d", id+1);
    return sysfs_create_link(kobj, target, name);
}

static void bf_fan_remove_symlink(struct platform_device *pdev)
{
    int id = pdev->id;
    char name[6];
    struct kobject *kobj = g_data->fan_root_kobj;
    sprintf(name, "fan%d", id+1);
    return sysfs_remove_link(kobj, name);
}

static int bf_motor_create_symlink(struct platform_device *pdev)
{
    int id = pdev->id;
    int m_idx = id % MOTOR_PER_FAN;
    int f_idx = id / MOTOR_PER_FAN;
    char name[8];
    struct kobject *kobj = &g_data->fan_pdev[f_idx].dev.kobj;
    struct kobject *target = &g_data->motor_pdev[id].dev.kobj;
    sprintf(name, "motor%d", m_idx);
    return sysfs_create_link(kobj, target, name);
}

static void bf_motor_remove_symlink(struct platform_device *pdev)
{
    int id = pdev->id;
    int f_idx = id / MOTOR_PER_FAN;
    int m_idx = id % MOTOR_PER_FAN;
    char name[8];
    struct kobject *kobj = &g_data->fan_pdev[f_idx].dev.kobj;
    sprintf(name, "motor%d", m_idx);
    return sysfs_remove_link(kobj, name);
}

static int bf_fan_create_root_attr(void)
{
    g_data->fan_root_kobj = create_sysfs_dir_and_attr("fan", bf_get_switch_kobj(),
            &root_attr_group);
    if(g_data->fan_root_kobj == NULL)
        return -EINVAL;
    return 0;
}

static void bf_fan_remove_root_attr(void)
{
    remove_sysfs_dir_and_attr(g_data->fan_root_kobj, &root_attr_group);
}

///////////////////////////////////////////////////////////////

static int bf_fan_probe(struct platform_device *pdev)
{
    dev_info(&pdev->dev, "bf_fan_probe, pdev id=%d\n", pdev->id);
    return bf_fan_create_symlink(pdev);
}

static int bf_fan_remove(struct platform_device *pdev)
{
    bf_fan_remove_symlink(pdev);
    return 0;
}

static struct platform_driver bf_fan_driver = {
    .probe = bf_fan_probe,
    .remove = bf_fan_remove,
    .driver = {
        .name = FAN_DRVNAME,
        .owner = THIS_MODULE,
    },
};

///////////////////////////////////////////////////////////
static int bf_motor_probe(struct platform_device *pdev)
{
    dev_info(&pdev->dev, "bf_motor_probe, pdev id=%d\n", pdev->id);
    return bf_motor_create_symlink(pdev);
}

static int bf_motor_remove(struct platform_device *pdev)
{
    bf_motor_remove_symlink(pdev);
    return 0;
}

static struct platform_driver bf_motor_driver = {
    .probe = bf_motor_probe,
    .remove = bf_motor_remove,
    .driver = {
        .name = MOTOR_DRVNAME,
        .owner = THIS_MODULE,
    },
};

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

static int fan_init(void)
{
    int i, j, ret;

    ret = platform_driver_register(&bf_fan_driver);
    if (ret < 0)
        goto fan_dri_reg_err;

    for (i = 0 ; i < NUM_FAN ; i++) {
        struct platform_device *pdev = &g_data->fan_pdev[i];
        init_pdev(pdev, FAN_DRVNAME, i, fan_attr_groups);
        ret = platform_device_register(pdev);
        if (ret != 0)
            goto fan_dev_reg_err;
    }
    return 0;

fan_dev_reg_err:
    for(j=0 ; j<i ; j++)
        platform_device_unregister(&g_data->fan_pdev[j]);
    platform_driver_unregister(&bf_fan_driver);
fan_dri_reg_err:
    return ret;
}

static void fan_exit(void)
{
    int i;
    for (i = 0 ; i < NUM_FAN ; i++)
        platform_device_unregister(&g_data->fan_pdev[i]);
    platform_driver_unregister(&bf_fan_driver);
}

static int motor_init(void)
{
    int i, j, ret;

    ret = platform_driver_register(&bf_motor_driver);
    if (ret < 0)
        goto mtr_dri_reg_err;

    for (i = 0 ; i < NUM_MOTOR ; i++) {
        struct platform_device *pdev = &g_data->motor_pdev[i];
        init_pdev(pdev, MOTOR_DRVNAME, i, motor_attr_groups);
        ret = platform_device_register(pdev);
        if (ret != 0)
            goto mtr_dev_reg_err;
    }
    return 0;

mtr_dev_reg_err:
    for(j=0 ; j<i ; j++)
        platform_device_unregister(&g_data->motor_pdev[j]);
    platform_driver_unregister(&bf_motor_driver);
mtr_dri_reg_err:
    return ret;
}

static void motor_exit(void)
{
    int i;
    for (i = 0 ; i < NUM_MOTOR ; i++)
        platform_device_unregister(&g_data->motor_pdev[i]);
    platform_driver_unregister(&bf_motor_driver);
}

static int __init bf_fan_init(void)
{
    int ret;

    g_data = kzalloc(sizeof(struct bf_fan_drv_data), GFP_KERNEL);
    if (!g_data) {
        ret = -ENOMEM;
        goto alloc_err;
    }

    ret = bf_fan_create_root_attr();
    if (ret < 0)
        goto create_root_sysfs_err;

    ret = fan_init();
    if (ret < 0)
        goto fan_init_err;

    ret = motor_init();
    if (ret < 0)
        goto motor_init_err;

    return 0;

motor_init_err:
fan_init_err:
    bf_fan_remove_root_attr();
create_root_sysfs_err:
    kfree(g_data);
alloc_err:
    return ret;
}

static void __exit bf_fan_exit(void)
{
    motor_exit();
    fan_exit();
    bf_fan_remove_root_attr();
    kfree(g_data);
}


MODULE_AUTHOR("Edgecore");
MODULE_DESCRIPTION("BF Fan Driver");
MODULE_LICENSE("GPL");

module_init(bf_fan_init);
module_exit(bf_fan_exit);
