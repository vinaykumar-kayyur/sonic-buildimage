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
#include <linux/ipmi.h>
#include "ipmi_util.h"

/* ----------------------------------------------------------------------------
 * Constant
 * ----------------------------------------------------------------------------
 */
#define _DRIVER_NAME            "sc5630el_sfp"
#define _SFP_EEPROM_PAGE_SIZE   256
#define _SFP_IPMI_MAX_RESP_LEN  64

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
 * Mapping of SFP index and I2C address
 * ----------------------------------------------------------------------------
 */
#if 1 /* Case of continuous I2C addresses */

#define _SFP_COUNT          32
#define _I2C_START_ADDR     0x30

/*
    >= 0 : SFP index
    -1   : failed
*/
static int _index_lookup_by_addr(
    int     i2c_addr
)
{
    if (i2c_addr < _I2C_START_ADDR || i2c_addr >= (_I2C_START_ADDR + _SFP_COUNT)) {
        _DEBMSG("Exit, invalid i2c_addr %d", i2c_addr);
        return -1;
    }

    return i2c_addr - _I2C_START_ADDR;
}

#else /* Case of dis-continuous I2C addresses */

typedef struct
{
    int     index;
    int     i2c_addr;
} index_table_t;

index_table_t   _mapping[] = {
    {  0, 0x30},
    {  1, 0x31},
    {  2, 0x32},
    {  3, 0x33},
    {  4, 0x34},
    {  5, 0x35},
    {  6, 0x36},
    {  7, 0x37},
    {  8, 0x38},
    {  9, 0x39},
    { 10, 0x3a},
    { 11, 0x3b},
    { 12, 0x3c},
    { 13, 0x3d},
    { 14, 0x3e},
    { 15, 0x3f},
    { 16, 0x40},
    { 17, 0x41},
    { 18, 0x42},
    { 19, 0x43},
    { 20, 0x44},
    { 21, 0x45},
    { 22, 0x46},
    { 23, 0x47},
    { 24, 0x48},
    { 25, 0x49},
    { 26, 0x4a},
    { 27, 0x4b},
    { 28, 0x4c},
    { 29, 0x4d},
    { 30, 0x4e},
    { 31, 0x4f},
    { -1,   -1}
};

/*
    >= 0 : SFP index
    -1   : failed
*/
static int _index_lookup_by_addr(
    int     i2c_addr
)
{
    int     i = 0;

    while (_mapping[i].index >= 0) {
        if (_mapping[i].i2c_addr == i2c_addr) {
            // found
            return _mapping[i].index;
        }

        // next index
        ++i;
    }

    // not found
    return -1;
}

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
#define _CMD_COUNT_GET      0x40
#define _CMD_PRESENT_GET    0x41
#define _CMD_LPM_GET        0x42
#define _CMD_LPM_SET        0x43
#define _CMD_RESET          0x44
#define _CMD_EEPROM_GET     0x45

/* ----------------------------------------------------------------------------
 * Sysfs hooks function for read operation
 * ----------------------------------------------------------------------------
 */
static ssize_t _cb_count_get(
    struct device               *dev,
    struct device_attribute     *devattr,
    char                        *buf
)
{
    int                 rc;
    struct i2c_client   *client = to_i2c_client(dev);
    int                 result_len = _SFP_IPMI_MAX_RESP_LEN;

    _DEBMSG("Enter, i2c_addr = 0x%x", client->addr);

    rc = ipmi_cmd(_NETFN, _CMD_COUNT_GET, NULL, 0, buf, &result_len);
    if (rc) {
        _DEBMSG("Exit, Invalid IPMI result, rc=%d", rc);
        return 0;
    } else if (result_len != 1) {
        _DEBMSG("Exit, unexpected IPMI response length(Expected length 1) %d", result_len);
        return 0;
    }

    _DEBMSG("Exit");
    return sprintf(buf, "%d\n", buf[0]);
}

