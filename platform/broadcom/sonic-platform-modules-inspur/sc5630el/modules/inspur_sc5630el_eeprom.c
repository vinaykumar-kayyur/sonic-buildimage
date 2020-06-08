/*
 * Copyright (C) 2018 Inspur Electronic Information Industry Co.,Ltd
 *
 * Licensed under the GNU General Public License Version 2
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 */

/* ----------------------------------------------------------------------------
 * Include files
 * ----------------------------------------------------------------------------
 */
#include <linux/module.h>   // included for all kernel modules
#include <linux/kernel.h>   // included for KERN_INFO
#include <linux/init.h>     // included for __init and __exit macros
#include <linux/i2c.h>      // For I2C_CLIENT_END
#include <linux/err.h>
#include <linux/slab.h>
#include <linux/list.h>
#include "ipmi_util.h"

/* ----------------------------------------------------------------------------
 * Constant
 * ----------------------------------------------------------------------------
 */
#define _DRIVER_NAME                "sc5630el_eeprom"
#define _EEPROM_SIZE                256
#define _EEPROMP_IPMI_MAX_RESP_LEN  64

/* ----------------------------------------------------------------------------
 * Local debug
 * ----------------------------------------------------------------------------
 */
#define _LOCAL_DEBUG
#ifdef _LOCAL_DEBUG
#define _DEBMSG(fmt, args...)   \
		 printk(KERN_INFO "[%s/%s()#%d]: " fmt "\r\n", __FILE__, __FUNCTION__, __LINE__, ##args)
#else
#define _DEBMSG(fmt, args...)
#endif

/* ----------------------------------------------------------------------------
 * IPMI functions
 * ----------------------------------------------------------------------------
 */
//
//  IPMI NetFn code
//
#define _NETFN              0x3c

//
//  IPMI command code
//
#define _CMD_EEPROM_GET     0x00

/* ----------------------------------------------------------------------------
 * Sysfs hooks function for read operation
 * ----------------------------------------------------------------------------
 */
static ssize_t _cb_eeprom_get(
    struct device               *dev,
    struct device_attribute     *devattr,
    char                        *buf
)
{
    int                 rc;
    struct i2c_client   *client = to_i2c_client(dev);
    int                 ipmi_resp_len, total_ipmi_resp_len;
    char                raw_data[2];

    _DEBMSG("Enter, i2c_addr = 0x%x", client->addr);

    for (total_ipmi_resp_len = 0; total_ipmi_resp_len < _EEPROM_SIZE; total_ipmi_resp_len += _EEPROMP_IPMI_MAX_RESP_LEN) {
        raw_data[0] = total_ipmi_resp_len;          // start offset
        raw_data[1] = _EEPROMP_IPMI_MAX_RESP_LEN;   // read length

        /* Execute IPMI command to get EERPOM data */
        ipmi_resp_len = _EEPROMP_IPMI_MAX_RESP_LEN;
        rc = ipmi_cmd(_NETFN, _CMD_EEPROM_GET, raw_data, sizeof(raw_data), buf + total_ipmi_resp_len, &ipmi_resp_len);
        if (rc) {
            _DEBMSG("Exit, Invalid IPMI result, rc=%d, total_ipmi_resp_len=%d", rc, total_ipmi_resp_len);
            return 0;
        } else if (ipmi_resp_len != _EEPROMP_IPMI_MAX_RESP_LEN) {
            _DEBMSG("Exit, Invalid IPMI response length %d (Expected %d)", ipmi_resp_len, _EEPROMP_IPMI_MAX_RESP_LEN);
            return 0;
        }
    }

    _DEBMSG("Exit");
    return total_ipmi_resp_len;
}

/* ------------------------------------------------------------------------------
 * Register sysfs/i2c
 * ----------------------------------------------------------------------------
 */
static DEVICE_ATTR(cpu_eeprom, S_IRUGO, _cb_eeprom_get, NULL);

static struct attribute *_i2c_eeprom_attr[] = {
    &dev_attr_cpu_eeprom.attr,
    NULL
};

static const struct attribute_group _i2c_eeprom_attr_grp = {
    .attrs = _i2c_eeprom_attr,
};

/* ----------------------------------------------------------------------------
 * Module probe/remove functions
 * ----------------------------------------------------------------------------
 */
/* Probe I2C driver */
static int _i2c_driver_probe(
    struct i2c_client           *client,
    const struct i2c_device_id  *dev_id
)
{
    int rc;

    _DEBMSG("Enter, i2c_addr = 0x%x", client->addr);

    rc = i2c_check_functionality(client->adapter, I2C_FUNC_SMBUS_BYTE_DATA);
    if (rc == 0) {
        _DEBMSG("Exit, failed on I2C address = 0x%x", client->addr);
        return -EIO;
    }

    dev_info(&client->dev, "chip found - New\n");

    /* Register sysfs hooks */
    rc = sysfs_create_group(&client->dev.kobj, &_i2c_eeprom_attr_grp);
    if (rc) {
        _DEBMSG("Exit, failed to create sysfs, rc = 0x%x", rc);
        return rc;
    }

    _DEBMSG("Exit");
    return 0;
}

/* Remove I2C driver */
static int _i2c_driver_remove(
    struct i2c_client   *client
)
{
    _DEBMSG("Enter");

    sysfs_remove_group(&client->dev.kobj, &_i2c_eeprom_attr_grp);

    _DEBMSG("Exit");
    return 0;
}

/* ----------------------------------------------------------------------------
 * Module main functions
 * ----------------------------------------------------------------------------
 */
static const struct i2c_device_id _i2c_driver_id[] = {
    {_DRIVER_NAME, 0 },
    {}
};
MODULE_DEVICE_TABLE(i2c, _i2c_driver_id);

static struct i2c_driver _i2c_device_driver = {
    .driver = {
        .name     = _DRIVER_NAME,
    },
    .probe        = _i2c_driver_probe,
    .remove       = _i2c_driver_remove,
    .id_table     = _i2c_driver_id,
};

module_i2c_driver(_i2c_device_driver);   // Simply module_init() & module_exit()

MODULE_AUTHOR("sdn@inspur.com");
MODULE_DESCRIPTION ("SONiC EEPROM driver via ipmi");
MODULE_LICENSE("GPL");
