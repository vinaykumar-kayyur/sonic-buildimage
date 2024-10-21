#include <linux/module.h>
#include <linux/init.h>
#include <linux/slab.h>
#include <linux/jiffies.h>
#include <linux/i2c.h>
#include <linux/hwmon.h>
#include <linux/hwmon-sysfs.h>
#include <linux/err.h>
#include <linux/mutex.h>
#include <linux/fs.h>
#include <linux/uaccess.h>
#include <linux/delay.h>

#define RC32312_PAGE_REG                    (0xfd)
#define RC32312_OUT_CTRL_EN                 (0x0001)
#define RC32312_OUT_CTRL_DIS                (0x0002)

static int g_wb_rc32312_debug = 0;
static int g_wb_rc32312_error = 0;

module_param(g_wb_rc32312_debug, int, S_IRUGO | S_IWUSR);
module_param(g_wb_rc32312_error, int, S_IRUGO | S_IWUSR);

#define WB_RC32312_VERBOSE(fmt, args...) do {                                        \
    if (g_wb_rc32312_debug) { \
        printk(KERN_INFO "[WB_RC32312][VER][func:%s line:%d]\n"fmt, __func__, __LINE__, ## args); \
    } \
} while (0)

#define WB_RC32312_ERROR(fmt, args...) do {                                        \
    if (g_wb_rc32312_error) { \
        printk(KERN_ERR "[WB_RC32312][ERR][func:%s line:%d]\n"fmt, __func__, __LINE__, ## args); \
    } \
} while (0)

enum chips {
    rc32312
};

struct rc32312_data {
    struct i2c_client   *client;
    struct mutex        update_lock;
    struct attribute_group *sysfs_group;
    int page_reg;
};

int rc32312_set_page(struct i2c_client *client, int page)
{
    struct rc32312_data *data = i2c_get_clientdata(client);
    int rv;

    rv = i2c_smbus_write_byte_data(client, data->page_reg, page);
    if (rv < 0) {
        WB_RC32312_ERROR("rc32312 wirte page failed page_reg 0x%x target page %d, errno: %d\n", data->page_reg, page, rv);
        return rv;
    }

    rv = i2c_smbus_read_byte_data(client, data->page_reg);
    if (rv < 0) {
        WB_RC32312_ERROR("rc32312 read page failed page_reg 0x%x target page %d, errno: %d\n", data->page_reg, page, rv);
        return rv;
    }

    if (rv != page) {
        WB_RC32312_ERROR("rc32312 current page %d != target page %d \n", rv, page);
        return -EIO;
    }
    WB_RC32312_VERBOSE("rc32312 set to page: %d success \n", page);
    return 0;
}

static s32 rc32312_read_byte_data(struct i2c_client *client, int page, u8 reg)
{
    int rv;

    rv = rc32312_set_page(client, page);
    if (rv < 0) {
        WB_RC32312_ERROR("rc32312 read byte setting page failed errno: %d\n", rv);
        return rv;
    }

    return i2c_smbus_read_byte_data(client, reg);
}

static s32 rc32312_read_word_data(struct i2c_client *client, int page, u8 reg)
{
    int rv;

    rv = rc32312_set_page(client, page);
    if (rv < 0) {
        WB_RC32312_ERROR("rc32312 read word setting page failed errno: %d\n", rv);
        return rv;
    }

    return i2c_smbus_read_word_data(client, reg);
}

static int rc32312_write_byte_data(struct i2c_client *client, int page, u8 reg, u8 value)
{
    int rv;

    rv = rc32312_set_page(client, page);
    if (rv < 0) {
        WB_RC32312_ERROR("rc32312 write byte setting page failed errno: %d\n", rv);
        return rv;
    }

    return i2c_smbus_write_byte_data(client, reg, value);
}