static ssize_t _cb_eeprom_get(
    struct device               *dev,
    struct device_attribute     *devattr,
    char                        *buf
)
{
    int                 rc;
    struct i2c_client   *client = to_i2c_client(dev);
    int                 sfp_index = _index_lookup_by_addr(client->addr);
    int                 ipmi_resp_len, total_ipmi_resp_len;
    char                raw_data[4];

    _DEBMSG("Enter, sfp_index = %d, i2c_addr = 0x%x", sfp_index, client->addr);

    if (sfp_index < 0) {
        _DEBMSG("Exit, Failed to lookup I2C address, sfp_index = %d, i2c_addr = 0x%x", sfp_index, client->addr);
        return 0;
    }

    for (total_ipmi_resp_len = 0; total_ipmi_resp_len < _SFP_EEPROM_PAGE_SIZE; total_ipmi_resp_len += _SFP_IPMI_MAX_RESP_LEN) {
        raw_data[0] = (char) sfp_index;         // SFP index
        raw_data[1] = 0;                        // page index
        raw_data[2] = total_ipmi_resp_len;      // start offset
        raw_data[3] = _SFP_IPMI_MAX_RESP_LEN;   // read length

        /* Execute IPMI command to get EERPOM data */
        ipmi_resp_len = _SFP_IPMI_MAX_RESP_LEN;
        rc = ipmi_cmd(_NETFN, _CMD_EEPROM_GET, raw_data, sizeof(raw_data), buf + total_ipmi_resp_len, &ipmi_resp_len);
        if (rc) {
             /* It is the expected result when the SFP module is not present. */
            _DEBMSG("Exit, Invalid IPMI result, rc=%d, total_ipmi_resp_len=%d, sfp_index = %d", rc, total_ipmi_resp_len, sfp_index);
            return 0;
        } else if (ipmi_resp_len != _SFP_IPMI_MAX_RESP_LEN) {
            _DEBMSG("Exit, Invalid IPMI response length %d (Expected %d), sfp_index = %d", ipmi_resp_len, _SFP_IPMI_MAX_RESP_LEN, sfp_index);
            return 0;
        }
    }

    _DEBMSG("Exit");
    return total_ipmi_resp_len;
}

static ssize_t _cb_lpm_get(
    struct device               *dev,
    struct device_attribute     *devattr,
    char                        *buf
)
{
    int                 rc;
    struct i2c_client   *client = to_i2c_client(dev);
    int                 sfp_index = _index_lookup_by_addr(client->addr);
    char                data[1];
    int                 data_len;
    int                 result_len = _SFP_IPMI_MAX_RESP_LEN;

    _DEBMSG("Enter, sfp_index = %d, i2c_addr = 0x%x", sfp_index, client->addr);

    if (sfp_index < 0) {
        _DEBMSG("Exit, Failed to lookup I2C address, sfp_index = %d, i2c_addr = 0x%x", sfp_index, client->addr);
        return 0;
    }

    /* Execute IPMI command to get response data */
    data[0]  = (char) sfp_index; // SFP index
    data_len = 1;
    rc = ipmi_cmd(_NETFN, _CMD_LPM_GET, data, data_len, buf, &result_len);
    if (rc) {
        _DEBMSG("Exit, Invalid IPMI result, rc=%d, sfp_index = %d", rc, sfp_index);
        return 0;
    } else if (result_len != 1) {
        _DEBMSG("Exit, unexpected IPMI response length(Expected length 1) %d, sfp_index = %d", result_len, sfp_index);
        return 0;
    }

    _DEBMSG("Exit");
    return sprintf(buf, "%d\n", buf[0]);
}

static ssize_t _cb_lpm_set(
    struct device           *dev,
    struct device_attribute *devattr,
    const char              *buf,
    size_t                  count
)
{
    int                 rc;
    struct i2c_client   *client = to_i2c_client(dev);
    int                 sfp_index = _index_lookup_by_addr(client->addr);
    char                data[2];
    int                 data_len;

    _DEBMSG("Enter, sfp_index = %d, i2c_addr = 0x%x", sfp_index, client->addr);

    if (sfp_index < 0) {
        _DEBMSG("Exit, Failed to lookup I2C address, sfp_index = %d, i2c_addr = 0x%x", sfp_index, client->addr);
        return count;
    }

    /* Execute IPMI command to get response data */
    data[0]  = (char) sfp_index;    // SFP index
    data[1]  = (data_len == 4) ? 0x1 : 0x0; // 'False' ¡V disable low power mode, 'True' ¡V enable low power mode
    data_len = 2;
    rc = ipmi_cmd(_NETFN, _CMD_LPM_SET, data, data_len, NULL, NULL);
    if (rc) {
        _DEBMSG("Exit, Invalid IPMI result, rc=%d, sfp_index = %d", rc, sfp_index);
        return count;
    }

    //
    //  return count.
    //  Otherwise, it will send till the count is satisfied
    //
    _DEBMSG("Exit");
    return count;
}

