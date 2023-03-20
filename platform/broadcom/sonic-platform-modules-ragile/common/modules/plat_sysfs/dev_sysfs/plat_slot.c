/*
 * plat_slot.c
 * Original Author: support 2020-02-17
 *
 * This module create slot kobjects and attributes in /sys/wb_plat/slot
 *
 * History
 *  [Version]        [Author]           [Date]            [Description]
 *   *  v1.0          support          2020-02-17        Initial version
 */

#include <linux/slab.h>

#include "./include/plat_switch.h"
#include "./include/sysfs_common.h"

#define SLOT_INFO(fmt, args...) LOG_INFO("slot: ", fmt, ##args)
#define SLOT_ERR(fmt, args...)  LOG_ERR("slot: ", fmt, ##args)
#define SLOT_DBG(fmt, args...)  LOG_DBG("slot: ", fmt, ##args)

struct slot_obj_t{
    struct switch_obj *obj;
};

struct slot_t{
    unsigned int slot_number;
    struct slot_obj_t *slot;
};

static int g_loglevel = 0;
static struct slot_t g_slot;
static struct switch_obj *g_slot_obj = NULL;
static struct switch_drivers_t *g_drv = NULL;

static ssize_t slot_number_show(struct switch_obj *obj, struct switch_attribute *attr, char *buf)
{
    return (ssize_t)snprintf(buf, PAGE_SIZE, "%d\n", g_slot.slot_number);
}

static ssize_t slot_present_status_show(struct switch_obj *obj, struct switch_attribute *attr, char *buf)
{
    unsigned int slot_index;
    int ret;

    slot_index = obj->index;
    SLOT_DBG("slot_present_status_show, slot index:%d\n",slot_index);
    check_p(g_drv);
    check_p(g_drv->get_slot_present_status);

    ret = g_drv->get_slot_present_status(slot_index);
    if(ret < 0) {
        return (ssize_t)snprintf(buf, PAGE_SIZE, "%s\n", WB_SYSFS_DEV_ERROR);
    }

    return (ssize_t)snprintf(buf, PAGE_SIZE, "%d\n", ret);
}

/************************************slot dir and attrs*******************************************/
static struct switch_attribute slot_number_att = __ATTR(num_slots, S_IRUGO, slot_number_show, NULL);

static struct attribute *slot_dir_attrs[] = {
    &slot_number_att.attr,
    NULL,
};

static struct attribute_group slot_root_attr_group = {
    .attrs = slot_dir_attrs,
};

/*******************************slot1 slot2 dir and attrs*******************************************/
static struct switch_attribute slot_present_status_att = __ATTR(present, S_IRUGO, slot_present_status_show, NULL);

static struct attribute *slot_attrs[] = {
    &slot_present_status_att.attr,
    NULL,
};

static struct attribute_group slot_attr_group = {
    .attrs = slot_attrs,
};

static int slot_sub_single_remove_kobj_and_attrs(unsigned int index)
{
    struct slot_obj_t * curr_slot;

    if (index > g_slot.slot_number) {
        SLOT_ERR("slot number = %d, slot%d error.\n", g_slot.slot_number, index);
        return -EINVAL;
    }
    curr_slot = &g_slot.slot[index-1];
    if (curr_slot->obj) {
        sysfs_remove_group(&curr_slot->obj->kobj, &slot_attr_group);
        wb_plat_kobject_delete(&curr_slot->obj);
    }

    SLOT_DBG("delete slot%d.\n", index);
    return 0;
}

static int slot_sub_single_create_kobj_and_attrs(struct kobject *parent, unsigned int index)
{
    char name[DIR_NAME_MAX_LEN];
    struct slot_obj_t * curr_slot;

    curr_slot = &g_slot.slot[index-1];
    SLOT_DBG("create slot%d ...\n", index);
    memset(name, 0, sizeof(name));
    snprintf(name, sizeof(name), "%s%d",SLOT_SYSFS_NAME, index);
    curr_slot->obj = wb_plat_kobject_create(name, parent);
    if (!curr_slot->obj) {
        SLOT_ERR("create slot%d object error!\n", index);
        return -EBADRQC;
    }
    curr_slot->obj->index = index;
    if (sysfs_create_group(&curr_slot->obj->kobj, &slot_attr_group) != 0) {
        SLOT_ERR("create slot%d attrs error.\n", index);
        wb_plat_kobject_delete(&curr_slot->obj);
        return -EBADRQC;
    }
    SLOT_DBG("create slot%d ok.\n", index);
    return 0;
}

