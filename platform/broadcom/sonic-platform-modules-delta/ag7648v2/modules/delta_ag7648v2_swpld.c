#include <linux/device.h>
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/sysfs.h>
#include <linux/platform_device.h>
#include <linux/i2c.h>
#include <linux/mutex.h>
#include <linux/completion.h>
#include <linux/hwmon-sysfs.h>
#include <linux/hwmon.h>



#define SWPLD1_ADDR 0x40
#define SWPLD2_ADDR 0x41
#define SWPLD3_ADDR 0x42
//#define SWPLD4_ADDR 0x43 T.B.D.


enum cpld_type {
    swpld1 = 0,
    swpld2,
    swpld3,
};

enum {
    BUS0 = 0,
    BUS1,
    BUS2,
    BUS3,
    BUS4,
    BUS5,
    BUS6,
    BUS7,
    BUS8,
};

enum swpld1_attr{
    BOARD_ID = 0,  //0X0
    BOARD_VER,
    DEV_VER,       //0X1
    PSU1_PWR_EN,   //0xb
    PSU2_PWR_EN,
    PSU2_PRESENT,  //0xc
    PSU2_PWOK,
    PSU1_PRESENT,
    PSU1_PWOK,
    SFP_P01_TXDIS, //0x12
    SFP_P02_TXDIS,
    SFP_P03_TXDIS,
    SFP_P04_TXDIS,
    SFP_P05_TXDIS,
    SFP_P06_TXDIS,
    SFP_P07_TXDIS,
    SFP_P08_TXDIS,
    SFP_P09_TXDIS, //0x13
    SFP_P10_TXDIS,
    SFP_P11_TXDIS,
    SFP_P12_TXDIS,
    SFP_P13_TXDIS,
    SFP_P14_TXDIS,
    SFP_P15_TXDIS,
    SFP_P16_TXDIS,
    HW_VERSION,    //0xf6
    SWPLD1_VER,    //0xf7
};

/* SWPLD2 */
enum swpld2_attr{
    SFP_P17_TXDIS = 0,
    SFP_P18_TXDIS,
    SFP_P19_TXDIS,
    SFP_P20_TXDIS,
    SFP_P21_TXDIS,
    SFP_P22_TXDIS,
    SFP_P23_TXDIS,
    SFP_P24_TXDIS,
    SFP_P25_TXDIS,
    SFP_P26_TXDIS,
    SFP_P27_TXDIS,
    SFP_P28_TXDIS,
    SFP_P29_TXDIS,
    SFP_P30_TXDIS,
    SFP_P31_TXDIS,
    SFP_P32_TXDIS,
    SFP_P33_TXDIS,
    SFP_P34_TXDIS,
    SFP_P35_TXDIS,
    SFP_P36_TXDIS,
    SFP_P37_TXDIS,
    SFP_P38_TXDIS,
    SFP_P39_TXDIS,
    SFP_P40_TXDIS,
    SFP_P01_MODPRS,
    SFP_P02_MODPRS,
    SFP_P03_MODPRS,
    SFP_P04_MODPRS,
    SFP_P05_MODPRS,
    SFP_P06_MODPRS,
    SFP_P07_MODPRS,
    SFP_P08_MODPRS,
    SFP_P09_MODPRS,
    SFP_P10_MODPRS,
    SFP_P11_MODPRS,
    SFP_P12_MODPRS,
    SFP_P13_MODPRS,
    SFP_P14_MODPRS,
    SFP_P15_MODPRS,
    SFP_P16_MODPRS,
    SFP_P17_MODPRS,
    SFP_P18_MODPRS,
    SFP_P19_MODPRS,
    SFP_P20_MODPRS,
    SFP_P21_MODPRS,
    SFP_P22_MODPRS,
    SFP_P23_MODPRS,
    SFP_P24_MODPRS,
    SFP_P25_MODPRS,
    SFP_P26_MODPRS,
    SFP_P27_MODPRS,
    SFP_P28_MODPRS,
    SFP_P29_MODPRS,
    SFP_P30_MODPRS,
    SFP_P31_MODPRS,
    SFP_P32_MODPRS,
    SFP_P01_TXFAULT,
    SFP_P02_TXFAULT,
    SFP_P03_TXFAULT,
    SFP_P04_TXFAULT,
    SFP_P05_TXFAULT,
    SFP_P06_TXFAULT,
    SFP_P07_TXFAULT,
    SFP_P08_TXFAULT,
    SFP_P09_TXFAULT,
    SFP_P10_TXFAULT,
    SFP_P11_TXFAULT,
    SFP_P12_TXFAULT,
    SFP_P13_TXFAULT,
    SFP_P14_TXFAULT,
    SFP_P15_TXFAULT,
    SFP_P16_TXFAULT,
    SFP_P17_TXFAULT,
    SFP_P18_TXFAULT,
    SFP_P19_TXFAULT,
    SFP_P20_TXFAULT,
    SFP_P21_TXFAULT,
    SFP_P22_TXFAULT,
    SFP_P23_TXFAULT,
    SFP_P24_TXFAULT,
    SFP_P25_TXFAULT,
    SFP_P26_TXFAULT,
    SFP_P27_TXFAULT,
    SFP_P28_TXFAULT,
    SFP_P29_TXFAULT,
    SFP_P30_TXFAULT,
    SFP_P31_TXFAULT,
    SFP_P32_TXFAULT,
    SFP_P01_RXLOS,
    SFP_P02_RXLOS,
    SFP_P03_RXLOS,
    SFP_P04_RXLOS,
    SFP_P05_RXLOS,
    SFP_P06_RXLOS,
    SFP_P07_RXLOS,
    SFP_P08_RXLOS,
    SFP_P09_RXLOS,
    SFP_P10_RXLOS,
    SFP_P11_RXLOS,
    SFP_P12_RXLOS,
    SFP_P13_RXLOS,
    SFP_P14_RXLOS,
    SFP_P15_RXLOS,
    SFP_P16_RXLOS,
    SFP_P17_RXLOS,
    SFP_P18_RXLOS,
    SFP_P19_RXLOS,
    SFP_P20_RXLOS,
    SFP_P21_RXLOS,
    SFP_P22_RXLOS,
    SFP_P23_RXLOS,
    SFP_P24_RXLOS,
    SFP_P25_RXLOS,
    SFP_P26_RXLOS,
    SFP_P27_RXLOS,
    SFP_P28_RXLOS,
    SFP_P29_RXLOS,
    SFP_P30_RXLOS,
    SFP_P31_RXLOS,
    SFP_P32_RXLOS,
    SWPLD2_VER,
};

/* SWPLD3 */
enum swpld3_attr{
    SFP_P41_TXDIS = 0,
    SFP_P42_TXDIS,
    SFP_P43_TXDIS,
    SFP_P44_TXDIS,
    SFP_P45_TXDIS,
    SFP_P46_TXDIS,
    SFP_P47_TXDIS,
    SFP_P48_TXDIS,
    SFP_P33_MODPRS,
    SFP_P34_MODPRS,
    SFP_P35_MODPRS,
    SFP_P36_MODPRS,
    SFP_P37_MODPRS,
    SFP_P38_MODPRS,
    SFP_P39_MODPRS,
    SFP_P40_MODPRS,
    SFP_P41_MODPRS,
    SFP_P42_MODPRS,
    SFP_P43_MODPRS,
    SFP_P44_MODPRS,
    SFP_P45_MODPRS,
    SFP_P46_MODPRS,
    SFP_P47_MODPRS,
    SFP_P48_MODPRS,
    SFP_P33_TXFAULT,
    SFP_P34_TXFAULT,
    SFP_P35_TXFAULT,
    SFP_P36_TXFAULT,
    SFP_P37_TXFAULT,
    SFP_P38_TXFAULT,
    SFP_P39_TXFAULT,
    SFP_P40_TXFAULT,
    SFP_P41_TXFAULT,
    SFP_P42_TXFAULT,
    SFP_P43_TXFAULT,
    SFP_P44_TXFAULT,
    SFP_P45_TXFAULT,
    SFP_P46_TXFAULT,
    SFP_P47_TXFAULT,
    SFP_P48_TXFAULT,
    SFP_P33_RXLOS,
    SFP_P34_RXLOS,
    SFP_P35_RXLOS,
    SFP_P36_RXLOS,
    SFP_P37_RXLOS,
    SFP_P38_RXLOS,
    SFP_P39_RXLOS,
    SFP_P40_RXLOS,
    SFP_P41_RXLOS,
    SFP_P42_RXLOS,
    SFP_P43_RXLOS,
    SFP_P44_RXLOS,
    SFP_P45_RXLOS,
    SFP_P46_RXLOS,
    SFP_P47_RXLOS,
    SFP_P48_RXLOS,
    QSFP_P49_RST,
    QSFP_P50_RST,
    QSFP_P51_RST,
    QSFP_P52_RST,
    QSFP_P53_RST,
    QSFP_P54_RST,
    QSFP_P49_MODPRS,
    QSFP_P50_MODPRS,
    QSFP_P51_MODPRS,
    QSFP_P52_MODPRS,
    QSFP_P53_MODPRS,
    QSFP_P54_MODPRS,
    QSFP_P49_INTR,
    QSFP_P50_INTR,
    QSFP_P51_INTR,
    QSFP_P52_INTR,
    QSFP_P53_INTR,
    QSFP_P54_INTR,
    QSFP_P49_LPMODE,
    QSFP_P50_LPMODE,
    QSFP_P51_LPMODE,
    QSFP_P52_LPMODE,
    QSFP_P53_LPMODE,
    QSFP_P54_LPMODE,
    SWPLD3_VER,
};


