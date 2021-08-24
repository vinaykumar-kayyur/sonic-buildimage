/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * device attributes handler prototypes for bf eeprom driver
 */

#ifndef __BF_EEPROM_API_H__
#define __BF_EEPROM_API_H__

ssize_t eeprom_show(struct device *dev, struct device_attribute *da,
                            char *buf);

#endif //__BF_EEPROM_API_H__