static int slot_sub_create_kobj_and_attrs(struct kobject *parent, int slot_num)
{
    unsigned int slot_index, i;

    g_slot.slot = kzalloc(sizeof(struct slot_obj_t) * slot_num, GFP_KERNEL);
    if (!g_slot.slot) {
        SLOT_ERR("kzalloc slot.slot error, slot number = %d.\n", slot_num);
        return -ENOMEM;
    }

    for(slot_index = 1; slot_index <= slot_num; slot_index++) {
        if(slot_sub_single_create_kobj_and_attrs(parent, slot_index) != 0 ) {
            goto error;
        }
    }
    return 0;
error:
    for(i = 1; i < slot_index; i++) {
        slot_sub_single_remove_kobj_and_attrs(i);
    }
    if(g_slot.slot) {
        kfree(g_slot.slot);
        g_slot.slot = NULL;
    }
    return -EBADRQC;
}

static int slot_sub_create(void)
{
    int ret, slot_num;

    check_p(g_drv->get_dev_number);
    slot_num = g_drv->get_dev_number(WB_MAIN_DEV_SLOT, WB_MINOR_DEV_NONE);
    if (slot_num < 0) {
        SLOT_ERR("slot number = %d error.\n", slot_num);
        return -EINVAL;
    }
    g_slot.slot_number = slot_num;
    ret = slot_sub_create_kobj_and_attrs(&g_slot_obj->kobj, slot_num);
    return ret;
}

static void slot_sub_remove(void)
{
    unsigned int slot_index;

    if (g_slot.slot) {
       for (slot_index = 1; slot_index <= g_slot.slot_number; slot_index++) {
           if (g_slot.slot[slot_index-1].obj) {
               slot_sub_single_remove_kobj_and_attrs(slot_index);
           }
       }
       kfree(g_slot.slot);
    }
    memset(&g_slot, 0, sizeof(struct slot_t));
    return ;
}

static int slot_root_create(void)
{
    g_slot_obj = wb_plat_kobject_create(SLOT_SYSFS_NAME, NULL);
    if (!g_slot_obj)
        return -ENOMEM;

    if (sysfs_create_group(&g_slot_obj->kobj, &slot_root_attr_group) != 0) {
        wb_plat_kobject_delete(&g_slot_obj);
        SLOT_ERR("create slot dir attrs error!\n");
        return -EBADRQC;
    }
    return 0;

}

static void slot_root_remove(void)
{
    if (g_slot_obj) {
        sysfs_remove_group(&g_slot_obj->kobj, &slot_root_attr_group);
        wb_plat_kobject_delete(&g_slot_obj);
    }

    return ;
}

static int wb_slot_init(void)
{
    int ret;

    SLOT_INFO("wb_slot_init...\n");
    g_drv = dfd_plat_driver_get();
    check_p(g_drv);

    ret = slot_root_create();
    if (ret < 0) {
        goto slot_root_error;
    }

    ret = slot_sub_create();
    if (ret < 0) {
        goto slot_sub_error;
    }
    SLOT_INFO("wb_slot_init ok.\n");
    return 0;
slot_sub_error:
    slot_root_remove();
slot_root_error:
    return ret;
}

static void wb_slot_exit(void)
{
    slot_sub_remove();
    slot_root_remove();
    SLOT_INFO("wb_slot_exit ok.\n");
    return ;
}

module_init(wb_slot_init);
module_exit(wb_slot_exit);
module_param(g_loglevel, int, 0644);
MODULE_PARM_DESC(g_loglevel, "the log level(info=0x1, err=0x2, dbg=0x4).\n");
MODULE_LICENSE("GPL");
MODULE_AUTHOR("support");
MODULE_DESCRIPTION("slot sysfs driver");
