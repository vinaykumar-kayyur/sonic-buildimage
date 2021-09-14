/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * kernel driver module for bf fpga switch interface
 */

#define pr_fmt(fmt) "%s:%s: " fmt, KBUILD_MODNAME,  __func__

#include <linux/module.h>
#include <linux/slab.h>
#include <linux/platform_device.h>
#include "bf_switch_sysfs.h"
#include "bf_module_util.h"
#include "bf_fpga_swi_driver.h"
#include "bf_fpga_swi_api.h"

#define DRVNAME "bf_fpga_swi"
#define DIRNAME "fpga%d"
#define ROOT_DIRNAME "fpga"

struct bf_fpga_swi_drv_data *g_data = NULL;
int *module_loglevel = NULL;

/* Root Attributes */
BF_DEV_ATTR_RO(debug, debug, DEBUG_ATTR_ID);
BF_DEV_ATTR_RW(loglevel, loglevel, LOGLEVEL_ATTR_ID);
BF_DEV_ATTR_RO(num, devnum, NUM_DEV_ATTR_ID);

static struct attribute *root_attrs[] = {
    &sensor_dev_attr_debug.dev_attr.attr,
    &sensor_dev_attr_loglevel.dev_attr.attr,
    &sensor_dev_attr_num.dev_attr.attr,
    NULL
};

static struct attribute_group root_attr_group = {
    .attrs = root_attrs,
};

/* fpga_swi Attributes */
BF_DEV_ATTR_RO(alias, fpga_alias, FPGA_ALIAS_ATTR_ID);
BF_DEV_ATTR_RO(type, fpga_type, FPGA_TYPE_ATTR_ID);
BF_DEV_ATTR_RO(hw_version, fpga_ver, FPGA_HWVER_ATTR_ID);
BF_DEV_ATTR_RO(board_version, na, FPGA_BDVER_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c0, reset_reg, FPGA_RESET_I2C0_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c1, reset_reg, FPGA_RESET_I2C1_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c2, reset_reg, FPGA_RESET_I2C2_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c3, reset_reg, FPGA_RESET_I2C3_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c4, reset_reg, FPGA_RESET_I2C4_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c5, reset_reg, FPGA_RESET_I2C5_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c6, reset_reg, FPGA_RESET_I2C6_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c7, reset_reg, FPGA_RESET_I2C7_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c8, reset_reg, FPGA_RESET_I2C8_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c9, reset_reg, FPGA_RESET_I2C9_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c10, reset_reg, FPGA_RESET_I2C10_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c11, reset_reg, FPGA_RESET_I2C11_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c12, reset_reg, FPGA_RESET_I2C12_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c13, reset_reg, FPGA_RESET_I2C13_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c14, reset_reg, FPGA_RESET_I2C14_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c15, reset_reg, FPGA_RESET_I2C15_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c16, reset_reg, FPGA_RESET_I2C16_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c17, reset_reg, FPGA_RESET_I2C17_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c18, reset_reg, FPGA_RESET_I2C18_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c19, reset_reg, FPGA_RESET_I2C19_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c20, reset_reg, FPGA_RESET_I2C20_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c21, reset_reg, FPGA_RESET_I2C21_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c22, reset_reg, FPGA_RESET_I2C22_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c23, reset_reg, FPGA_RESET_I2C23_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c24, reset_reg, FPGA_RESET_I2C24_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c25, reset_reg, FPGA_RESET_I2C25_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c26, reset_reg, FPGA_RESET_I2C26_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c27, reset_reg, FPGA_RESET_I2C27_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c28, reset_reg, FPGA_RESET_I2C28_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c29, reset_reg, FPGA_RESET_I2C29_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c30, reset_reg, FPGA_RESET_I2C30_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c31, reset_reg, FPGA_RESET_I2C31_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c32, reset_reg, FPGA_RESET_I2C32_ATTR_ID);
BF_DEV_ATTR_RW(reset_i2c33, reset_reg, FPGA_RESET_I2C33_ATTR_ID);


