/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * Implementation of common module utilities.
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

int kernlevel_to_userlevel(int level){
    if(level >= ARRAY_SIZE(level_map))
        return -EINVAL;
    return level_map[level];
}


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

void unregister_device_and_driver(struct platform_driver *driver,
        struct platform_device devs[], size_t num_dev)
{
    int i;
    for (i = 0 ; i < num_dev ; i++)
        platform_device_unregister(&devs[i]);
    platform_driver_unregister(driver);
}