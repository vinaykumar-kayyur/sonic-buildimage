/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * kernel driver module for bf wdt
 */

#define pr_fmt(fmt) "%s:%s: " fmt, KBUILD_MODNAME,  __func__

#include <linux/module.h>
#include <linux/slab.h>
#include <linux/platform_device.h>
#include "bf_switch_sysfs.h"
#include "bf_module_util.h"
#include "bf_watchdog_driver.h"
#include "bf_watchdog_api.h"

#define ROOT_DIRNAME "watchdog"

struct bf_wdt_drv_data *g_data = NULL;

/* Root Attributes */
BF_DEV_ATTR_RO(debug, debug, DEBUG_ATTR_ID);
BF_DEV_ATTR_RW(loglevel, loglevel, LOGLEVEL_ATTR_ID);
BF_DEV_ATTR_RO(identify, identify, IDENTIFY_ATTR_ID);
BF_DEV_ATTR_RO(state, wdt, STATE_ATTR_ID);
BF_DEV_ATTR_RO(timeleft, wdt, TIMELEFT_ATTR_ID);
BF_DEV_ATTR_RW(timeout, wdt, TIMEOUT_ATTR_ID);
BF_DEV_ATTR_WO(reset, wdt, RESET_ATTR_ID);
BF_DEV_ATTR_RW(enable, wdt, ENABLE_ATTR_ID);

static struct attribute *root_attrs[] = {
    &sensor_dev_attr_debug.dev_attr.attr,
    &sensor_dev_attr_loglevel.dev_attr.attr,
    &sensor_dev_attr_identify.dev_attr.attr,
    &sensor_dev_attr_state.dev_attr.attr,
    &sensor_dev_attr_timeleft.dev_attr.attr,
    &sensor_dev_attr_timeout.dev_attr.attr,
    &sensor_dev_attr_reset.dev_attr.attr,
    &sensor_dev_attr_enable.dev_attr.attr,
    NULL
};

static struct attribute_group root_attr_group = {
    .attrs = root_attrs,
};

static int bf_wdt_create_root_attr(void)
{
    g_data->root_kobj = create_sysfs_dir_and_attr(ROOT_DIRNAME,
            bf_get_switch_kobj(), &root_attr_group);
    if(g_data->root_kobj == NULL)
        return -EIO;
    return 0;
}

static void bf_wdt_remove_root_attr(void)
{
    remove_sysfs_dir_and_attr(g_data->root_kobj, &root_attr_group);
}

static int __init bf_wdt_init(void)
{
    int ret;

    g_data = kzalloc(sizeof(struct bf_wdt_drv_data), GFP_KERNEL);
    if (!g_data) {
        ret = -ENOMEM;
        goto alloc_err;
    }
    init_bf_print(KBUILD_MODNAME, &g_data->loglevel);
    mutex_init(&g_data->update_lock);

    ret = bf_wdt_create_root_attr();
    if (ret < 0)
        goto create_root_sysfs_err;

    /* Set up IPMI interface */
    ret = init_ipmi_data(&g_data->ipmi, 0);
    if (ret)
        goto ipmi_err;

    return 0;

ipmi_err:
    bf_wdt_remove_root_attr();
create_root_sysfs_err:
    deinit_bf_print();
    kfree(g_data);
alloc_err:
    return ret;
}

static void __exit bf_wdt_exit(void)
{
    ipmi_destroy_user(g_data->ipmi.user);
    bf_wdt_remove_root_attr();
    deinit_bf_print();
    kfree(g_data);
}


MODULE_AUTHOR("Edgecore");
MODULE_DESCRIPTION("BF Watchdog Driver");
MODULE_LICENSE("GPL");

module_init(bf_wdt_init);
module_exit(bf_wdt_exit);
