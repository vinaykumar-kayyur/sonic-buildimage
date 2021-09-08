/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * eeprom driver related data structures and enum
 */

#ifndef __BF_EEPROM_DRIVER_H__
#define __BF_EEPROM_DRIVER_H__

#define BSP_VERSION "0.1.0"
#define EEPROM_SIZE (256) /* only first 256B matter as syseeprom */

enum eeprom_sysfs_attributes
{
    EEPROM_ATTR_ID,
    BSP_VER_ATTR_ID,
    DEBUG_ATTR_ID,
    LOGLEVEL_ATTR_ID,
    EEPROM_MAX_ATTR_ID
};

struct bf_eeprom_drv_data {
    struct kobject *root_kobj;
    int loglevel;
};

#endif //__BF_EEPROM_DRIVER_H__
