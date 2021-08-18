/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * /sys/switch dir creation and exporting
 */

#include <linux/module.h>

struct kobject *switch_kobj = NULL;


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

MODULE_AUTHOR("Edgecore");
MODULE_DESCRIPTION("BF Switch Sysfs");
MODULE_LICENSE("GPL");

module_init(bf_switch_sysfs_init);
module_exit(bf_switch_sysfs_exit);
