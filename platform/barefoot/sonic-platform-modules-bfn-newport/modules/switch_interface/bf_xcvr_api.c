/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * device attribute handler implementation for bf xcvr driver
 */

#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/hwmon-sysfs.h>


ssize_t root_show(struct device *dev, struct device_attribute *da,
                            char *buf)
{
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
    printk("root_show, name(%s) attr_idx=%d\n", da->attr.name, attr->index);
    return 0;
}
ssize_t root_store(struct device *dev, struct device_attribute *da,
                            const char *buf, size_t count)
{
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
    printk("root_store, name(%s) attr_idx=%d\n", da->attr.name, attr->index);
    return count;
}

ssize_t xcvr_show(struct device *dev, struct device_attribute *da,
                            char *buf)
{
    struct platform_device *pdev = to_platform_device(dev);
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
    printk("xcvr_show, id=%d, name(%s) attr_idx=%d\n", pdev->id, da->attr.name, attr->index);
    return 0;
}
ssize_t xcvr_store(struct device *dev, struct device_attribute *da,
                            const char *buf, size_t count)
{
    struct platform_device *pdev = to_platform_device(dev);
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
    printk("xcvr_store, id=%d, name(%s) attr_idx=%d\n", pdev->id, da->attr.name, attr->index);
    return count;
}