static int rc32312_write_word_data(struct i2c_client *client, int page, u8 reg, u16 value)
{
    int rv;

    rv = rc32312_set_page(client, page);
    if (rv < 0) {
        WB_RC32312_ERROR("rc32312 write byte setting page failed errno: %d\n", rv);
        return rv;
    }

    return i2c_smbus_write_word_data(client, reg, value);
}

static ssize_t show_rc32312_value(struct device *dev, struct device_attribute *da, char *buf)
{
    struct rc32312_data *data = dev_get_drvdata(dev);
    struct i2c_client *client = data->client;
    int reg = to_sensor_dev_attr_2(da)->index;
    int page = to_sensor_dev_attr_2(da)->nr;
    s32 status;

    status = -1;
    mutex_lock(&data->update_lock);
    status = rc32312_read_byte_data(client, page, reg);
    if (status < 0) {
        WB_RC32312_ERROR("rc32312 show value failed page [%d] reg [0x%x], errno: %d\n", page, reg, status);
        mutex_unlock(&data->update_lock);
        return status;
    }
    WB_RC32312_VERBOSE("rc32312 show value success page [%d] reg[0x%x] read value[0x%x]\n", page, reg, status);
    mutex_unlock(&data->update_lock);
    return snprintf(buf, PAGE_SIZE, "0x%x\n", status & 0xff);
}

static ssize_t set_rc32312_value(struct device *dev, struct device_attribute *da, const char *buf, size_t count)
{
    struct rc32312_data *data = dev_get_drvdata(dev);
    struct i2c_client *client = data->client;
    int reg = to_sensor_dev_attr_2(da)->index;
    int page = to_sensor_dev_attr_2(da)->nr;
    u8 val;
    int ret;

    ret = kstrtou8(buf, 0, &val);
    if (ret) {
        WB_RC32312_ERROR("Invaild input value [%s], errno: %d\n", buf, ret);
        return -EINVAL;
    }

    mutex_lock(&data->update_lock);
    ret = rc32312_write_byte_data(client, page, reg, val);
    if (ret < 0) {
        WB_RC32312_ERROR("rc32312 set value failed page [%d] reg [0x%x] val [0x%x], errno: %d\n", page, reg, val, ret);
        mutex_unlock(&data->update_lock);
        return ret;
    }
    WB_RC32312_VERBOSE("rc32312 set value success page [%d] reg[0x%x] value[0x%x]\n", page, reg, val);
    mutex_unlock(&data->update_lock);

    return count;
}

static ssize_t show_rc32312_out_ctrl_value(struct device *dev, struct device_attribute *da, char *buf)
{
    struct rc32312_data *data = dev_get_drvdata(dev);
    struct i2c_client *client = data->client;
    int reg = to_sensor_dev_attr_2(da)->index;
    int page = to_sensor_dev_attr_2(da)->nr;
    s32 status;

    status = -1;
    mutex_lock(&data->update_lock);
    status = rc32312_read_word_data(client, page, reg);
    if (status < 0) {
        WB_RC32312_ERROR("rc32312 read word data failed page [%d] reg [0x%x], errno: %d\n", page, reg, status);
        mutex_unlock(&data->update_lock);
        return status;
    }
    WB_RC32312_VERBOSE("rc32312 read word data success page [%d] reg[0x%x] read value[0x%x]\n", page, reg, status);

    mutex_unlock(&data->update_lock);
    if (status == RC32312_OUT_CTRL_EN) {
        return snprintf(buf, PAGE_SIZE, "1\n");
    }

    if (status == RC32312_OUT_CTRL_DIS) {
        return snprintf(buf, PAGE_SIZE, "0\n");
    }

    return snprintf(buf, PAGE_SIZE, "0x%04x\n", status & 0xffff);
}


