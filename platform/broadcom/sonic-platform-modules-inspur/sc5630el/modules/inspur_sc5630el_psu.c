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
#include <linux/jiffies.h>
#include <linux/hwmon.h>
#include <linux/hwmon-sysfs.h>
#include <linux/mutex.h>
#include <linux/ipmi.h>
#include "ipmi_util.h"

/* ----------------------------------------------------------------------------
 * Constant
 * ----------------------------------------------------------------------------
 */
#define _DRIVER_NAME    "inspur_sc5630el_psu"

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
/* PSU IPMI definition */
#define _PSU_IPMI_PSUID_BASE                1       // PSU IPMI base PSU ID (used for zero-based)

#define _PSU_IPMI_REQ_NETFN                 0x3c    // PSU IPMI request netfun code
#define _PSU_IPMI_REQ_CMD_STATUS            0x29    // PSU IPMI request command code for PSU status
#define _PSU_IPMI_REQ_PSUID_OFFSET          1       // The offset of PSU ID in IPMI request

#define _PSU_IPMI_RESP_MAX_OFFSET(a, b)     (((a) > (b)) ? (a) : (b))
#define _PSU_IPMI_RESP_PSUID_OFFSET         0       // The offset of PSU ID in IPMI response
#define _PSU_IPMI_RESP_PRESENT_OFFSET       1       // The offset of PSU present in IPMI response
#define _PSU_IPMI_RESP_OUT_VOLT_LB_OFFSET   14      // The offset of PSU output voltage in IPMI response (high byte)
#define _PSU_IPMI_RESP_OUT_VOLT_HB_OFFSET   13      // The offset of PSU output voltage in IPMI response (low byte)
#define _PSU_IPMI_RESP_OUT_VOLT_OFFSET      _PSU_IPMI_RESP_MAX_OFFSET(_PSU_IPMI_RESP_OUT_VOLT_LB_OFFSET, _PSU_IPMI_RESP_OUT_VOLT_HB_OFFSET)

/* Get PSU status via IPMI command */
bool ipmi_psu_status_get(u8 psu_id, char *ipmi_resp, int *ipmi_resp_len)
{
    int rc;
    char raw_data[_PSU_IPMI_REQ_PSUID_OFFSET] = {psu_id - _PSU_IPMI_PSUID_BASE};

    _DEBMSG("Enter");

    /* Execute IPMI command to get PSU status */
    rc = ipmi_cmd(_PSU_IPMI_REQ_NETFN, _PSU_IPMI_REQ_CMD_STATUS,
                      raw_data, sizeof(raw_data),
                      ipmi_resp, ipmi_resp_len);
    if (rc) {
       _DEBMSG("Exit, ipmi result rc=%d", rc);
       return false;
    }

    /* Return true when operation successfully and IPMI response correctly
     * Otherwise, false.
     */
    _DEBMSG("Exit");
    return ((*ipmi_resp_len != 0) &&
            ipmi_resp[_PSU_IPMI_RESP_PSUID_OFFSET] == (psu_id - _PSU_IPMI_PSUID_BASE) &&
            ipmi_resp[_PSU_IPMI_RESP_PRESENT_OFFSET])
            ? true : false;
}

/* ----------------------------------------------------------------------------
 * PSU device attributes
 * ----------------------------------------------------------------------------
 */
/* PSU device attributes index */
enum inspur_sc5630el_psu_attr_idx_e {
    DEV_ATTR_IDX_PSU_PRESENT_E,
    DEV_ATTR_IDX_PSU_VOLTAGE_E
};

/* The data structure of PSU device private data */
typedef struct inspur_sc5630el_psu_data_s {
    struct device   *hwmon_dev;
    u8              psu_id;     /* PSU ID (one-based) */
    struct mutex    mutex;
} inspur_sc5630el_psu_data_t;

/* ----------------------------------------------------------------------------
 * Sysfs hooks function for read operation
 * ----------------------------------------------------------------------------
 */
static ssize_t _sysfs_read_psu_status(
    struct device               *dev,
    struct device_attribute     *dev_attr,
    char                        *buf
)
{
    int status_val = 0;
    struct sensor_device_attribute *attr = to_sensor_dev_attr(dev_attr);
    struct i2c_client *client = to_i2c_client(dev);
    inspur_sc5630el_psu_data_t *psu_data = i2c_get_clientdata(client);
    char ipmi_resp[IPMI_MAX_MSG_LENGTH];
    int ipmi_resp_len = 0;

    _DEBMSG("Enter, attr->index = %d, psu_data->psu_id = %d", attr->index, psu_data->psu_id);
    mutex_lock(&psu_data->mutex);

    if (ipmi_psu_status_get(psu_data->psu_id, ipmi_resp, &ipmi_resp_len)) {
        if (attr->index == DEV_ATTR_IDX_PSU_PRESENT_E) {
            status_val = (ipmi_resp_len > _PSU_IPMI_RESP_PRESENT_OFFSET) ? ipmi_resp[_PSU_IPMI_RESP_PRESENT_OFFSET] : 0;
        } else if (attr->index == DEV_ATTR_IDX_PSU_VOLTAGE_E) {
            status_val = (ipmi_resp_len > _PSU_IPMI_RESP_OUT_VOLT_OFFSET) ? ((ipmi_resp[_PSU_IPMI_RESP_OUT_VOLT_HB_OFFSET] << 8) + ipmi_resp[_PSU_IPMI_RESP_OUT_VOLT_LB_OFFSET]) : 0;
        } else {
            _DEBMSG("Failed when calling psu_status_get(): Unknown PSU attr->index = %d", attr->index);
        }
    }

    mutex_unlock(&psu_data->mutex);
    _DEBMSG("Exit");
    return sprintf(buf, "%d\n", status_val);
}

