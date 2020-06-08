/*
 * Inspur Generic PMBUS driver
 *
 *
 * Based on pmbus_core driver and ltc2978 driver
 *
 * History:
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
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
 */

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/init.h>
#include <linux/err.h>
#include <linux/slab.h>
#include <linux/i2c.h>
#include <linux/delay.h>
#include <linux/pmbus.h>
#include "pmbus.h"  /* FIXME :based on pmbus_core need pmbus definition, but it would
                                              need to migrated when different version of kernel */


enum id_name {
	ps2551
};


static int pmbus_read_block(struct i2c_client *client, u8 command, int data_len, u8 *data)
{
    int result = 0;
    int retry_count = 3;

    while (retry_count) {
        retry_count--;

        result = i2c_smbus_read_i2c_block_data(client, command, data_len, data);

        if (result < 0) {
            msleep(10);
            continue;
        }

        result = 0;
        break;
    }

    return result;
}

static ssize_t pmbus_show_mfr_id(struct device *dev,
                struct device_attribute *da, char *buf)
{
    int ret, len;
    u8 block_buffer[I2C_SMBUS_BLOCK_MAX + 1], *str;
    struct i2c_client *client = container_of(dev, struct i2c_client, dev);

    ret = pmbus_read_block(client, PMBUS_MFR_ID, I2C_SMBUS_BLOCK_MAX, block_buffer);
    if (ret < 0) {
        dev_err(&client->dev, "Failed to read Manufacturer ID\n");
        return ret;
    }
    len = block_buffer[0];
    block_buffer[(len+1)] = '\0';
    str = &(block_buffer[1]);

    return snprintf(buf, PAGE_SIZE, "%s\n", str);
}

static ssize_t pmbus_show_mfr_model(struct device *dev,
                struct device_attribute *da, char *buf)
{
    int ret, len;
    u8 block_buffer[I2C_SMBUS_BLOCK_MAX + 1], *str;
    struct i2c_client *client = container_of(dev, struct i2c_client, dev);

    ret = pmbus_read_block(client, PMBUS_MFR_MODEL, I2C_SMBUS_BLOCK_MAX, block_buffer);
    if (ret < 0) {
        dev_err(&client->dev, "Failed to read Manufacturer Model\n");
        return ret;
    }
    len = block_buffer[0];
    block_buffer[(len+1)] = '\0';
    str = &(block_buffer[1]);

    return snprintf(buf, PAGE_SIZE, "%s\n", str);
}

static ssize_t pmbus_show_mfr_revision(struct device *dev,
                struct device_attribute *da, char *buf)
{
    int ret, len;
    u8 block_buffer[I2C_SMBUS_BLOCK_MAX + 1], *str;
    struct i2c_client *client = container_of(dev, struct i2c_client, dev);

    ret = pmbus_read_block(client, PMBUS_MFR_REVISION, I2C_SMBUS_BLOCK_MAX, block_buffer);
    if (ret < 0) {
        dev_err(&client->dev, "Failed to read Manufacturer Revision\n");
        return ret;
    }
    len = block_buffer[0];
    block_buffer[(len+1)] = '\0';
    str = &(block_buffer[1]);

    return snprintf(buf, PAGE_SIZE, "%s\n", str);
}

static ssize_t pmbus_show_mfr_location(struct device *dev,
                struct device_attribute *da, char *buf)
{
    int ret, len;
    u8 block_buffer[I2C_SMBUS_BLOCK_MAX + 1], *str;
    struct i2c_client *client = container_of(dev, struct i2c_client, dev);

    ret = pmbus_read_block(client, PMBUS_MFR_LOCATION, I2C_SMBUS_BLOCK_MAX, block_buffer);
    if (ret < 0) {
        dev_err(&client->dev, "Failed to read Manufacture Location\n");
        return ret;
    }
    len = block_buffer[0];
    block_buffer[(len+1)] = '\0';
    str = &(block_buffer[1]);

    return snprintf(buf, PAGE_SIZE, "%s\n", str);
}

static ssize_t pmbus_show_mfr_serial(struct device *dev,
                struct device_attribute *da, char *buf)
{
    int ret, len;
    u8 block_buffer[I2C_SMBUS_BLOCK_MAX + 1], *str;
    struct i2c_client *client = container_of(dev, struct i2c_client, dev);

