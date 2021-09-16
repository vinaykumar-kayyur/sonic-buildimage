/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * kernel driver module for bf sysled
 */

#define pr_fmt(fmt) "%s:%s: " fmt, KBUILD_MODNAME,  __func__

#include <linux/module.h>
#include <linux/slab.h>
#include <linux/platform_device.h>
#include "bf_switch_sysfs.h"
#include "bf_module_util.h"
#include "bf_sysled_driver.h"
#include "bf_sysled_api.h"

#define SYSLED_DRVNAME "bf_sysled"
#define ROOT_DIRNAME "sysled"

struct bf_sysled_drv_data *g_data = NULL;

/* Root Attributes */
BF_DEV_ATTR_RO(debug, debug, DEBUG_ATTR_ID);
BF_DEV_ATTR_RW(loglevel, loglevel, LOGLEVEL_ATTR_ID);
BF_DEV_ATTR_RW(sys_led_status, sysled, SYSLED_SYS_STATUS_ATTR_ID);
BF_DEV_ATTR_RW(id_led_status, sysled, SYSLED_LOC_STATUS_ATTR_ID);
BF_DEV_ATTR_RO(bmc_led_status, na, SYSLED_BMC_STATUS_ATTR_ID);
BF_DEV_ATTR_RO(fan_led_status, na, SYSLED_FAN_STATUS_ATTR_ID);
BF_DEV_ATTR_RO(psu_led_status, na, SYSLED_PSU_STATUS_ATTR_ID);

static struct attribute *root_attrs[] = {
    &sensor_dev_attr_debug.dev_attr.attr,
    &sensor_dev_attr_loglevel.dev_attr.attr,
    &sensor_dev_attr_sys_led_status.dev_attr.attr,
    &sensor_dev_attr_id_led_status.dev_attr.attr, /*loc*/
    &sensor_dev_attr_bmc_led_status.dev_attr.attr,
    &sensor_dev_attr_fan_led_status.dev_attr.attr,
    &sensor_dev_attr_psu_led_status.dev_attr.attr,
    NULL
};

static struct attribute_group root_attr_group = {
    .attrs = root_attrs,
};

static int bf_sysled_create_root_attr(void)
{
    g_data->root_kobj = create_sysfs_dir_and_attr(ROOT_DIRNAME,
            bf_get_switch_kobj(), &root_attr_group);
    if(g_data->root_kobj == NULL)
        return -EIO;
    return 0;
}

static void bf_sysled_remove_root_attr(void)
{
    remove_sysfs_dir_and_attr(g_data->root_kobj, &root_attr_group);
}

static int __init bf_sysled_init(void)
{
    int ret;

    g_data = kzalloc(sizeof(struct bf_sysled_drv_data), GFP_KERNEL);
    if (!g_data) {
        ret = -ENOMEM;
        goto alloc_err;
    }
    init_bf_print(KBUILD_MODNAME, &g_data->loglevel);
    mutex_init(&g_data->update_lock);

    ret = bf_sysled_create_root_attr();
    if (ret < 0)
        goto create_root_sysfs_err;

    /* Set up IPMI interface */
    ret = init_ipmi_data(&g_data->ipmi, 0);
    if (ret)
        goto ipmi_err;

    return 0;

ipmi_err:
    bf_sysled_remove_root_attr();
create_root_sysfs_err:
    deinit_bf_print();
    kfree(g_data);
alloc_err:
    return ret;
}

static void __exit bf_sysled_exit(void)
{
    ipmi_destroy_user(g_data->ipmi.user);
    bf_sysled_remove_root_attr();
    deinit_bf_print();
    kfree(g_data);
}


MODULE_AUTHOR("Edgecore");
MODULE_DESCRIPTION("BF SYSLED Driver");
MODULE_LICENSE("GPL");

module_init(bf_sysled_init);
module_exit(bf_sysled_exit);
