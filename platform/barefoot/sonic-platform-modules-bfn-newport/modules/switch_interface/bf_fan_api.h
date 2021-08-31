/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * device attributes handler prototypes for bf fan driver
 */

#ifndef __BF_FAN_API_H__
#define __BF_FAN_API_H__

ssize_t num_fan_show(struct device *dev, struct device_attribute *da,
                            char *buf);
ssize_t num_motor_show(struct device *dev, struct device_attribute *da,
                            char *buf);
ssize_t fan_show(struct device *dev, struct device_attribute *da,
                            char *buf);
ssize_t motor_show(struct device *dev, struct device_attribute *da,
                            char *buf);
ssize_t motor_store(struct device *dev, struct device_attribute *da,
                            const char *buf, size_t count);

#endif //__BF_FAN_API_H__