static ssize_t _cb_present_get(
    struct device               *dev,
    struct device_attribute     *devattr,
    char                        *buf
)
{
    int                 rc;
    struct i2c_client   *client = to_i2c_client(dev);
    int                 sfp_index = _index_lookup_by_addr(client->addr);
    char                data[1];
    int                 data_len;
    int                 result_len = _SFP_IPMI_MAX_RESP_LEN;

    _DEBMSG("Enter, sfp_index = %d, i2c_addr = 0x%x", sfp_index, client->addr);

    if (sfp_index < 0) {
        _DEBMSG("Exit, Failed to lookup I2C address, sfp_index = %d, i2c_addr = 0x%x", sfp_index, client->addr);
        return 0;
    }

    /* Execute IPMI command to get response data */
    data[0]  = (char) sfp_index; // SFP index
    data_len = 1;
    rc = ipmi_cmd(_NETFN, _CMD_PRESENT_GET, data, data_len, buf, &result_len);
    if (rc) {
        _DEBMSG("Exit, Invalid IPMI result, rc=%d, sfp_index = %d", rc, sfp_index);
        return 0;
    } else if (result_len != 1) {
        _DEBMSG("Exit, unexpected IPMI response length(Expected length 1) %d, sfp_index = %d", result_len, sfp_index);
        return 0;
    }

    _DEBMSG("Exit");
    return sprintf(buf, "%d\n", buf[0]);
}

static ssize_t _cb_reset_set(
    struct device           *dev,
    struct device_attribute *devattr,
    const char              *buf,
    size_t                  count
)
{
    int                 rc;
    struct i2c_client   *client = to_i2c_client(dev);
    int                 sfp_index = _index_lookup_by_addr(client->addr);
    char                data[1];
    int                 data_len;

    _DEBMSG("Enter, sfp_index = %d, i2c_addr = 0x%x", sfp_index, client->addr);

    if (sfp_index < 0) {
        _DEBMSG("Exit, Failed to lookup I2C address, sfp_index = %d, i2c_addr = 0x%x", sfp_index, client->addr);
        return count;
    }

    /* Execute IPMI command to get response data */
    data[0]  = (char) sfp_index; // SFP index
    data_len = 1;
    rc = ipmi_cmd(_NETFN, _CMD_RESET, data, data_len, NULL, NULL);
    if (rc) {
        _DEBMSG("Exit, Invalid IPMI result, rc=%d, sfp_index = %d", rc, sfp_index);
        return count;
    }

    //
    //  return count.
    //  Otherwise, it will send till the count is satisfied
    //
    _DEBMSG("Exit");
    return count;
}

/* ------------------------------------------------------------------------------
 * Register sysfs/i2c
 * ----------------------------------------------------------------------------
 */
static DEVICE_ATTR(sfp_count,   S_IRUGO,           _cb_count_get,   NULL);
static DEVICE_ATTR(sfp_eeprom,  S_IRUGO,           _cb_eeprom_get,  NULL);
static DEVICE_ATTR(sfp_lpm,     S_IRUGO | S_IWUSR, _cb_lpm_get,     _cb_lpm_set);
static DEVICE_ATTR(sfp_present, S_IRUGO,           _cb_present_get, NULL);
static DEVICE_ATTR(sfp_reset,   S_IWUSR,           NULL,            _cb_reset_set);

static struct attribute         *_i2c_sfp_attr[] = {
    &dev_attr_sfp_count.attr,
    &dev_attr_sfp_eeprom.attr,
    &dev_attr_sfp_lpm.attr,
    &dev_attr_sfp_present.attr,
    &dev_attr_sfp_reset.attr,
    NULL
};

static const struct attribute_group _i2c_sfp_attr_grp = {
    .attrs = _i2c_sfp_attr,
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
    rc = sysfs_create_group(&client->dev.kobj, &_i2c_sfp_attr_grp);
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

    sysfs_remove_group(&client->dev.kobj, &_i2c_sfp_attr_grp);

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

MODULE_AUTHOR("switchsupport@inspur.com");
MODULE_DESCRIPTION ("SONiC SFP platform driver for SC5630EL ");
MODULE_LICENSE("GPL");
