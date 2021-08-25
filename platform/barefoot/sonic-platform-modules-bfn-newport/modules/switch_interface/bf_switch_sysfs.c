/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * /sys/switch dir creation and export some symbols and utilities.
 */

#include <linux/module.h>
#include <linux/platform_device.h>

enum switch_log_levels{
    LOG_ERR = 0X1,
    LOG_WARN = 0X2,
    LOG_INFO = 0X4,
    LOG_DEBUG = 0X8
};
#define DEFAULT_LOGLEVEL_IDX 0  // 0 = LOG_WARN, kzalloc g_data works.

struct kobject *switch_kobj = NULL;
static int level_map[] = {LOG_WARN, LOG_ERR, LOG_INFO, LOG_DEBUG};

int userlevel_to_kernlevel(int level){
    int i, ret = DEFAULT_LOGLEVEL_IDX; //default level while not exist
    for(i=0 ; i<ARRAY_SIZE(level_map) ; i++){
        if(level_map[i] == level){
            ret = i;
            break;
        }
    }
    return ret;
}
EXPORT_SYMBOL(userlevel_to_kernlevel);

int kernlevel_to_userlevel(int level){
    if(level >= ARRAY_SIZE(level_map))
        return -EINVAL;
    return level_map[level];
}
EXPORT_SYMBOL(kernlevel_to_userlevel);

static int __init bf_switch_sysfs_init(void)
{
    switch_kobj = kobject_create_and_add("switch", NULL);
    if(switch_kobj==NULL)
        return -1;
    return 0;
}

static void __exit bf_switch_sysfs_exit(void)
{
    kobject_put(switch_kobj);
}

struct kobject * bf_get_switch_kobj(void)
{
    return switch_kobj;
}
EXPORT_SYMBOL(bf_get_switch_kobj);

struct kobject * create_sysfs_dir_and_attr(char *dir_name,
        struct kobject *parent, struct attribute_group *attrs)
{
    int status;

    struct kobject *kobj = kobject_create_and_add(dir_name, parent);
    if (kobj == NULL) {
        pr_err("Couldn't create %s kobject\r\n", dir_name);
        return NULL;
    }

    if ((status = sysfs_create_group(kobj, attrs)) != 0) {
        pr_err("Couldn't create sysfs interface of %s kobject(%d)\r\n",
                dir_name, status);
        kobject_put(kobj);
        return NULL;
    }

    return kobj;
}
EXPORT_SYMBOL(create_sysfs_dir_and_attr);

void remove_sysfs_dir_and_attr(struct kobject *kobj, struct attribute_group *attr)
{
    if(kobj == NULL)
        return;

    sysfs_remove_group(kobj, attr);
    kobject_put(kobj);
}
EXPORT_SYMBOL(remove_sysfs_dir_and_attr);

static void blanked_device_release(struct device *dev){ }

static inline void init_pdev(struct platform_device *pdev, char *name, int id,
        const struct attribute_group **groups)
{
    pdev->name = name;
    pdev->id = id;
    pdev->dev.groups = groups;
    pdev->dev.release = blanked_device_release;
}

int register_device_and_driver(struct platform_driver *driver, char *name,
                               struct platform_device devs[], size_t num_dev,
                               const struct attribute_group *attrs[])
{
    int i, j, ret;

    ret = platform_driver_register(driver);
    if (ret < 0)
        goto dri_reg_err;

    for (i = 0 ; i < num_dev ; i++) {
        struct platform_device *pdev = &devs[i];
        init_pdev(pdev, name, i, attrs);
        ret = platform_device_register(pdev);
        if (ret != 0)
            goto dev_reg_err;
    }
    return 0;

dev_reg_err:
    for(j=0 ; j<i ; j++)
        platform_device_unregister(&devs[j]);
    platform_driver_unregister(driver);
dri_reg_err:
    return ret;
}
EXPORT_SYMBOL(register_device_and_driver);

void unregister_device_and_driver(struct platform_driver *driver,
        struct platform_device devs[], size_t num_dev)
{
    int i;
    for (i = 0 ; i < num_dev ; i++)
        platform_device_unregister(&devs[i]);
    platform_driver_unregister(driver);
}
EXPORT_SYMBOL(unregister_device_and_driver);

MODULE_AUTHOR("Edgecore");
MODULE_DESCRIPTION("BF Switch Sysfs");
MODULE_LICENSE("GPL");

module_init(bf_switch_sysfs_init);
module_exit(bf_switch_sysfs_exit);