static ssize_t set_rc32312_out_ctrl_value(struct device *dev, struct device_attribute *da, const char *buf, size_t count)
{
    struct rc32312_data *data = dev_get_drvdata(dev);
    struct i2c_client *client = data->client;
    int reg = to_sensor_dev_attr_2(da)->index;
    int page = to_sensor_dev_attr_2(da)->nr;
    u16 val;
    int ret;

    ret = kstrtou16(buf, 0, &val);
    if (ret) {
        dev_err(&client->dev, "Invaild input value [%s], errno: %d\n", buf, ret);
        return -EINVAL;
    }

    if ((val != 0) && (val != 1)) {
        dev_err(&client->dev, "Unsupport value: %d, please enter 0 or 1\n", val);
        return -EINVAL;
    }

    if (val == 0) {
        val = RC32312_OUT_CTRL_DIS;
    } else {
        val = RC32312_OUT_CTRL_EN;
    }

    mutex_lock(&data->update_lock);
    ret = rc32312_write_word_data(client, page, reg, val);
    if (ret < 0) {
        WB_RC32312_ERROR("rc32312 write word data failed page [%d] reg [0x%x] val [0x%x], errno: %d\n", page, reg, val, ret);
        mutex_unlock(&data->update_lock);
        return ret;
    }
    WB_RC32312_VERBOSE("rc32312 write word data success page [%d] reg[0x%x] value[0x%x]\n", page, reg, val);
    mutex_unlock(&data->update_lock);
    return count;
}


static SENSOR_DEVICE_ATTR_2(apll_event, S_IRUGO | S_IWUSR, show_rc32312_value, set_rc32312_value, 2, 0x6e);
static SENSOR_DEVICE_ATTR_2(apll_log_event, S_IRUGO | S_IWUSR, show_rc32312_value, set_rc32312_value, 2, 0x6f);
static SENSOR_DEVICE_ATTR_2(apll_sts, S_IRUGO, show_rc32312_value, NULL, 2, 0x71);
static SENSOR_DEVICE_ATTR_2(out_en_ctrl_0, S_IRUGO | S_IWUSR, show_rc32312_out_ctrl_value, set_rc32312_out_ctrl_value, 1, 0x04);
static SENSOR_DEVICE_ATTR_2(out_en_ctrl_1, S_IRUGO | S_IWUSR, show_rc32312_out_ctrl_value, set_rc32312_out_ctrl_value, 1, 0x0c);
static SENSOR_DEVICE_ATTR_2(out_en_ctrl_2, S_IRUGO | S_IWUSR, show_rc32312_out_ctrl_value, set_rc32312_out_ctrl_value, 1, 0x14);
static SENSOR_DEVICE_ATTR_2(out_en_ctrl_3, S_IRUGO | S_IWUSR, show_rc32312_out_ctrl_value, set_rc32312_out_ctrl_value, 1, 0x1c);
static SENSOR_DEVICE_ATTR_2(out_en_ctrl_4, S_IRUGO | S_IWUSR, show_rc32312_out_ctrl_value, set_rc32312_out_ctrl_value, 1, 0x24);
static SENSOR_DEVICE_ATTR_2(out_en_ctrl_5, S_IRUGO | S_IWUSR, show_rc32312_out_ctrl_value, set_rc32312_out_ctrl_value, 1, 0x2c);
static SENSOR_DEVICE_ATTR_2(out_en_ctrl_6, S_IRUGO | S_IWUSR, show_rc32312_out_ctrl_value, set_rc32312_out_ctrl_value, 1, 0x34);
static SENSOR_DEVICE_ATTR_2(out_en_ctrl_7, S_IRUGO | S_IWUSR, show_rc32312_out_ctrl_value, set_rc32312_out_ctrl_value, 1, 0x3c);
static SENSOR_DEVICE_ATTR_2(out_en_ctrl_8, S_IRUGO | S_IWUSR, show_rc32312_out_ctrl_value, set_rc32312_out_ctrl_value, 1, 0x44);
static SENSOR_DEVICE_ATTR_2(out_en_ctrl_9, S_IRUGO | S_IWUSR, show_rc32312_out_ctrl_value, set_rc32312_out_ctrl_value, 1, 0x4c);
static SENSOR_DEVICE_ATTR_2(out_en_ctrl_10, S_IRUGO | S_IWUSR, show_rc32312_out_ctrl_value, set_rc32312_out_ctrl_value, 1, 0x54);
static SENSOR_DEVICE_ATTR_2(out_en_ctrl_11, S_IRUGO | S_IWUSR, show_rc32312_out_ctrl_value, set_rc32312_out_ctrl_value, 1, 0x5c);