    ret = pmbus_read_block(client, PMBUS_MFR_SERIAL, I2C_SMBUS_BLOCK_MAX, block_buffer);
    if (ret < 0) {
        dev_err(&client->dev, "Failed to read Manufacturer Serial\n");
        return ret;
    }
    len = block_buffer[0];
    block_buffer[(len+1)] = '\0';
    str = &(block_buffer[1]);

    return snprintf(buf, PAGE_SIZE, "%s\n", str);
}


static DEVICE_ATTR(mfr_id, S_IRUGO, pmbus_show_mfr_id, NULL);
static DEVICE_ATTR(mfr_model, S_IRUGO, pmbus_show_mfr_model, NULL);
static DEVICE_ATTR(mfr_revision, S_IRUGO, pmbus_show_mfr_revision, NULL);
static DEVICE_ATTR(mfr_location, S_IRUGO, pmbus_show_mfr_location, NULL);
static DEVICE_ATTR(mfr_serial, S_IRUGO, pmbus_show_mfr_serial, NULL);


static struct attribute *pmbus_inventory_attrs[] = {
    &dev_attr_mfr_id.attr,
    &dev_attr_mfr_model.attr,
    &dev_attr_mfr_revision.attr,
    &dev_attr_mfr_location.attr,
    &dev_attr_mfr_serial.attr,
    NULL
};

static struct attribute_group pmbus_inventory_attr_grp = {
    .attrs = pmbus_inventory_attrs
};

/* FIXME: add psu specific id here */
static const struct i2c_device_id pmbus_id[] = {
    {"ps2551", ps2551},
    {}
};
MODULE_DEVICE_TABLE(i2c, pmbus_id);

static int pmbus_probe(struct i2c_client *client,
			 const struct i2c_device_id *id)
{
	struct device *dev = &client->dev;
	struct pmbus_driver_info *info;

	int ret, i;

	dev_info(dev, "inspur-psu pmbus_probe\n");

	if (!i2c_check_functionality(client->adapter,
				     I2C_FUNC_SMBUS_READ_WORD_DATA))
		return -ENODEV;
	
	info = devm_kzalloc(&client->dev, sizeof(*info),
			    GFP_KERNEL);

	if (!info)
		return -ENOMEM;

	info->func[0] = 0;

	/* FIXME: add project specific function table here */
	switch (id->driver_data) {
	case ps2551:
		info->pages = 1;
		info->func[0] = PMBUS_HAVE_VIN | PMBUS_HAVE_IIN
		  | PMBUS_HAVE_PIN | PMBUS_HAVE_STATUS_INPUT
		  | PMBUS_HAVE_FAN12 | PMBUS_HAVE_STATUS_FAN12
		  | PMBUS_HAVE_TEMP | PMBUS_HAVE_TEMP2
		  | PMBUS_HAVE_TEMP3 | PMBUS_HAVE_STATUS_TEMP
		  | PMBUS_HAVE_VOUT | PMBUS_HAVE_STATUS_VOUT
		  | PMBUS_HAVE_IOUT | PMBUS_HAVE_STATUS_IOUT
		  | PMBUS_HAVE_POUT
		  ;
		dev_info(dev, "inspur-psu pmbus_probe : info->func[0] %x \n", info->func[0]);
		break;

	default:
		break;
	}
	
	/* FIXME: reserve for future use */
	//info->write_word_data = write_word_data;
	//info->write_byte = write_byte;
	//info->identify = pmbus_identify;	

	/* Register sysfs hooks */
	ret = sysfs_create_group(&dev->kobj, &pmbus_inventory_attr_grp);
	if (ret) {
		dev_err(dev, "Failed to create sysfs entries\n");
		return -1;
	}
	
	dev_info(dev, "inspur-psu pmbus_probe : exit\n");
	return pmbus_do_probe(client, id, info);
	
}

/* This is the driver that will be inserted */
static struct i2c_driver pmbus_driver = {
	.driver = {
		   .name = "inspur_psu",
		   },
	.probe = pmbus_probe,
	.remove = pmbus_do_remove,
	.id_table = pmbus_id,
};

module_i2c_driver(pmbus_driver);


MODULE_AUTHOR("sdn@inspur.com");
MODULE_VERSION("1.0");
MODULE_DESCRIPTION("SONiC platform driver for Inspur PSU");
MODULE_LICENSE("GPL");