struct platform_data {
    int reg_addr;
    struct i2c_client *client;
};

struct cpld_platform_data {
    int reg_addr;
    struct i2c_client *client;
};

static struct kobject *kobj_swpld1;
static struct kobject *kobj_swpld2;
static struct kobject *kobj_swpld3;

unsigned char swpld1_reg_addr;
unsigned char swpld2_reg_addr;
unsigned char swpld3_reg_addr;

struct i2c_cpld_data {
    int type;
    int offset;
    int shift;
    int mask;
    char desc[256];
};

struct i2c_cpld_data swcpld1_data_list [] = {
{BOARD_ID, 0x0, 0, 0x30, "\r\nSWPLD1 Version.\r\n"},
{BOARD_VER, 0x0, 0, 0x0F, "\r\nBorad Version.\r\n"},
{DEV_VER, 0x01, 0, 0xFF, "\r\nDEV Version.\r\n"},
{PSU1_PWR_EN, 0x0B, 1, 0x01, "\r\n“1” = Disable.\r\n“0” = Enable.\r\n"},
{PSU2_PWR_EN, 0x0B, 0, 0x01, "\r\n“1” = Disable.\r\n“0” = Enable.\r\n"},
{PSU2_PRESENT, 0x0C, 5, 0x01, "\r\n“1” = Not present.\r\n“0” = Present.\r\n"},
{PSU2_PWOK, 0x0C, 4, 0x01, "\r\n“1” = Good.\r\n“0” = Fail.\r\n"},
{PSU1_PRESENT, 0x0C, 1, 0x01, "\r\n“1” = Not present.\r\n“0” = Present.\r\n"},
{PSU1_PWOK, 0x0C, 0, 0x01, "\r\n“1” = Good.\r\n“0” = Fail.\r\n"},
{SFP_P01_TXDIS, 0x12, 0, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P02_TXDIS, 0x12, 1, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P03_TXDIS, 0x12, 2, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P04_TXDIS, 0x12, 3, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P05_TXDIS, 0x12, 4, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P06_TXDIS, 0x12, 5, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P07_TXDIS, 0x12, 6, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P08_TXDIS, 0x12, 7, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P09_TXDIS, 0x13, 0, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P10_TXDIS, 0x13, 1, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P11_TXDIS, 0x13, 2, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P12_TXDIS, 0x13, 3, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P13_TXDIS, 0x13, 4, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P14_TXDIS, 0x13, 5, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P15_TXDIS, 0x13, 6, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P16_TXDIS, 0x13, 7, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{HW_VERSION, 0xF6, 0, 0x03, "\r\nSystem Board HW Version.\r\n"},
{SWPLD1_VER, 0xF7, 0, 0xFF, "\r\nSWPLD1 Version.\r\n"},
};

static ssize_t swpld1_data_show(struct device *dev, struct device_attribute *dev_attr, char *buf)
{
    struct sensor_device_attribute *attr = to_sensor_dev_attr(dev_attr);
    struct device *i2cdev = kobj_to_dev(kobj_swpld1->parent);
    struct platform_data *pdata = i2cdev->platform_data;
    unsigned char offset = 0;
    int mask = 0xFF;
    int shift = 0;
    int value = 0;
    bool hex_fmt = 0;
    char desc[256] = {0};
    int cnt = 0;

    for (cnt = 0; cnt < ARRAY_SIZE(swcpld1_data_list); cnt++) {
        if (attr->index == swcpld1_data_list[cnt].type){
            offset = swcpld1_data_list[cnt].offset;
            shift = swcpld1_data_list[cnt].shift;
            if (shift == 0){
                mask = swcpld1_data_list[cnt].mask;
            } else {
                mask = (1 << shift);
            }
            scnprintf(desc, PAGE_SIZE, swcpld1_data_list[cnt].desc);
        }
    }

    value = i2c_smbus_read_byte_data(pdata[swpld1].client, offset);
    value = (value & mask) >> shift;
    if(hex_fmt) {
        return scnprintf(buf, PAGE_SIZE, "0x%02x%s", value, desc);
    } else {
        return scnprintf(buf, PAGE_SIZE, "%d%s", value, desc);
    }
}

static ssize_t swpld1_data_store(struct device *dev, struct device_attribute *dev_attr,
             const char *buf, size_t count)
{
    struct sensor_device_attribute *attr = to_sensor_dev_attr(dev_attr);
    struct device *i2cdev = kobj_to_dev(kobj_swpld1->parent);
    struct platform_data *pdata = i2cdev->platform_data;
    unsigned char offset = 0;
    int mask = 0xFF;
    int shift = 0;
    int value = 0;
    int err = 0;
    int cnt = 0;
    unsigned long data;

    err = kstrtoul(buf, 0, &data);
    if (err){
        return err;
    }

    if (data > 0xff){
        printk(KERN_ALERT "address out of range (0x00-0xFF)\n");
        return count;
    }

    for (cnt = 0; cnt < ARRAY_SIZE(swcpld1_data_list); cnt++) {
        if (attr->index == swcpld1_data_list[cnt].type){
            offset = swcpld1_data_list[cnt].offset;
            shift = swcpld1_data_list[cnt].shift;
            if (shift == 0){
                mask = swcpld1_data_list[cnt].mask;
            } else {
                mask = (1 << shift);
            }
        }
    }

    value = i2c_smbus_read_byte_data(pdata[swpld1].client, offset);
    data = (value & ~mask) | (data << shift);
    i2c_smbus_write_byte_data(pdata[swpld1].client, offset, data);

    return count;
}

/* offset 0x0 */
static SENSOR_DEVICE_ATTR(board_id,         S_IRUGO,           swpld1_data_show, NULL,              BOARD_ID);
static SENSOR_DEVICE_ATTR(board_ver,        S_IRUGO,           swpld1_data_show, NULL,              BOARD_VER);
/* offser 0x01 */
static SENSOR_DEVICE_ATTR(dev_ver,       S_IRUGO,           swpld1_data_show, NULL,              DEV_VER);
/* offset 0x12 */
static SENSOR_DEVICE_ATTR(sfp_p01_txdis,     S_IRUGO | S_IWUSR, swpld1_data_show, swpld1_data_store, SFP_P01_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p02_txdis,     S_IRUGO | S_IWUSR, swpld1_data_show, swpld1_data_store, SFP_P02_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p03_txdis,     S_IRUGO | S_IWUSR, swpld1_data_show, swpld1_data_store, SFP_P03_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p04_txdis,     S_IRUGO | S_IWUSR, swpld1_data_show, swpld1_data_store, SFP_P04_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p05_txdis,     S_IRUGO | S_IWUSR, swpld1_data_show, swpld1_data_store, SFP_P05_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p06_txdis,     S_IRUGO | S_IWUSR, swpld1_data_show, swpld1_data_store, SFP_P06_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p07_txdis,     S_IRUGO | S_IWUSR, swpld1_data_show, swpld1_data_store, SFP_P07_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p08_txdis,     S_IRUGO | S_IWUSR, swpld1_data_show, swpld1_data_store, SFP_P08_TXDIS);
/* offset 0x13 */
static SENSOR_DEVICE_ATTR(sfp_p09_txdis,     S_IRUGO | S_IWUSR, swpld1_data_show, swpld1_data_store, SFP_P09_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p10_txdis,     S_IRUGO | S_IWUSR, swpld1_data_show, swpld1_data_store, SFP_P10_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p11_txdis,     S_IRUGO | S_IWUSR, swpld1_data_show, swpld1_data_store, SFP_P11_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p12_txdis,     S_IRUGO | S_IWUSR, swpld1_data_show, swpld1_data_store, SFP_P12_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p13_txdis,     S_IRUGO | S_IWUSR, swpld1_data_show, swpld1_data_store, SFP_P13_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p14_txdis,     S_IRUGO | S_IWUSR, swpld1_data_show, swpld1_data_store, SFP_P14_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p15_txdis,     S_IRUGO | S_IWUSR, swpld1_data_show, swpld1_data_store, SFP_P15_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p16_txdis,     S_IRUGO | S_IWUSR, swpld1_data_show, swpld1_data_store, SFP_P16_TXDIS);
/* offser 0x0B */
static SENSOR_DEVICE_ATTR(psu1_pwr_en,       S_IRUGO | S_IWUSR, swpld1_data_show, swpld1_data_store, PSU1_PWR_EN);
static SENSOR_DEVICE_ATTR(psu2_pwr_en,       S_IRUGO | S_IWUSR, swpld1_data_show, swpld1_data_store, PSU2_PWR_EN);
/* offser 0x0C */
static SENSOR_DEVICE_ATTR(psu2_present,         S_IRUGO,           swpld1_data_show, NULL,              PSU2_PRESENT);
static SENSOR_DEVICE_ATTR(psu2_pwok,         S_IRUGO,           swpld1_data_show, NULL,              PSU2_PWOK);
static SENSOR_DEVICE_ATTR(psu1_present,         S_IRUGO,           swpld1_data_show, NULL,              PSU1_PRESENT);
static SENSOR_DEVICE_ATTR(psu1_pwok,         S_IRUGO,           swpld1_data_show, NULL,              PSU1_PWOK);
/* offset 0xF6 */
static SENSOR_DEVICE_ATTR(hw_version,         S_IRUGO,           swpld1_data_show, NULL,              HW_VERSION);
/* offset 0xF7 */
static SENSOR_DEVICE_ATTR(swpld1_ver,         S_IRUGO,           swpld1_data_show, NULL,              SWPLD1_VER);

static struct attribute *swpld1_device_attrs[] = {
    &sensor_dev_attr_board_id.dev_attr.attr,
    &sensor_dev_attr_board_ver.dev_attr.attr,
    &sensor_dev_attr_dev_ver.dev_attr.attr,
    &sensor_dev_attr_psu1_pwr_en.dev_attr.attr,
    &sensor_dev_attr_psu2_pwr_en.dev_attr.attr,
    &sensor_dev_attr_psu2_present.dev_attr.attr,
    &sensor_dev_attr_psu2_pwok.dev_attr.attr,
    &sensor_dev_attr_psu1_present.dev_attr.attr,
    &sensor_dev_attr_psu1_pwok.dev_attr.attr,
    &sensor_dev_attr_sfp_p01_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p02_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p03_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p04_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p05_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p06_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p07_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p08_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p09_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p10_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p11_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p12_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p13_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p14_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p15_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p16_txdis.dev_attr.attr,
    &sensor_dev_attr_hw_version.dev_attr.attr,
    &sensor_dev_attr_swpld1_ver.dev_attr.attr,
};


struct i2c_cpld_data swcpld2_data_list [] = {
{SFP_P17_TXDIS, 0x0, 0, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P18_TXDIS, 0x0, 1, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P19_TXDIS, 0x0, 2, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P20_TXDIS, 0x0, 3, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P21_TXDIS, 0x0, 4, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P22_TXDIS, 0x0, 5, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P23_TXDIS, 0x0, 6, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P24_TXDIS, 0x0, 7, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P25_TXDIS, 0x01, 0, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P26_TXDIS, 0x01, 1, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P27_TXDIS, 0x01, 2, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P28_TXDIS, 0x01, 3, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P29_TXDIS, 0x01, 4, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P30_TXDIS, 0x01, 5, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P31_TXDIS, 0x01, 6, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P32_TXDIS, 0x01, 7, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P33_TXDIS, 0x02, 0, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P34_TXDIS, 0x02, 1, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P35_TXDIS, 0x02, 2, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P36_TXDIS, 0x02, 3, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P37_TXDIS, 0x02, 4, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P38_TXDIS, 0x02, 5, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P39_TXDIS, 0x02, 6, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P40_TXDIS, 0x02, 7, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P01_MODPRS, 0x03, 0, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P02_MODPRS, 0x03, 1, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P03_MODPRS, 0x03, 2, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P04_MODPRS, 0x03, 3, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P05_MODPRS, 0x03, 4, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P06_MODPRS, 0x03, 5, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P07_MODPRS, 0x03, 6, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P08_MODPRS, 0x03, 7, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P09_MODPRS, 0x04, 0, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P10_MODPRS, 0x04, 1, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P11_MODPRS, 0x04, 2, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P12_MODPRS, 0x04, 3, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P13_MODPRS, 0x04, 4, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P14_MODPRS, 0x04, 5, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P15_MODPRS, 0x04, 6, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P16_MODPRS, 0x04, 7, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P17_MODPRS, 0x05, 0, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P18_MODPRS, 0x05, 1, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P19_MODPRS, 0x05, 2, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P20_MODPRS, 0x05, 3, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P21_MODPRS, 0x05, 4, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P22_MODPRS, 0x05, 5, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P23_MODPRS, 0x05, 6, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P24_MODPRS, 0x05, 7, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P25_MODPRS, 0x06, 0, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P26_MODPRS, 0x06, 1, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P27_MODPRS, 0x06, 2, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P28_MODPRS, 0x06, 3, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P29_MODPRS, 0x06, 4, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P30_MODPRS, 0x06, 5, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P31_MODPRS, 0x06, 6, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P32_MODPRS, 0x06, 7, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P01_TXFAULT, 0x07, 0, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P02_TXFAULT, 0x07, 1, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P03_TXFAULT, 0x07, 2, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P04_TXFAULT, 0x07, 3, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P05_TXFAULT, 0x07, 4, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P06_TXFAULT, 0x07, 5, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P07_TXFAULT, 0x07, 6, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P08_TXFAULT, 0x07, 7, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P09_TXFAULT, 0x08, 0, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P10_TXFAULT, 0x08, 1, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P11_TXFAULT, 0x08, 2, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P12_TXFAULT, 0x08, 3, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P13_TXFAULT, 0x08, 4, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P14_TXFAULT, 0x08, 5, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P15_TXFAULT, 0x08, 6, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P16_TXFAULT, 0x08, 7, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P17_TXFAULT, 0x09, 0, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P18_TXFAULT, 0x09, 1, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P19_TXFAULT, 0x09, 2, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P20_TXFAULT, 0x09, 3, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P21_TXFAULT, 0x09, 4, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P22_TXFAULT, 0x09, 5, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P23_TXFAULT, 0x09, 6, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P24_TXFAULT, 0x09, 7, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P25_TXFAULT, 0x0A, 0, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P26_TXFAULT, 0x0A, 1, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P27_TXFAULT, 0x0A, 2, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P28_TXFAULT, 0x0A, 3, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P29_TXFAULT, 0x0A, 4, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P30_TXFAULT, 0x0A, 5, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P31_TXFAULT, 0x0A, 6, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P32_TXFAULT, 0x0A, 7, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P01_RXLOS, 0x0B, 0, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P02_RXLOS, 0x0B, 1, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P03_RXLOS, 0x0B, 2, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P04_RXLOS, 0x0B, 3, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P05_RXLOS, 0x0B, 4, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P06_RXLOS, 0x0B, 5, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P07_RXLOS, 0x0B, 6, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P08_RXLOS, 0x0B, 7, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P09_RXLOS, 0x0C, 0, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P10_RXLOS, 0x0C, 1, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P11_RXLOS, 0x0C, 2, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P12_RXLOS, 0x0C, 3, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P13_RXLOS, 0x0C, 4, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P14_RXLOS, 0x0C, 5, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P15_RXLOS, 0x0C, 6, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P16_RXLOS, 0x0C, 7, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P17_RXLOS, 0x0C, 0, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P18_RXLOS, 0x0C, 1, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P19_RXLOS, 0x0D, 2, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P20_RXLOS, 0x0D, 3, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P21_RXLOS, 0x0D, 4, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P22_RXLOS, 0x0D, 5, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P23_RXLOS, 0x0D, 6, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P24_RXLOS, 0x0D, 7, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P25_RXLOS, 0x0E, 0, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P26_RXLOS, 0x0E, 1, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P27_RXLOS, 0x0E, 2, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P28_RXLOS, 0x0E, 3, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P29_RXLOS, 0x0E, 4, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P30_RXLOS, 0x0E, 5, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P31_RXLOS, 0x0E, 6, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P32_RXLOS, 0x0E, 7, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SWPLD2_VER, 0x10, 0, 0xFF, "\r\nSWPLD2 Version.\r\n"},
};

static ssize_t swpld2_data_show(struct device *dev, struct device_attribute *dev_attr, char *buf)
{
    struct sensor_device_attribute *attr = to_sensor_dev_attr(dev_attr);
    struct device *i2cdev = kobj_to_dev(kobj_swpld2->parent);
    struct platform_data *pdata = i2cdev->platform_data;
    unsigned char offset = 0;
    int mask = 0xFF;
    int shift = 0;
    int value = 0;
    bool hex_fmt = 0;
    char desc[256] = {0};
    int cnt = 0;

    for (cnt = 0; cnt < ARRAY_SIZE(swcpld2_data_list); cnt++) {
        if (attr->index == swcpld2_data_list[cnt].type){
            offset = swcpld2_data_list[cnt].offset;
            shift = swcpld2_data_list[cnt].shift;
            if (shift == 0){
                mask = swcpld2_data_list[cnt].mask;
            } else {
                mask = (1 << shift);
            }
            scnprintf(desc, PAGE_SIZE, swcpld2_data_list[cnt].desc);
        }
    }

    value = i2c_smbus_read_byte_data(pdata[swpld2].client, offset);
    value = (value & mask) >> shift;
    if(hex_fmt) {
        return scnprintf(buf, PAGE_SIZE, "0x%02x%s", value, desc);
    } else {
        return scnprintf(buf, PAGE_SIZE, "%d%s", value, desc);
    }
}

static ssize_t swpld2_data_store(struct device *dev, struct device_attribute *dev_attr,
             const char *buf, size_t count)
{
    struct sensor_device_attribute *attr = to_sensor_dev_attr(dev_attr);
    struct device *i2cdev = kobj_to_dev(kobj_swpld2->parent);
    struct platform_data *pdata = i2cdev->platform_data;
    unsigned char offset = 0;
    int mask = 0xFF;
    int shift = 0;
    int value = 0;
    int err = 0;
    int cnt = 0;
    unsigned long data;

    err = kstrtoul(buf, 0, &data);
    if (err){
        return err;
    }

    if (data > 0xff){
        printk(KERN_ALERT "address out of range (0x00-0xFF)\n");
        return count;
    }

    for (cnt = 0; cnt < ARRAY_SIZE(swcpld2_data_list); cnt++) {
        if (attr->index == swcpld2_data_list[cnt].type){
            offset = swcpld2_data_list[cnt].offset;
            shift = swcpld2_data_list[cnt].shift;
            if (shift == 0){
                mask = swcpld2_data_list[cnt].mask;
            } else {
                mask = (1 << shift);
            }
        }
    }

    value = i2c_smbus_read_byte_data(pdata[swpld2].client, offset);
    data = (value & ~mask) | (data << shift);
    i2c_smbus_write_byte_data(pdata[swpld2].client, offset, data);

    return count;
}

/* offset 0x0 */
static SENSOR_DEVICE_ATTR(sfp_p17_txdis,     S_IRUGO | S_IWUSR, swpld2_data_show, swpld2_data_store, SFP_P17_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p18_txdis,     S_IRUGO | S_IWUSR, swpld2_data_show, swpld2_data_store, SFP_P18_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p19_txdis,     S_IRUGO | S_IWUSR, swpld2_data_show, swpld2_data_store, SFP_P19_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p20_txdis,     S_IRUGO | S_IWUSR, swpld2_data_show, swpld2_data_store, SFP_P20_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p21_txdis,     S_IRUGO | S_IWUSR, swpld2_data_show, swpld2_data_store, SFP_P21_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p22_txdis,     S_IRUGO | S_IWUSR, swpld2_data_show, swpld2_data_store, SFP_P22_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p23_txdis,     S_IRUGO | S_IWUSR, swpld2_data_show, swpld2_data_store, SFP_P23_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p24_txdis,     S_IRUGO | S_IWUSR, swpld2_data_show, swpld2_data_store, SFP_P24_TXDIS);
/* offset 0x01 */
static SENSOR_DEVICE_ATTR(sfp_p25_txdis,     S_IRUGO | S_IWUSR, swpld2_data_show, swpld2_data_store, SFP_P25_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p26_txdis,     S_IRUGO | S_IWUSR, swpld2_data_show, swpld2_data_store, SFP_P26_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p27_txdis,     S_IRUGO | S_IWUSR, swpld2_data_show, swpld2_data_store, SFP_P27_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p28_txdis,     S_IRUGO | S_IWUSR, swpld2_data_show, swpld2_data_store, SFP_P28_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p29_txdis,     S_IRUGO | S_IWUSR, swpld2_data_show, swpld2_data_store, SFP_P29_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p30_txdis,     S_IRUGO | S_IWUSR, swpld2_data_show, swpld2_data_store, SFP_P30_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p31_txdis,     S_IRUGO | S_IWUSR, swpld2_data_show, swpld2_data_store, SFP_P31_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p32_txdis,     S_IRUGO | S_IWUSR, swpld2_data_show, swpld2_data_store, SFP_P32_TXDIS);
/* offset 0x02 */
static SENSOR_DEVICE_ATTR(sfp_p33_txdis,     S_IRUGO | S_IWUSR, swpld2_data_show, swpld2_data_store, SFP_P33_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p34_txdis,     S_IRUGO | S_IWUSR, swpld2_data_show, swpld2_data_store, SFP_P34_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p35_txdis,     S_IRUGO | S_IWUSR, swpld2_data_show, swpld2_data_store, SFP_P35_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p36_txdis,     S_IRUGO | S_IWUSR, swpld2_data_show, swpld2_data_store, SFP_P36_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p37_txdis,     S_IRUGO | S_IWUSR, swpld2_data_show, swpld2_data_store, SFP_P37_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p38_txdis,     S_IRUGO | S_IWUSR, swpld2_data_show, swpld2_data_store, SFP_P38_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p39_txdis,     S_IRUGO | S_IWUSR, swpld2_data_show, swpld2_data_store, SFP_P39_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p40_txdis,     S_IRUGO | S_IWUSR, swpld2_data_show, swpld2_data_store, SFP_P40_TXDIS);
/* offset 0x03 */
static SENSOR_DEVICE_ATTR(sfp_p01_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P01_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p02_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P02_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p03_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P03_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p04_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P04_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p05_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P05_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p06_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P06_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p07_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P07_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p08_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P08_MODPRS);
/* offset 0x04 */
static SENSOR_DEVICE_ATTR(sfp_p09_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P09_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p10_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P10_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p11_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P11_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p12_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P12_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p13_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P13_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p14_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P14_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p15_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P15_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p16_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P16_MODPRS);
/* offset 0x05 */
static SENSOR_DEVICE_ATTR(sfp_p17_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P17_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p18_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P18_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p19_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P19_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p20_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P20_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p21_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P21_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p22_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P22_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p23_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P23_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p24_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P24_MODPRS);
/* offset 0x06 */
static SENSOR_DEVICE_ATTR(sfp_p25_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P25_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p26_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P26_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p27_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P27_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p28_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P28_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p29_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P29_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p30_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P30_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p31_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P31_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p32_modprs,    S_IRUGO,           swpld2_data_show, NULL,              SFP_P32_MODPRS);
/* offset 0x07 */
static SENSOR_DEVICE_ATTR(sfp_p01_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P01_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p02_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P02_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p03_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P03_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p04_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P04_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p05_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P05_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p06_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P06_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p07_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P07_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p08_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P08_TXFAULT);
/* offset 0x08 */
static SENSOR_DEVICE_ATTR(sfp_p09_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P09_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p10_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P10_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p11_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P11_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p12_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P12_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p13_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P13_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p14_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P14_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p15_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P15_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p16_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P16_TXFAULT);
/* offset 0x09 */
static SENSOR_DEVICE_ATTR(sfp_p17_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P17_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p18_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P18_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p19_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P19_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p20_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P20_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p21_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P21_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p22_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P22_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p23_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P23_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p24_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P24_TXFAULT);
/* offset 0x0A */
static SENSOR_DEVICE_ATTR(sfp_p25_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P25_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p26_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P26_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p27_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P27_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p28_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P28_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p29_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P29_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p30_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P30_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p31_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P31_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p32_txfault,   S_IRUGO,           swpld2_data_show, NULL,              SFP_P32_TXFAULT);
/* offset 0x0B */
static SENSOR_DEVICE_ATTR(sfp_p01_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P01_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p02_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P02_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p03_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P03_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p04_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P04_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p05_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P05_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p06_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P06_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p07_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P07_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p08_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P08_RXLOS);
/* offset 0x0C */
static SENSOR_DEVICE_ATTR(sfp_p09_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P09_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p10_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P10_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p11_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P11_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p12_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P12_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p13_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P13_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p14_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P14_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p15_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P15_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p16_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P16_RXLOS);
/* offset 0x0D */
static SENSOR_DEVICE_ATTR(sfp_p17_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P17_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p18_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P18_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p19_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P19_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p20_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P20_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p21_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P21_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p22_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P22_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p23_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P23_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p24_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P24_RXLOS);
/* offset 0x0E */
static SENSOR_DEVICE_ATTR(sfp_p25_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P25_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p26_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P26_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p27_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P27_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p28_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P28_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p29_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P29_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p30_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P30_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p31_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P31_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p32_rxlos,     S_IRUGO,           swpld2_data_show, NULL,              SFP_P32_RXLOS);
/* offset 0xF */
static SENSOR_DEVICE_ATTR(swpld2_ver,       S_IRUGO,           swpld2_data_show, NULL,              SWPLD2_VER);

static struct attribute *swpld2_device_attrs[] = {
    &sensor_dev_attr_sfp_p17_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p18_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p19_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p20_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p21_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p22_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p23_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p24_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p25_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p26_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p27_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p28_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p29_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p30_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p31_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p32_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p33_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p34_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p35_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p36_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p37_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p38_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p39_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p40_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p01_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p02_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p03_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p04_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p05_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p06_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p07_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p08_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p09_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p10_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p11_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p12_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p13_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p14_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p15_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p16_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p17_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p18_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p19_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p20_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p21_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p22_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p23_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p24_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p25_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p26_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p27_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p28_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p29_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p30_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p31_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p32_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p01_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p02_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p03_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p04_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p05_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p06_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p07_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p08_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p09_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p10_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p11_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p12_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p13_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p14_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p15_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p16_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p17_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p18_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p19_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p20_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p21_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p22_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p23_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p24_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p25_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p26_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p27_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p28_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p29_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p30_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p31_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p32_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p01_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p02_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p03_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p04_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p05_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p06_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p07_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p08_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p09_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p10_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p11_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p12_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p13_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p14_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p15_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p16_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p17_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p18_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p19_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p20_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p21_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p22_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p23_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p24_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p25_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p26_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p27_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p28_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p29_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p30_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p31_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p32_rxlos.dev_attr.attr,
    &sensor_dev_attr_swpld2_ver.dev_attr.attr,
};  

struct i2c_cpld_data swcpld3_data_list [] = {
{SFP_P41_TXDIS, 0x0, 0, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P42_TXDIS, 0x0, 1, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P43_TXDIS, 0x0, 2, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P44_TXDIS, 0x0, 3, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P45_TXDIS, 0x0, 4, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P46_TXDIS, 0x0, 5, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P47_TXDIS, 0x0, 6, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P48_TXDIS, 0x0, 7, 0x01, "\r\n“1” = Disable.\r\n“0” = Normal Operation.\r\n"},
{SFP_P33_MODPRS, 0x01, 0, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P34_MODPRS, 0x01, 1, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P35_MODPRS, 0x01, 2, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P36_MODPRS, 0x01, 3, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P37_MODPRS, 0x01, 4, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P38_MODPRS, 0x01, 5, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P39_MODPRS, 0x01, 6, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P40_MODPRS, 0x01, 7, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P41_MODPRS, 0x02, 0, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P42_MODPRS, 0x02, 1, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P43_MODPRS, 0x02, 2, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P44_MODPRS, 0x02, 3, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P45_MODPRS, 0x02, 4, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P46_MODPRS, 0x02, 5, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P47_MODPRS, 0x02, 6, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P48_MODPRS, 0x02, 7, 0x01, "\r\n“1” = Absent.\r\n“0” = Present.\r\n"},
{SFP_P33_TXFAULT, 0x03, 0, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P34_TXFAULT, 0x03, 1, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P35_TXFAULT, 0x03, 2, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P36_TXFAULT, 0x03, 3, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P37_TXFAULT, 0x03, 4, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P38_TXFAULT, 0x03, 5, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P39_TXFAULT, 0x03, 6, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P40_TXFAULT, 0x03, 7, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P41_TXFAULT, 0x04, 0, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P42_TXFAULT, 0x04, 1, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P43_TXFAULT, 0x04, 2, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P44_TXFAULT, 0x04, 3, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P45_TXFAULT, 0x04, 4, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P46_TXFAULT, 0x04, 5, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P47_TXFAULT, 0x04, 6, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P48_TXFAULT, 0x04, 7, 0x01, "\r\n“1” = Transmit Fault.\r\n“0” = Normal Operation.\r\n"},
{SFP_P33_RXLOS, 0x05, 0, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P34_RXLOS, 0x05, 1, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P35_RXLOS, 0x05, 2, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P36_RXLOS, 0x05, 3, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P37_RXLOS, 0x05, 4, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P38_RXLOS, 0x05, 5, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P39_RXLOS, 0x05, 6, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P40_RXLOS, 0x05, 7, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P41_RXLOS, 0x06, 0, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P42_RXLOS, 0x06, 1, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P43_RXLOS, 0x06, 2, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P44_RXLOS, 0x06, 3, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P45_RXLOS, 0x06, 4, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P46_RXLOS, 0x06, 5, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P47_RXLOS, 0x06, 6, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{SFP_P48_RXLOS, 0x06, 7, 0x01, "\r\n“1” = Receive Loss.\r\n“0” = Normal Operation.\r\n"},
{QSFP_P49_RST, 0x07, 0, 0x01, "\r\n“1” = Normal Operation.\r\n“0” = Reset.\r\n"},
{QSFP_P50_RST, 0x07, 1, 0x01, "\r\n“1” = Normal Operation.\r\n“0” = Reset.\r\n"},
{QSFP_P51_RST, 0x07, 2, 0x01, "\r\n“1” = Normal Operation.\r\n“0” = Reset.\r\n"},
{QSFP_P52_RST, 0x07, 3, 0x01, "\r\n“1” = Normal Operation.\r\n“0” = Reset.\r\n"},
{QSFP_P53_RST, 0x07, 4, 0x01, "\r\n“1” = Normal Operation.\r\n“0” = Reset.\r\n"},
{QSFP_P54_RST, 0x07, 5, 0x01, "\r\n“1” = Normal Operation.\r\n“0” = Reset.\r\n"},
{QSFP_P49_MODPRS, 0x08, 0, 0x01, "\r\n“1” = Not Present.\r\n“0” = Present.\r\n"},
{QSFP_P50_MODPRS, 0x08, 1, 0x01, "\r\n“1” = Not Present.\r\n“0” = Present.\r\n"},
{QSFP_P51_MODPRS, 0x08, 2, 0x01, "\r\n“1” = Not Present.\r\n“0” = Present.\r\n"},
{QSFP_P52_MODPRS, 0x08, 3, 0x01, "\r\n“1” = Not Present.\r\n“0” = Present.\r\n"},
{QSFP_P53_MODPRS, 0x08, 4, 0x01, "\r\n“1” = Not Present.\r\n“0” = Present.\r\n"},
{QSFP_P54_MODPRS, 0x08, 5, 0x01, "\r\n“1” = Not Present.\r\n“0” = Present.\r\n"},
{QSFP_P49_INTR, 0x09, 0, 0x01, "\r\n“1” = Not Present.\r\n“0” = Present.\r\n"},
{QSFP_P50_INTR, 0x09, 1, 0x01, "\r\n“1” = Not Present.\r\n“0” = Present.\r\n"},
{QSFP_P51_INTR, 0x09, 2, 0x01, "\r\n“1” = Not Present.\r\n“0” = Present.\r\n"},
{QSFP_P52_INTR, 0x09, 3, 0x01, "\r\n“1” = Not Present.\r\n“0” = Present.\r\n"},
{QSFP_P53_INTR, 0x09, 4, 0x01, "\r\n“1” = Not Present.\r\n“0” = Present.\r\n"},
{QSFP_P54_INTR, 0x09, 5, 0x01, "\r\n“1” = Not Present.\r\n“0” = Present.\r\n"},
{QSFP_P49_LPMODE, 0x0A, 0, 0x01, "\r\n“1” = LP Mode.\r\n“0” = Not LP Mode.\r\n"},
{QSFP_P50_LPMODE, 0x0A, 1, 0x01, "\r\n“1” = LP Mode.\r\n“0” = Not LP Mode.\r\n"},
{QSFP_P51_LPMODE, 0x0A, 2, 0x01, "\r\n“1” = LP Mode.\r\n“0” = Not LP Mode.\r\n"},
{QSFP_P52_LPMODE, 0x0A, 3, 0x01, "\r\n“1” = LP Mode.\r\n“0” = Not LP Mode.\r\n"},
{QSFP_P53_LPMODE, 0x0A, 4, 0x01, "\r\n“1” = LP Mode.\r\n“0” = Not LP Mode.\r\n"},
{QSFP_P54_LPMODE, 0x0A, 5, 0x01, "\r\n“1” = LP Mode.\r\n“0” = Not LP Mode.\r\n"},
{SWPLD3_VER, 0x10, 0, 0xFF, "\r\nSWPLD3 Version.\r\n"},
};

static ssize_t swpld3_data_show(struct device *dev, struct device_attribute *dev_attr, char *buf)
{
    struct sensor_device_attribute *attr = to_sensor_dev_attr(dev_attr);
    struct device *i2cdev = kobj_to_dev(kobj_swpld3->parent);
    struct platform_data *pdata = i2cdev->platform_data;
    unsigned char offset = 0;
    int mask = 0xFF;
    int shift = 0;
    int value = 0;
    bool hex_fmt = 0;
    char desc[256] = {0};
    int cnt = 0;

    for (cnt = 0; cnt < ARRAY_SIZE(swcpld3_data_list); cnt++) {
        if (attr->index == swcpld3_data_list[cnt].type){
            offset = swcpld3_data_list[cnt].offset;
            shift = swcpld3_data_list[cnt].shift;
            if (shift == 0){
                mask = swcpld3_data_list[cnt].mask;
            } else {
                mask = (1 << shift);
            }
            scnprintf(desc, PAGE_SIZE, swcpld3_data_list[cnt].desc);
        }
    }

    value = i2c_smbus_read_byte_data(pdata[swpld3].client, offset);
    value = (value & mask) >> shift;
    if(hex_fmt) {
        return scnprintf(buf, PAGE_SIZE, "0x%02x%s", value, desc);
    } else {
        return scnprintf(buf, PAGE_SIZE, "%d%s", value, desc);
    }
}


static ssize_t swpld3_data_store(struct device *dev, struct device_attribute *dev_attr,
             const char *buf, size_t count)
{
    struct sensor_device_attribute *attr = to_sensor_dev_attr(dev_attr);
    struct device *i2cdev = kobj_to_dev(kobj_swpld3->parent);
    struct platform_data *pdata = i2cdev->platform_data;
    unsigned char offset = 0;
    int mask = 0xFF;
    int shift = 0;
    int value = 0;
    int err = 0;
    unsigned long data;
    int cnt = 0;
    err = kstrtoul(buf, 0, &data);
    if (err){
        return err;
    }

    if (data > 0xff){
        printk(KERN_ALERT "address out of range (0x00-0xFF)\n");
        return count;
    }

    for (cnt = 0; cnt < ARRAY_SIZE(swcpld3_data_list); cnt++) {
        if (attr->index == swcpld3_data_list[cnt].type){
            offset = swcpld3_data_list[cnt].offset;
            shift = swcpld3_data_list[cnt].shift;
            if (shift == 0){
                mask = swcpld3_data_list[cnt].mask;
            } else {
                mask = (1 << shift);
            }
        }
    }

    value = i2c_smbus_read_byte_data(pdata[swpld3].client, offset);
    data = (value & ~mask) | (data << shift);
    i2c_smbus_write_byte_data(pdata[swpld3].client, offset, data);

    return count;
}

/* offset 0x0 */
static SENSOR_DEVICE_ATTR(sfp_p41_txdis,     S_IRUGO | S_IWUSR, swpld3_data_show, swpld3_data_store, SFP_P41_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p42_txdis,     S_IRUGO | S_IWUSR, swpld3_data_show, swpld3_data_store, SFP_P42_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p43_txdis,     S_IRUGO | S_IWUSR, swpld3_data_show, swpld3_data_store, SFP_P43_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p44_txdis,     S_IRUGO | S_IWUSR, swpld3_data_show, swpld3_data_store, SFP_P44_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p45_txdis,     S_IRUGO | S_IWUSR, swpld3_data_show, swpld3_data_store, SFP_P45_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p46_txdis,     S_IRUGO | S_IWUSR, swpld3_data_show, swpld3_data_store, SFP_P46_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p47_txdis,     S_IRUGO | S_IWUSR, swpld3_data_show, swpld3_data_store, SFP_P47_TXDIS);
static SENSOR_DEVICE_ATTR(sfp_p48_txdis,     S_IRUGO | S_IWUSR, swpld3_data_show, swpld3_data_store, SFP_P48_TXDIS);
/* offset 0x01 */
static SENSOR_DEVICE_ATTR(sfp_p33_modprs,    S_IRUGO,           swpld3_data_show, NULL,              SFP_P33_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p34_modprs,    S_IRUGO,           swpld3_data_show, NULL,              SFP_P34_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p35_modprs,    S_IRUGO,           swpld3_data_show, NULL,              SFP_P35_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p36_modprs,    S_IRUGO,           swpld3_data_show, NULL,              SFP_P36_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p37_modprs,    S_IRUGO,           swpld3_data_show, NULL,              SFP_P37_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p38_modprs,    S_IRUGO,           swpld3_data_show, NULL,              SFP_P38_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p39_modprs,    S_IRUGO,           swpld3_data_show, NULL,              SFP_P39_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p40_modprs,    S_IRUGO,           swpld3_data_show, NULL,              SFP_P40_MODPRS);
/* offset 0x02 */
static SENSOR_DEVICE_ATTR(sfp_p41_modprs,    S_IRUGO,           swpld3_data_show, NULL,              SFP_P41_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p42_modprs,    S_IRUGO,           swpld3_data_show, NULL,              SFP_P42_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p43_modprs,    S_IRUGO,           swpld3_data_show, NULL,              SFP_P43_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p44_modprs,    S_IRUGO,           swpld3_data_show, NULL,              SFP_P44_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p45_modprs,    S_IRUGO,           swpld3_data_show, NULL,              SFP_P45_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p46_modprs,    S_IRUGO,           swpld3_data_show, NULL,              SFP_P46_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p47_modprs,    S_IRUGO,           swpld3_data_show, NULL,              SFP_P47_MODPRS);
static SENSOR_DEVICE_ATTR(sfp_p48_modprs,    S_IRUGO,           swpld3_data_show, NULL,              SFP_P48_MODPRS);
/* offset 0x03 */
static SENSOR_DEVICE_ATTR(sfp_p33_txfault,   S_IRUGO,           swpld3_data_show, NULL,              SFP_P33_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p34_txfault,   S_IRUGO,           swpld3_data_show, NULL,              SFP_P34_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p35_txfault,   S_IRUGO,           swpld3_data_show, NULL,              SFP_P35_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p36_txfault,   S_IRUGO,           swpld3_data_show, NULL,              SFP_P36_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p37_txfault,   S_IRUGO,           swpld3_data_show, NULL,              SFP_P37_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p38_txfault,   S_IRUGO,           swpld3_data_show, NULL,              SFP_P38_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p39_txfault,   S_IRUGO,           swpld3_data_show, NULL,              SFP_P39_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p40_txfault,   S_IRUGO,           swpld3_data_show, NULL,              SFP_P40_TXFAULT);
/* offset 0x04 */
static SENSOR_DEVICE_ATTR(sfp_p41_txfault,   S_IRUGO,           swpld3_data_show, NULL,              SFP_P41_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p42_txfault,   S_IRUGO,           swpld3_data_show, NULL,              SFP_P42_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p43_txfault,   S_IRUGO,           swpld3_data_show, NULL,              SFP_P43_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p44_txfault,   S_IRUGO,           swpld3_data_show, NULL,              SFP_P44_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p45_txfault,   S_IRUGO,           swpld3_data_show, NULL,              SFP_P45_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p46_txfault,   S_IRUGO,           swpld3_data_show, NULL,              SFP_P46_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p47_txfault,   S_IRUGO,           swpld3_data_show, NULL,              SFP_P47_TXFAULT);
static SENSOR_DEVICE_ATTR(sfp_p48_txfault,   S_IRUGO,           swpld3_data_show, NULL,              SFP_P48_TXFAULT);
/* offset 0x05 */
static SENSOR_DEVICE_ATTR(sfp_p33_rxlos,     S_IRUGO,           swpld3_data_show, NULL,              SFP_P33_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p34_rxlos,     S_IRUGO,           swpld3_data_show, NULL,              SFP_P34_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p35_rxlos,     S_IRUGO,           swpld3_data_show, NULL,              SFP_P35_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p36_rxlos,     S_IRUGO,           swpld3_data_show, NULL,              SFP_P36_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p37_rxlos,     S_IRUGO,           swpld3_data_show, NULL,              SFP_P37_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p38_rxlos,     S_IRUGO,           swpld3_data_show, NULL,              SFP_P38_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p39_rxlos,     S_IRUGO,           swpld3_data_show, NULL,              SFP_P39_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p40_rxlos,     S_IRUGO,           swpld3_data_show, NULL,              SFP_P40_RXLOS);
/* offset 0x06 */
static SENSOR_DEVICE_ATTR(sfp_p41_rxlos,     S_IRUGO,           swpld3_data_show, NULL,              SFP_P41_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p42_rxlos,     S_IRUGO,           swpld3_data_show, NULL,              SFP_P42_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p43_rxlos,     S_IRUGO,           swpld3_data_show, NULL,              SFP_P43_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p44_rxlos,     S_IRUGO,           swpld3_data_show, NULL,              SFP_P44_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p45_rxlos,     S_IRUGO,           swpld3_data_show, NULL,              SFP_P45_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p46_rxlos,     S_IRUGO,           swpld3_data_show, NULL,              SFP_P46_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p47_rxlos,     S_IRUGO,           swpld3_data_show, NULL,              SFP_P47_RXLOS);
static SENSOR_DEVICE_ATTR(sfp_p48_rxlos,     S_IRUGO,           swpld3_data_show, NULL,              SFP_P48_RXLOS);
/* offset 0x07 */
static SENSOR_DEVICE_ATTR(qsfp_p49_rst,     S_IRUGO | S_IWUSR, swpld3_data_show, swpld3_data_store, QSFP_P49_RST);
static SENSOR_DEVICE_ATTR(qsfp_p50_rst,     S_IRUGO | S_IWUSR, swpld3_data_show, swpld3_data_store, QSFP_P50_RST);
static SENSOR_DEVICE_ATTR(qsfp_p51_rst,     S_IRUGO | S_IWUSR, swpld3_data_show, swpld3_data_store, QSFP_P51_RST);
static SENSOR_DEVICE_ATTR(qsfp_p52_rst,     S_IRUGO | S_IWUSR, swpld3_data_show, swpld3_data_store, QSFP_P52_RST);
static SENSOR_DEVICE_ATTR(qsfp_p53_rst,     S_IRUGO | S_IWUSR, swpld3_data_show, swpld3_data_store, QSFP_P53_RST);
static SENSOR_DEVICE_ATTR(qsfp_p54_rst,     S_IRUGO | S_IWUSR, swpld3_data_show, swpld3_data_store, QSFP_P54_RST);
/* offset 0x08 */
static SENSOR_DEVICE_ATTR(qsfp_p49_modprs,  S_IRUGO,           swpld3_data_show, NULL,              QSFP_P49_MODPRS);
static SENSOR_DEVICE_ATTR(qsfp_p50_modprs,  S_IRUGO,           swpld3_data_show, NULL,              QSFP_P50_MODPRS);
static SENSOR_DEVICE_ATTR(qsfp_p51_modprs,  S_IRUGO,           swpld3_data_show, NULL,              QSFP_P51_MODPRS);
static SENSOR_DEVICE_ATTR(qsfp_p52_modprs,  S_IRUGO,           swpld3_data_show, NULL,              QSFP_P52_MODPRS);
static SENSOR_DEVICE_ATTR(qsfp_p53_modprs,  S_IRUGO,           swpld3_data_show, NULL,              QSFP_P53_MODPRS);
static SENSOR_DEVICE_ATTR(qsfp_p54_modprs,  S_IRUGO,           swpld3_data_show, NULL,              QSFP_P54_MODPRS);
/* offset 0x09 */
static SENSOR_DEVICE_ATTR(qsfp_p49_intr,    S_IRUGO,           swpld3_data_show, NULL,              QSFP_P49_INTR);
static SENSOR_DEVICE_ATTR(qsfp_p50_intr,    S_IRUGO,           swpld3_data_show, NULL,              QSFP_P50_INTR);
static SENSOR_DEVICE_ATTR(qsfp_p51_intr,    S_IRUGO,           swpld3_data_show, NULL,              QSFP_P51_INTR);
static SENSOR_DEVICE_ATTR(qsfp_p52_intr,    S_IRUGO,           swpld3_data_show, NULL,              QSFP_P52_INTR);
static SENSOR_DEVICE_ATTR(qsfp_p53_intr,    S_IRUGO,           swpld3_data_show, NULL,              QSFP_P53_INTR);
static SENSOR_DEVICE_ATTR(qsfp_p54_intr,    S_IRUGO,           swpld3_data_show, NULL,              QSFP_P54_INTR);
/* offset 0x0A */
static SENSOR_DEVICE_ATTR(qsfp_p49_lpmode,  S_IRUGO | S_IWUSR, swpld3_data_show, swpld3_data_store, QSFP_P49_LPMODE);
static SENSOR_DEVICE_ATTR(qsfp_p50_lpmode,  S_IRUGO | S_IWUSR, swpld3_data_show, swpld3_data_store, QSFP_P50_LPMODE);
static SENSOR_DEVICE_ATTR(qsfp_p51_lpmode,  S_IRUGO | S_IWUSR, swpld3_data_show, swpld3_data_store, QSFP_P51_LPMODE);
static SENSOR_DEVICE_ATTR(qsfp_p52_lpmode,  S_IRUGO | S_IWUSR, swpld3_data_show, swpld3_data_store, QSFP_P52_LPMODE);
static SENSOR_DEVICE_ATTR(qsfp_p53_lpmode,  S_IRUGO | S_IWUSR, swpld3_data_show, swpld3_data_store, QSFP_P53_LPMODE);
static SENSOR_DEVICE_ATTR(qsfp_p54_lpmode,  S_IRUGO | S_IWUSR, swpld3_data_show, swpld3_data_store, QSFP_P54_LPMODE);
/* offset 0x10 */
static SENSOR_DEVICE_ATTR(swpld3_ver,       S_IRUGO,           swpld3_data_show, NULL,              SWPLD3_VER);

static struct attribute *swpld3_device_attrs[] = {
    &sensor_dev_attr_sfp_p41_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p42_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p43_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p44_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p45_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p46_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p47_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p48_txdis.dev_attr.attr,
    &sensor_dev_attr_sfp_p33_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p34_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p35_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p36_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p37_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p38_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p39_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p40_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p41_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p42_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p43_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p44_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p45_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p46_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p47_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p48_modprs.dev_attr.attr,
    &sensor_dev_attr_sfp_p33_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p34_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p35_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p36_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p37_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p38_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p39_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p40_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p41_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p42_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p43_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p44_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p45_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p46_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p47_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p48_txfault.dev_attr.attr,
    &sensor_dev_attr_sfp_p33_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p34_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p35_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p36_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p37_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p38_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p39_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p40_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p41_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p42_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p43_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p44_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p45_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p46_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p47_rxlos.dev_attr.attr,
    &sensor_dev_attr_sfp_p48_rxlos.dev_attr.attr,
    &sensor_dev_attr_qsfp_p49_rst.dev_attr.attr,
    &sensor_dev_attr_qsfp_p50_rst.dev_attr.attr,
    &sensor_dev_attr_qsfp_p51_rst.dev_attr.attr,
    &sensor_dev_attr_qsfp_p52_rst.dev_attr.attr,
    &sensor_dev_attr_qsfp_p53_rst.dev_attr.attr,
    &sensor_dev_attr_qsfp_p54_rst.dev_attr.attr,
    &sensor_dev_attr_qsfp_p49_modprs.dev_attr.attr,
    &sensor_dev_attr_qsfp_p50_modprs.dev_attr.attr,
    &sensor_dev_attr_qsfp_p51_modprs.dev_attr.attr,
    &sensor_dev_attr_qsfp_p52_modprs.dev_attr.attr,
    &sensor_dev_attr_qsfp_p53_modprs.dev_attr.attr,
    &sensor_dev_attr_qsfp_p54_modprs.dev_attr.attr,
    &sensor_dev_attr_qsfp_p49_intr.dev_attr.attr,
    &sensor_dev_attr_qsfp_p50_intr.dev_attr.attr,
    &sensor_dev_attr_qsfp_p51_intr.dev_attr.attr,
    &sensor_dev_attr_qsfp_p52_intr.dev_attr.attr,
    &sensor_dev_attr_qsfp_p53_intr.dev_attr.attr,
    &sensor_dev_attr_qsfp_p54_intr.dev_attr.attr,
    &sensor_dev_attr_qsfp_p49_lpmode.dev_attr.attr,
    &sensor_dev_attr_qsfp_p50_lpmode.dev_attr.attr,
    &sensor_dev_attr_qsfp_p51_lpmode.dev_attr.attr,
    &sensor_dev_attr_qsfp_p52_lpmode.dev_attr.attr,
    &sensor_dev_attr_qsfp_p53_lpmode.dev_attr.attr,
    &sensor_dev_attr_qsfp_p54_lpmode.dev_attr.attr,
    &sensor_dev_attr_swpld3_ver.dev_attr.attr,
};

static struct attribute_group swpld1_device_attr_group = {
    .attrs = swpld1_device_attrs,
};

static struct attribute_group swpld2_device_attr_group = {
    .attrs = swpld2_device_attrs,
};

static struct attribute_group swpld3_device_attr_group = {
    .attrs = swpld3_device_attrs,
};


static struct cpld_platform_data ag7648v2_swpld_platform_data[] = {
    [swpld1] = {
        .reg_addr = SWPLD1_ADDR,
    },
    [swpld2] = {
        .reg_addr = SWPLD2_ADDR,
    },
    [swpld3] = {
        .reg_addr = SWPLD3_ADDR,
    },
};

static void device_release(struct device *dev)
{
    return;
}


static struct platform_device swpld_device = {
        .name               = "delta-ag7648v2-swpld",
        .id                 = 0,
        .dev                = {
                    .platform_data   = ag7648v2_swpld_platform_data,
                    .release         = device_release
        },
};


static int __init swpld_probe(struct platform_device *pdev)
{
    int ret;
    struct cpld_platform_data *pdata;
    struct i2c_adapter *parent;

    pdata = pdev->dev.platform_data;
    if (!pdata) {
        dev_err(&pdev->dev, "CPLD platform data not found\n");
        return -ENODEV;
    }

    parent = i2c_get_adapter(BUS5);
    if (!parent) {
        printk(KERN_ERR "Parent adapter (%d) not found\n", BUS5);
        return -ENODEV;
    }

    pdata[swpld1].client = i2c_new_dummy(parent, pdata[swpld1].reg_addr);
    if (!pdata[swpld1].client) {
        printk(KERN_ERR "Fail to create dummy i2c client for addr %d\n", pdata[swpld1].reg_addr);
        goto error_swpld1;
    }

    pdata[swpld2].client = i2c_new_dummy(parent, pdata[swpld2].reg_addr);
    if (!pdata[swpld2].client) {
        printk(KERN_ERR "Fail to create dummy i2c client for addr %d\n", pdata[swpld2].reg_addr);
        goto error_swpld2;
    }

    pdata[swpld3].client = i2c_new_dummy(parent, pdata[swpld3].reg_addr);
    if (!pdata[swpld3].client) {
        printk(KERN_ERR "Fail to create dummy i2c client for addr %d\n", pdata[swpld3].reg_addr);
        goto error_swpld3;
    }

    kobj_swpld1 = kobject_create_and_add("SWPLD1", &pdev->dev.kobj);
    if (!kobj_swpld1){
        printk(KERN_ERR "Fail to create directory");
        goto error_swpld3;
    }
 
    kobj_swpld2 = kobject_create_and_add("SWPLD2", &pdev->dev.kobj);
    if (!kobj_swpld2){
        printk(KERN_ERR "Fail to create directory");
        goto error_swpld3;
    }

    kobj_swpld3 = kobject_create_and_add("SWPLD3", &pdev->dev.kobj);
    if (!kobj_swpld3){
        printk(KERN_ERR "Fail to create directory");
        goto error_swpld3;
    }

    ret = sysfs_create_group(kobj_swpld1, &swpld1_device_attr_group);
    if (ret) {
        printk(KERN_ERR "Fail to create SWPLD1 attribute group");
        goto error_add_swpld1;
    }

    ret = sysfs_create_group(kobj_swpld2, &swpld2_device_attr_group);
    if (ret) {
        printk(KERN_ERR "Fail to create SWPLD2 attribute group");
        goto error_add_swpld2;
    }

    ret = sysfs_create_group(kobj_swpld3, &swpld3_device_attr_group);
    if (ret) {
        printk(KERN_ERR "Fail to create SWPLD3 attribute group");
        goto error_add_swpld3;
    }

    return 0;

error_add_swpld3:
    kobject_put(kobj_swpld2);
error_add_swpld2:
    kobject_put(kobj_swpld1);
error_add_swpld1:
    i2c_unregister_device(pdata[swpld3].client);
error_swpld3:
    i2c_unregister_device(pdata[swpld2].client);
error_swpld2:
    i2c_unregister_device(pdata[swpld1].client);
error_swpld1:
    i2c_put_adapter(parent);

    return 1;
}

static int __exit swpld_remove(struct platform_device *pdev)
{
    struct i2c_adapter *parent = NULL;
    struct cpld_platform_data *pdata = pdev->dev.platform_data;

    if (!kobj_swpld1){
        sysfs_remove_group(kobj_swpld1, &swpld1_device_attr_group);
    }
    if (!kobj_swpld2){
        sysfs_remove_group(kobj_swpld2, &swpld2_device_attr_group);
    }
    if (!kobj_swpld3){
        sysfs_remove_group(kobj_swpld3, &swpld3_device_attr_group);
    }
    if (!pdata) {
        dev_err(&pdev->dev, "Missing platform data\n");
    }
    else {
        if (pdata[swpld1].client) {
            if (!parent) {
                parent = (pdata[swpld1].client)->adapter;
            }
            i2c_unregister_device(pdata[swpld1].client);
        }
        if (pdata[swpld2].client) {
            if (!parent) {
                parent = (pdata[swpld2].client)->adapter;
            }
            i2c_unregister_device(pdata[swpld2].client);
        }
        if (pdata[swpld3].client) {
            if (!parent) {
                parent = (pdata[swpld3].client)->adapter;
            }
            i2c_unregister_device(pdata[swpld3].client);
        }
    }
    i2c_put_adapter(parent);

    i2c_smbus_write_byte_data(pdata[swpld3].client, 0x07, 0xff);
    i2c_smbus_write_byte_data(pdata[swpld3].client, 0x0a, 0x0);


    return 0;
}

static struct platform_driver swpld_driver = {
    .probe  = swpld_probe,
    .remove = __exit_p(swpld_remove),
    .driver = {
        .owner  = THIS_MODULE,
        .name   = "delta-ag7648v2-swpld",
    },
};


static int __init delta_ag7648v2_swpld_init(void)
{
    int ret;

    printk(KERN_INFO "ag7648v2_platform_swpld module initialization\n");

    /* Register SWPLD driver */
    ret = platform_driver_register(&swpld_driver);
    if (ret) {
        printk(KERN_ERR "Fail to register swpld driver\n");
        goto error_swpld1_driver;
    }

    /* Register SWPLD Device */
    ret = platform_device_register(&swpld_device);
    if (ret) {
        printk(KERN_ERR "Fail to create swpld device\n");
        goto error_swpld1_device;
    }

    return 0;

    printk(KERN_INFO "ag7648v2_platform_swpld module initialization -- to error \n");

error_swpld1_device:
    platform_driver_unregister(&swpld_driver);
error_swpld1_driver:

    return ret;
}

static void __exit delta_ag7648v2_swpld_exit(void)
{

    platform_device_unregister(&swpld_device);
    platform_driver_unregister(&swpld_driver);
}

module_init(delta_ag7648v2_swpld_init);
module_exit(delta_ag7648v2_swpld_exit);

MODULE_DESCRIPTION("DNI AG7648V2 SWPLD Platform Support");
MODULE_AUTHOR("Jean Yi Chen <jean.yi.chen@deltaww.com>");
MODULE_LICENSE("GPL");