static struct attribute *dev_attrs[] = {
    &sensor_dev_attr_alias.dev_attr.attr,
    &sensor_dev_attr_type.dev_attr.attr,
    &sensor_dev_attr_hw_version.dev_attr.attr,
    &sensor_dev_attr_board_version.dev_attr.attr,
    &sensor_dev_attr_reset_i2c0.dev_attr.attr,
    &sensor_dev_attr_reset_i2c1.dev_attr.attr,
    &sensor_dev_attr_reset_i2c2.dev_attr.attr,
    &sensor_dev_attr_reset_i2c3.dev_attr.attr,
    &sensor_dev_attr_reset_i2c4.dev_attr.attr,
    &sensor_dev_attr_reset_i2c5.dev_attr.attr,
    &sensor_dev_attr_reset_i2c6.dev_attr.attr,
    &sensor_dev_attr_reset_i2c7.dev_attr.attr,
    &sensor_dev_attr_reset_i2c8.dev_attr.attr,
    &sensor_dev_attr_reset_i2c9.dev_attr.attr,
    &sensor_dev_attr_reset_i2c10.dev_attr.attr,
    &sensor_dev_attr_reset_i2c11.dev_attr.attr,
    &sensor_dev_attr_reset_i2c12.dev_attr.attr,
    &sensor_dev_attr_reset_i2c13.dev_attr.attr,
    &sensor_dev_attr_reset_i2c14.dev_attr.attr,
    &sensor_dev_attr_reset_i2c15.dev_attr.attr,
    &sensor_dev_attr_reset_i2c16.dev_attr.attr,
    &sensor_dev_attr_reset_i2c17.dev_attr.attr,
    &sensor_dev_attr_reset_i2c18.dev_attr.attr,
    &sensor_dev_attr_reset_i2c19.dev_attr.attr,
    &sensor_dev_attr_reset_i2c20.dev_attr.attr,
    &sensor_dev_attr_reset_i2c21.dev_attr.attr,
    &sensor_dev_attr_reset_i2c22.dev_attr.attr,
    &sensor_dev_attr_reset_i2c23.dev_attr.attr,
    &sensor_dev_attr_reset_i2c24.dev_attr.attr,
    &sensor_dev_attr_reset_i2c25.dev_attr.attr,
    &sensor_dev_attr_reset_i2c26.dev_attr.attr,
    &sensor_dev_attr_reset_i2c27.dev_attr.attr,
    &sensor_dev_attr_reset_i2c28.dev_attr.attr,
    &sensor_dev_attr_reset_i2c29.dev_attr.attr,
    &sensor_dev_attr_reset_i2c30.dev_attr.attr,
    &sensor_dev_attr_reset_i2c31.dev_attr.attr,
    &sensor_dev_attr_reset_i2c32.dev_attr.attr,
    &sensor_dev_attr_reset_i2c33.dev_attr.attr,
    NULL
};

static struct attribute_group dev_attr_group = {
    .attrs = dev_attrs,
};
static const struct attribute_group *dev_attr_groups[] = {
    &dev_attr_group,
    NULL
};


static int bf_fpga_swi_create_symlink(struct platform_device *pdev)
{
    char name[7];
    sprintf(name, DIRNAME, pdev->id + 1);
    return sysfs_create_link(g_data->root_kobj, &pdev->dev.kobj, name);
}

static void bf_fpga_swi_remove_symlink(struct platform_device *pdev)
{
    char name[7];
    sprintf(name, DIRNAME, pdev->id + 1);
    return sysfs_remove_link(g_data->root_kobj, name);
}

static int bf_fpga_swi_create_root_attr(void)
{
    g_data->root_kobj = create_sysfs_dir_and_attr(ROOT_DIRNAME,
            bf_get_switch_kobj(), &root_attr_group);
    if(g_data->root_kobj == NULL)
        return -EIO;
    return 0;
}

static void bf_fpga_swi_remove_root_attr(void)
{
    remove_sysfs_dir_and_attr(g_data->root_kobj, &root_attr_group);
}


static int bf_fpga_swi_probe(struct platform_device *pdev)
{
    bf_print("found dev id=%d\n", pdev->id);
    return bf_fpga_swi_create_symlink(pdev);
}

static int bf_fpga_swi_remove(struct platform_device *pdev)
{
    bf_fpga_swi_remove_symlink(pdev);
    return 0;
}

DECL_PLATFORM_DRIVER(bf_fpga_swi, DRVNAME);


static int __init bf_fpga_swi_init(void)
{
    int ret;

    g_data = kzalloc(sizeof(struct bf_fpga_swi_drv_data), GFP_KERNEL);
    if (!g_data) {
        ret = -ENOMEM;
        goto alloc_err;
    }
    module_loglevel = &g_data->loglevel;

    ret = bf_fpga_swi_create_root_attr();
    if (ret < 0)
        goto create_root_sysfs_err;

    ret = register_device_and_driver(&bf_fpga_swi_driver, DRVNAME,
            g_data->pdev, ARRAY_SIZE(g_data->pdev), dev_attr_groups);
    if (ret < 0)
        goto reg_dev_err;

    return 0;

reg_dev_err:
    bf_fpga_swi_remove_root_attr();
create_root_sysfs_err:
    module_loglevel = NULL;
    kfree(g_data);
alloc_err:
    return ret;
}

static void __exit bf_fpga_swi_exit(void)
{
    unregister_device_and_driver(&bf_fpga_swi_driver, g_data->pdev,
                                 ARRAY_SIZE(g_data->pdev));
    bf_fpga_swi_remove_root_attr();
    module_loglevel = NULL;
    kfree(g_data);
}


MODULE_AUTHOR("Edgecore");
MODULE_DESCRIPTION("BF fpga_swi Driver");
MODULE_LICENSE("GPL");

module_init(bf_fpga_swi_init);
module_exit(bf_fpga_swi_exit);
