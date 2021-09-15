/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * device attributes handler prototypes for bf watchdog driver
 */

#ifndef __BF_WATCHDOG_API_H__
#define __BF_WATCHDOG_API_H__

ssize_t wdt_show(struct device *dev, struct device_attribute *da,
                            char *buf);
ssize_t wdt_store(struct device *dev, struct device_attribute *da,
                            const char *buf, size_t count);
ssize_t identify_show(struct device *dev, struct device_attribute *da,
                            char *buf);

#endif //__BF_WATCHDOG_API_H__
