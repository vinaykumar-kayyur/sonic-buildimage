/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * device attributes handler prototypes for bf psu driver
 */

#ifndef __BF_PSU_API_H__
#define __BF_PSU_API_H__

ssize_t devnum_show(struct device *dev, struct device_attribute *da,
                            char *buf);
ssize_t num_temp_show(struct device *dev, struct device_attribute *da,
                            char *buf);
ssize_t psu_show(struct device *dev, struct device_attribute *da,
                            char *buf);
ssize_t temp_show(struct device *dev, struct device_attribute *da,
                            char *buf);

#endif //__BF_PSU_API_H__
