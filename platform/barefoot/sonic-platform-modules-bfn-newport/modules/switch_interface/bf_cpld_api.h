/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * device attributes handler prototypes for bf cpld driver
 */

#ifndef __BF_CPLD_API_H__
#define __BF_CPLD_API_H__

ssize_t devnum_show(struct device *dev, struct device_attribute *da,
                            char *buf);
ssize_t num_temp_show(struct device *dev, struct device_attribute *da,
                            char *buf);
ssize_t cpld_show(struct device *dev, struct device_attribute *da,
                            char *buf);
ssize_t reset_show(struct device *dev, struct device_attribute *da,
                            char *buf);
ssize_t reset_store(struct device *dev, struct device_attribute *da,
                            const char *buf, size_t count);
struct bf_cpld_drv_data *update_cpld_status(unsigned char p_id);

#endif //__BF_CPLD_API_H__
