/*
 * system_device_driver.c
 *
 * This module realize /sys/s3ip/system attributes read and write functions
 *
 * History
 *  [Version]                [Date]                    [Description]
 *   *  v1.0                2021-08-31                  S3IP sysfs
 */

#include <linux/slab.h>

#include "./include/device_driver_common.h"
#include "../sysfs_driver/include/system_sysfs.h"
#include "../switch_driver/include/dfd_sysfs_common.h"

#define TEMP_SENSOR_INFO(fmt, args...) LOG_INFO("system: ", fmt, ##args)
#define TEMP_SENSOR_ERR(fmt, args...)  LOG_ERR("system: ", fmt, ##args)
#define TEMP_SENSOR_DBG(fmt, args...)  LOG_DBG("system: ", fmt, ##args)

static int g_loglevel = 0;
static struct switch_drivers_s *g_drv = NULL;

static ssize_t wb_set_system_value(unsigned int type,  int value)
{
    ssize_t ret;

    check_p(g_drv);
    check_p(g_drv->set_system_value);

    ret = g_drv->set_system_value(type, value);
    return ret;
}

static ssize_t wb_get_system_value(unsigned int type, int *value)
{
    ssize_t ret;

    check_p(g_drv);
    check_p(g_drv->get_system_value);

    ret = g_drv->get_system_value(type, value);
    return ret;
}
/***********************************end of main board temp*************************************/

static struct s3ip_sysfs_system_drivers_s drivers = {
    /*
     * set ODM system drivers to /sys/s3ip/system,
     * if not support the function, set corresponding hook to NULL.
     */
    .get_system_value = wb_get_system_value,
    .set_system_value = wb_set_system_value,
};

static int __init system_dev_drv_init(void)
{
    int ret;

    TEMP_SENSOR_INFO("system_init...\n");
    g_drv = s3ip_switch_driver_get();
    check_p(g_drv);

    ret = s3ip_sysfs_system_drivers_register(&drivers);
    if (ret < 0) {
        TEMP_SENSOR_ERR("temp sensor drivers register err, ret %d.\n", ret);
        return ret;
    }
    TEMP_SENSOR_INFO("system_init success.\n");
    return 0;
}

static void __exit system_dev_drv_exit(void)
{
    s3ip_sysfs_system_drivers_unregister();
    TEMP_SENSOR_INFO("system_exit success.\n");
    return;
}

module_init(system_dev_drv_init);
module_exit(system_dev_drv_exit);
module_param(g_loglevel, int, 0644);
MODULE_PARM_DESC(g_loglevel, "the log level(info=0x1, err=0x2, dbg=0x4, all=0xf).\n");
MODULE_LICENSE("GPL");
MODULE_AUTHOR("sonic S3IP sysfs");
MODULE_DESCRIPTION("system device driver");