static SENSOR_DEVICE_ATTR(psu_present, S_IRUGO, _sysfs_read_psu_status, NULL, DEV_ATTR_IDX_PSU_PRESENT_E);
static SENSOR_DEVICE_ATTR(psu_voltage, S_IRUGO, _sysfs_read_psu_status, NULL, DEV_ATTR_IDX_PSU_VOLTAGE_E);

static struct attribute *_inspur_sc5630el_psu_attributes[] = {
    &sensor_dev_attr_psu_present.dev_attr.attr,
    &sensor_dev_attr_psu_voltage.dev_attr.attr,
    NULL
};

static const struct attribute_group _inspur_sc5630el_psu_group = {
    .attrs = _inspur_sc5630el_psu_attributes,
};

/* ----------------------------------------------------------------------------
 * Module probe/remove functions
 * ----------------------------------------------------------------------------
 */
/* Probe I2C driver */
static int _inspur_sc5630el_psu_probe(
    struct i2c_client           *client,
    const struct i2c_device_id  *dev_id
)
{
    int rc;
    inspur_sc5630el_psu_data_t *psu_data;

    _DEBMSG("Enter");

    rc = i2c_check_functionality(client->adapter, I2C_FUNC_SMBUS_I2C_BLOCK);
    if (rc == 0) {
        _DEBMSG("Exit, failed on I2C address = 0x%x", client->addr);
        return -EIO;
    }

    psu_data = kzalloc(sizeof(*psu_data), GFP_KERNEL);
    if (!psu_data) {
        _DEBMSG("Exit, failed to allocated memory");
        return -ENOMEM;
    }

    i2c_set_clientdata(client, psu_data);
    psu_data->psu_id = dev_id->driver_data;
    mutex_init(&psu_data->mutex);

    /* Register sysfs hooks */
    rc = sysfs_create_group(&client->dev.kobj, &_inspur_sc5630el_psu_group);
    if (rc) {
        _DEBMSG("Exit, failed to create sysfs, rc = 0x%x", rc);
        kfree(psu_data);
        return rc;
    }

#if 0 /* hwmon_device_register() is deprecated. Please convert the driver to use hwmon_device_register_with_info() */
    data->hwmon_dev = hwmon_device_register(&client->dev);
#else
    /* hwmon_device_register_with_info() parameter reference
    struct device *hwmon_device_register_with_info(struct device *dev,
                                    const char *name, void *drvdata,
                                    const struct hwmon_chip_info *info,
                                    const struct attribute_group **extra_groups);
    */
    psu_data->hwmon_dev = hwmon_device_register_with_info(&client->dev,
                                                          _DRIVER_NAME,
                                                          NULL,
                                                          NULL,
                                                          NULL);
#endif

    rc = IS_ERR(psu_data->hwmon_dev);
    if (rc) {
        _DEBMSG("Exit, hwmon_dev error, rc = 0x%x", rc);
        sysfs_remove_group(&client->dev.kobj, &_inspur_sc5630el_psu_group);
        return PTR_ERR(psu_data->hwmon_dev);
    }

    _DEBMSG("Exit");
    return rc;
}

/* Remove I2C driver */
static int _inspur_sc5630el_psu_remove(
    struct i2c_client   *client
)
{
    inspur_sc5630el_psu_data_t *psu_data = i2c_get_clientdata(client);

    _DEBMSG("Enter");

    hwmon_device_unregister(psu_data->hwmon_dev);
    sysfs_remove_group(&client->dev.kobj, &_inspur_sc5630el_psu_group);
    if (psu_data) {
        kfree(psu_data);
    }

    _DEBMSG("Exit");
    return 0;
}

/* ----------------------------------------------------------------------------
 * Module main functions
 * ----------------------------------------------------------------------------
 */
/* PSU ID (one-based) */
enum inspur_sc5630el_psu_id_e {
    INSPUR_SC5630EL_PSU_ID_1_E = 1,
    INSPUR_SC5630EL_PSU_ID_2_E
};

/* I2C address lists */
static const unsigned short _inspur_sc5630el_psu_i2c_addr[] = { 0x20, 0x21, I2C_CLIENT_END };

static const struct i2c_device_id _inspur_sc5630el_psu_id[] = {
    { "insp_sc5630el_psu1", INSPUR_SC5630EL_PSU_ID_1_E },
    { "insp_sc5630el_psu2", INSPUR_SC5630EL_PSU_ID_2_E },
    {}
};
MODULE_DEVICE_TABLE(i2c, _inspur_sc5630el_psu_id);

static struct i2c_driver _inspur_sc5630el_psu = {
    .class        = I2C_CLASS_HWMON,
    .driver = {
        .name     = _DRIVER_NAME,
    },
    .probe        = _inspur_sc5630el_psu_probe,
    .remove       = _inspur_sc5630el_psu_remove,
    .id_table     = _inspur_sc5630el_psu_id,
    .address_list = _inspur_sc5630el_psu_i2c_addr,
};

module_i2c_driver(_inspur_sc5630el_psu);   // Simply module_init() & module_exit()

MODULE_AUTHOR("switchsupport@inspur.com");
MODULE_DESCRIPTION ("SONiC PSU platform driver for SC5630EL ");
MODULE_LICENSE("GPL");