static struct attribute *rc32312_sysfs_attrs[] = {
    &sensor_dev_attr_apll_event.dev_attr.attr,
    &sensor_dev_attr_apll_log_event.dev_attr.attr,
    &sensor_dev_attr_apll_sts.dev_attr.attr,
    &sensor_dev_attr_out_en_ctrl_0.dev_attr.attr,
    &sensor_dev_attr_out_en_ctrl_1.dev_attr.attr,
    &sensor_dev_attr_out_en_ctrl_2.dev_attr.attr,
    &sensor_dev_attr_out_en_ctrl_3.dev_attr.attr,
    &sensor_dev_attr_out_en_ctrl_4.dev_attr.attr,
    &sensor_dev_attr_out_en_ctrl_5.dev_attr.attr,
    &sensor_dev_attr_out_en_ctrl_6.dev_attr.attr,
    &sensor_dev_attr_out_en_ctrl_7.dev_attr.attr,
    &sensor_dev_attr_out_en_ctrl_8.dev_attr.attr,
    &sensor_dev_attr_out_en_ctrl_9.dev_attr.attr,
    &sensor_dev_attr_out_en_ctrl_10.dev_attr.attr,
    &sensor_dev_attr_out_en_ctrl_11.dev_attr.attr,
    NULL
};

static struct attribute_group  rc32312_sysfs_group = {
    .attrs = rc32312_sysfs_attrs,
};

static int rc32312_probe(struct i2c_client *client, const struct i2c_device_id *id)
{
    struct rc32312_data *data;
    int ret;

    dev_dbg(&client->dev, "RC32312 enter probe\n");
    data = devm_kzalloc(&client->dev, sizeof(struct rc32312_data), GFP_KERNEL);
    if (!data) {
        dev_err(&client->dev, "RC32312 alloc memory failed\n");
        return -ENOMEM;
    }

    data->client = client;
    i2c_set_clientdata(client, data);
    mutex_init(&data->update_lock);

    switch (id->driver_data) {
    case rc32312:
        data->sysfs_group = &rc32312_sysfs_group;
        data->page_reg = RC32312_PAGE_REG;
        break;
    default:
        dev_err(&client->dev, "Unknown chip id %ld\n", id->driver_data);
        return -ENODEV;
    }

    ret = sysfs_create_group(&client->dev.kobj, data->sysfs_group);
    if (ret < 0) {
        dev_err(&client->dev, "RC32312 sysfs_create_group failed %d\n", ret);
    }
    return 0;
}

static int rc32312_remove(struct i2c_client *client)
{
    struct rc32312_data *data = i2c_get_clientdata(client);

    if (data->sysfs_group) {
        dev_err(&client->dev, "RC32312 unregister sysfs group\n");
        sysfs_remove_group(&client->dev.kobj, (const struct attribute_group *)data->sysfs_group);
    }
    dev_info(&client->dev, "RC32312 removed\n");
    return 0;
}

static const struct i2c_device_id rc32312_id[] = {
    { "wb_rc32312", rc32312 },
    {}
};
MODULE_DEVICE_TABLE(i2c, rc32312_id);

static struct i2c_driver wb_rc32312_driver = {
    .class      = I2C_CLASS_HWMON,
    .driver = {
        .name   = "wb_rc32312",
    },
    .probe      = rc32312_probe,
    .remove     = rc32312_remove,
    .id_table   = rc32312_id,
};

module_i2c_driver(wb_rc32312_driver);
MODULE_AUTHOR("support");
MODULE_DESCRIPTION("RC32312 driver");
MODULE_LICENSE("GPL");
