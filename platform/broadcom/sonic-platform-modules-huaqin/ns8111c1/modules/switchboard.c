/*================================================================
*   Copyright (C) 2020 Huaqin Technology Co.,Ltd.
*                 All rights reserved.
*   Building 10, No, 399, Keyuan Road, Pudong, Shanghai
*   
*   
*   File Name   : switchboard.c
*   Author      : carl.wang (carl.wang@huaqin.com)
*   Created Time: Thu Dec 14 16:12:51 2020
*   Description : switchboard.c -- the driver for FPGA and switch CPLD.
*   Copyright (C) 2020 Huaqin Corp.
* 
*   This program is free software. You can redistribute it and/or modify
*   it under the terms of the GNU General Public License as published by 
*   the free software foundation, either version 0 of the License, Or (at
*   your option) any later version.  
*   
================================================================*/

#include <linux/interrupt.h>
#include <linux/module.h>
#include <linux/pci.h>
#include <linux/kernel.h>
#include <linux/stddef.h>
#include <linux/delay.h>
#include <linux/ioport.h>
#include <linux/init.h>
#include <linux/i2c.h>
#include <linux/acpi.h>
#include <linux/io.h>
#include <linux/dmi.h>
#include <linux/slab.h>
#include <linux/wait.h>
#include <linux/err.h>
#include <linux/kobject.h>
#include <linux/platform_device.h>
#include <linux/types.h>
#include <uapi/linux/stat.h>
#include <linux/fs.h>
#include <linux/uaccess.h>
#include <linux/jiffies.h>
#include "def.h"

#define MOD_VERSION "0.0.1"
#define MOD_NAME	"switchboard"

#define CLASS_NAME 		"hq_fpga"
#define DRIVER_NAME 	"hq_switch"

static int fpga_pci_probe(struct pci_dev *pdev);
static void fpga_pci_remove(void);

/* MISC       */
#define FPGA_VERSION            0x0000
#define FPGA_VERSION_MJ_MSK     0xff00
#define FPGA_VERSION_MN_MSK     0x00ff
#define FPGA_SCRATCH            0x0004

#define FPGA_PORT_XCVR_READY    0x000c

#define I2C_MASTER_CH_1             1
#define I2C_MASTER_CH_2             2
#define I2C_MASTER_CH_7             7
#define I2C_MASTER_CH_8             8
#define I2C_MASTER_CH_9             9
#define I2C_MASTER_CH_10			10
#define I2C_MASTER_CH_11			11
#define I2C_MASTER_CH_12			12
#define I2C_MASTER_CH_13			13
#define I2C_MASTER_CH_14			14

/* FPGA FRONT PANEL PORT MGMT */
#define SFF_PORT_CTRL_BASE          0x4000
#define SFF_PORT_STATUS_BASE        0x4004
#define SFF_PORT_INT_STATUS_BASE    0x4008
#define SFF_PORT_INT_MASK_BASE      0x400c

#define PORT_XCVR_REGISTER_SIZE     0x1000

/* PORT CTRL REGISTER
[31:7]  RSVD
[6]     LPMOD   6
[5]     RSVD
[4]     RST     4
[3:1]   RSVD
[0]     TXDIS   0
*/
#define CTRL_LPMOD   6
#define CTRL_RST     4
#define CTRL_TXDIS   0

/* PORT STATUS REGISTER
[31:6]  RSVD
[5]     IRQ         5
[4]     PRESENT     4
[3]     RSVD
[2]     TXFAULT     2
[1]     RXLOS       1
[0]     MODABS      0
*/
#define STAT_IRQ         5
#define STAT_PRESENT     4
#define STAT_TXFAULT     2
#define STAT_RXLOS       1
#define STAT_MODABS      0

/* PORT INTRPT REGISTER
[31:6]  RSVD
[5]     INT_N       5
[4]     PRESENT     4
[3]     RSVD
[2]     RSVD
[1]     RXLOS       1
[0]     MODABS      0
*/
#define INTR_INT_N      5
#define INTR_PRESENT    4
#define INTR_TXFAULT    2
#define INTR_RXLOS      1
#define INTR_MODABS     0

/* PORT INT MASK REGISTER
[31:6]  RSVD
[5]     INT_N       5
[4]     PRESENT     4
[3]     RSVD
[2]     RSVD
[1]     RXLOS_INT   1
[0]     MODABS      0
*/
#define MASK_INT_N      5
#define MASK_PRESENT    4
#define MASK_TXFAULT    2
#define MASK_RXLOS      1
#define MASK_MODABS     0

/**
 *
 * The function is i2c algorithm implement to allow master access to
 * correct endpoint devices trough the PCA9548 switch devices.
 *
 *  FPGA I2C Master [mutex resource]
 *              |
 *              |
 *    ---------------------------
 *    |        PCA9548(s)       |
 *    ---1--2--3--4--5--6--7--8--
 *       |  |  |  |  |  |  |  |
 *   EEPROM      ...          EEPROM
 *
 */

#define VIRTUAL_I2C_QSFP_PORT   8
#define VIRTUAL_I2C_SFP_PORT    24
#define FANCPLD_SLAVE_ADDR		0x0D	/* FAN CPLD */
#define CPLD1_SLAVE_ADDR        0x30	/* SWITCHBOARD CPLD1 */
#define CPLD2_SLAVE_ADDR        0x30	/* SWITCHBOARD CPLD2 */
#define NUM_I2C_CLIENT          3
#define SFF_PORT_TOTAL    VIRTUAL_I2C_QSFP_PORT + VIRTUAL_I2C_SFP_PORT

static struct class*  fpgafwclass  = NULL; // < The device-driver class struct pointer

enum PORT_TYPE {
    NONE,
    QSFP,
    SFP
};

struct i2c_switch {
    unsigned char master_bus;   // I2C bus number
    unsigned char switch_addr;  // PCA9548 device address, 0xFF if directly connect to a bus.
    unsigned char channel;      // PCA9548 channel number. If the switch_addr is 0xFF, this value is ignored.
    enum PORT_TYPE port_type;   // QSFP/SFP tranceiver port type.
    char calling_name[20];      // Calling name.
};

struct i2c_dev_data {
    int portid;
    struct i2c_switch pca9548;
};

/* PREDEFINED I2C SWITCH DEVICE TOPOLOGY */
static struct i2c_switch fpga_i2c_bus_dev[] = {
    /* BUS3 QSFP Exported as virtual bus */
    {I2C_MASTER_CH_8, SFP_PORT_PCA9548_ADD, 0, SFP, "QSFP1"}, {I2C_MASTER_CH_8, SFP_PORT_PCA9548_ADD, 1, SFP, "QSFP2"},
    {I2C_MASTER_CH_8, SFP_PORT_PCA9548_ADD, 2, SFP, "QSFP3"}, {I2C_MASTER_CH_8, SFP_PORT_PCA9548_ADD, 3, SFP, "QSFP4"},
    {I2C_MASTER_CH_8, SFP_PORT_PCA9548_ADD, 4, SFP, "QSFP5"}, {I2C_MASTER_CH_8, SFP_PORT_PCA9548_ADD, 5, SFP, "QSFP6"},
    {I2C_MASTER_CH_8, SFP_PORT_PCA9548_ADD, 6, SFP, "QSFP7"}, {I2C_MASTER_CH_8, SFP_PORT_PCA9548_ADD, 7, SFP, "QSFP8"},

    {I2C_MASTER_CH_9, SFP_PORT_PCA9548_ADD, 0, SFP, "QSFP9"}, {I2C_MASTER_CH_9, SFP_PORT_PCA9548_ADD, 1, SFP, "QSFP10"},
    {I2C_MASTER_CH_9, SFP_PORT_PCA9548_ADD, 2, SFP, "QSFP11"}, {I2C_MASTER_CH_9, SFP_PORT_PCA9548_ADD, 3, SFP, "QSFP12"},
    {I2C_MASTER_CH_9, SFP_PORT_PCA9548_ADD, 4, SFP, "QSFP13"}, {I2C_MASTER_CH_9, SFP_PORT_PCA9548_ADD, 5, SFP, "QSFP14"},
    {I2C_MASTER_CH_9, SFP_PORT_PCA9548_ADD, 6, SFP, "QSFP15"}, {I2C_MASTER_CH_9, SFP_PORT_PCA9548_ADD, 7, SFP, "QSFP16"},

    {I2C_MASTER_CH_10, SFP_PORT_PCA9548_ADD, 0, SFP, "QSFP17"}, {I2C_MASTER_CH_10, SFP_PORT_PCA9548_ADD, 1, SFP, "QSFP18"},
    {I2C_MASTER_CH_10, SFP_PORT_PCA9548_ADD, 2, SFP, "QSFP19"}, {I2C_MASTER_CH_10, SFP_PORT_PCA9548_ADD, 3, SFP, "QSFP20"},
    {I2C_MASTER_CH_10, SFP_PORT_PCA9548_ADD, 4, SFP, "QSFP21"}, {I2C_MASTER_CH_10, SFP_PORT_PCA9548_ADD, 5, SFP, "QSFP22"},
    {I2C_MASTER_CH_10, SFP_PORT_PCA9548_ADD, 6, SFP, "QSFP23"}, {I2C_MASTER_CH_10, SFP_PORT_PCA9548_ADD, 7, SFP, "QSFP24"},

    {I2C_MASTER_CH_14, SFP_PORT_PCA9548_ADD, 0, QSFP, "QSFPDD25"}, {I2C_MASTER_CH_14, SFP_PORT_PCA9548_ADD, 1, QSFP, "QSFPDD26"},
    {I2C_MASTER_CH_14, SFP_PORT_PCA9548_ADD, 2, QSFP, "QSFPDD27"}, {I2C_MASTER_CH_14, SFP_PORT_PCA9548_ADD, 3, QSFP, "QSFPDD28"},
    {I2C_MASTER_CH_14, SFP_PORT_PCA9548_ADD, 4, QSFP, "QSFPDD29"}, {I2C_MASTER_CH_14, SFP_PORT_PCA9548_ADD, 5, QSFP, "QSFPDD30"},
    {I2C_MASTER_CH_14, SFP_PORT_PCA9548_ADD, 6, QSFP, "QSFPDD31"}, {I2C_MASTER_CH_14, SFP_PORT_PCA9548_ADD, 7, QSFP, "QSFPDD32"},

	{I2C_MASTER_CH_1, 0xFF, 0, NONE, "FCPLD"},
    {I2C_MASTER_CH_2, 0xFF, 0, NONE, "CPLD1"},
    {I2C_MASTER_CH_7, 0xFF, 0, NONE, "CPLD2"},  
};

struct fpga_device {
    /* data mmio region */
    void __iomem *data_base_addr;
    resource_size_t data_mmio_start;
    resource_size_t data_mmio_len;
};

static struct fpga_device fpga_dev = {
    .data_base_addr = 0,
    .data_mmio_start = 0,
    .data_mmio_len = 0,
};

struct switchboard_fpga_data {
    struct device *sff_devices[SFF_PORT_TOTAL];
    struct i2c_client *cpld_i2c_clients[NUM_I2C_CLIENT];
    struct mutex fpga_lock;         // For FPGA internal lock
    void __iomem * fpga_read_addr;
    uint8_t cpld1_read_addr;
    uint8_t cpld2_read_addr;
	uint8_t fan_cpld_read_addr;
};

struct sff_device_data {
    int portid;
    enum PORT_TYPE port_type;
};

struct switchboard_fpga_data *fpga_data;

/*
 * Kernel object for other module drivers.
 * Other module can use these kobject as a parent.
 */
static struct kobject *fpga = NULL;
static struct kobject *cpld1 = NULL;
static struct kobject *cpld2 = NULL;
static struct kobject *fan_cpld = NULL;

/**
 * Device node in sysfs tree.
 */
static struct device *sff_dev = NULL;

/**
 * Show the value of the register set by 'set_fpga_reg_address'
 * If the address is not set by 'set_fpga_reg_address' first,
 * The version register is selected by default.
 * @param  buf     register value in hextring
 * @return         number of bytes read, or an error code
 */
static ssize_t get_fpga_reg_value(struct device *dev, struct device_attribute *devattr,
                                  char *buf)
{
    // read data from the address
    uint32_t data;
    data = ioread32(fpga_data->fpga_read_addr);
    return sprintf(buf, "0x%8.8x\n", data);
}
/**
 * Store the register address
 * @param  buf     address wanted to be read value of
 * @return         number of bytes stored, or an error code
 */
static ssize_t set_fpga_reg_address(struct device *dev, struct device_attribute *devattr,
                                    const char *buf, size_t count)
{
    uint32_t addr;
    char *last;

    addr = (uint32_t)strtoul(buf, &last, 16);
    if (addr == 0 && buf == last) {
        return -EINVAL;
    }
    fpga_data->fpga_read_addr = fpga_dev.data_base_addr + addr;
    return count;
}
/**
 * Show value of fpga scratch register
 * @param  buf     register value in hexstring
 * @return         number of bytes read, or an error code
 */
static ssize_t get_fpga_scratch(struct device *dev, struct device_attribute *devattr,
                                char *buf)
{
    return sprintf(buf, "0x%8.8x\n", ioread32(fpga_dev.data_base_addr + FPGA_SCRATCH) & 0xffffffff);
}
/**
 * Store value of fpga scratch register
 * @param  buf     scratch register value passing from user space
 * @return         number of bytes stored, or an error code
 */
static ssize_t set_fpga_scratch(struct device *dev, struct device_attribute *devattr,
                                const char *buf, size_t count)
{
    uint32_t data;
    char *last;
    data = (uint32_t)strtoul(buf, &last, 16);
    if (data == 0 && buf == last) {
        return -EINVAL;
    }
    iowrite32(data, fpga_dev.data_base_addr + FPGA_SCRATCH);
    return count;
}
/**
 * Store a value in a specific register address
 * @param  buf     the value and address in format '0xhhhh 0xhhhhhhhh'
 * @return         number of bytes sent by user space, or an error code
 */
static ssize_t set_fpga_reg_value(struct device *dev, struct device_attribute *devattr,
                                  const char *buf, size_t count)
{
    // register are 4 bytes
    uint32_t addr;
    uint32_t value;
    uint32_t mode = 8;
    char *tok;
    char clone[count+1];
    char *pclone = clone;
    char *last;

    strcpy(clone, buf);

    mutex_lock(&fpga_data->fpga_lock);
    tok = strsep((char**)&pclone, " ");
    if (tok == NULL) {
        mutex_unlock(&fpga_data->fpga_lock);
        return -EINVAL;
    }
    addr = (uint32_t)strtoul(tok, &last, 16);
    if (addr == 0 && tok == last) {
        mutex_unlock(&fpga_data->fpga_lock);
        return -EINVAL;
    }
    tok = strsep((char**)&pclone, " ");
    if (tok == NULL) {
        mutex_unlock(&fpga_data->fpga_lock);
        return -EINVAL;
    }
    value = (uint32_t)strtoul(tok, &last, 16);
    if (value == 0 && tok == last) {
        mutex_unlock(&fpga_data->fpga_lock);
        return -EINVAL;
    }
    tok = strsep((char**)&pclone, " ");
    if (tok == NULL) {
        mode = 32;
    } else {
        mode = (uint32_t)strtoul(tok, &last, 10);
        if (mode == 0 && tok == last) {
            mutex_unlock(&fpga_data->fpga_lock);
            return -EINVAL;
        }
    }
    if (mode == 32) {
        iowrite32(value, fpga_dev.data_base_addr + addr);
    } else if (mode == 8) {
        iowrite8(value, fpga_dev.data_base_addr + addr);
    } else {
        mutex_unlock(&fpga_data->fpga_lock);
        return -EINVAL;
    }
    mutex_unlock(&fpga_data->fpga_lock);
    return count;
}

/**
 * Read all FPGA XCVR register in binary mode.
 * @param  buf   Raw transceivers port startus and control register values
 * @return       number of bytes read, or an error code
 */
static ssize_t dump_read(struct file *filp, struct kobject *kobj,
                         struct bin_attribute *attr, char *buf,
                         loff_t off, size_t count)
{
    unsigned long i = 0;
    ssize_t status;
    u8 read_reg;

    if ( off + count > PORT_XCVR_REGISTER_SIZE ) {
        return -EINVAL;
    }
    mutex_lock(&fpga_data->fpga_lock);
    while (i < count) {
        read_reg = ioread8(fpga_dev.data_base_addr + SFF_PORT_CTRL_BASE + off + i);
        buf[i++] = read_reg;
    }
    status = count;
    mutex_unlock(&fpga_data->fpga_lock);
    return status;
}

/**
 * Show FPGA port XCVR ready status
 * @param  buf  1 if the functin is ready, 0 if not.
 * @return      number of bytes read, or an error code
 */
static ssize_t ready_show(struct device *dev, struct device_attribute *attr, char *buf)
{
    u32 data;
    unsigned int REGISTER = FPGA_PORT_XCVR_READY;

    mutex_lock(&fpga_data->fpga_lock);
    data = ioread32(fpga_dev.data_base_addr + REGISTER);
    mutex_unlock(&fpga_data->fpga_lock);
    return sprintf(buf, "%d\n", (data >> 0) & 1U);
}

/* FPGA attributes */
static DEVICE_ATTR( getreg, 0600, get_fpga_reg_value, set_fpga_reg_address);
static DEVICE_ATTR( scratch, 0600, get_fpga_scratch, set_fpga_scratch);
static DEVICE_ATTR( setreg, 0200, NULL , set_fpga_reg_value);
static DEVICE_ATTR_RO(ready);
static BIN_ATTR_RO( dump, PORT_XCVR_REGISTER_SIZE);

static struct bin_attribute *fpga_bin_attrs[] = {
    &bin_attr_dump,
    NULL,
};

static struct attribute *fpga_attrs[] = {
    &dev_attr_getreg.attr,
    &dev_attr_scratch.attr,
    &dev_attr_setreg.attr,
    //&dev_attr_ready.attr,
    NULL,
};

static struct attribute_group fpga_attr_grp = {
    .attrs = fpga_attrs,
    //.bin_attrs = fpga_bin_attrs,
};

/* SW CPLDs attributes */
static ssize_t cpld1_getreg_show(struct device *dev, struct device_attribute *attr, char *buf)
{
    // CPLD register is one byte
    uint8_t data;
    struct i2c_client *client = fpga_data->cpld_i2c_clients[0];
    data = i2c_smbus_read_byte_data(client, fpga_data->cpld1_read_addr);
    if(data < 0)
        return data;
    return sprintf(buf, "0x%2.2x\n", data);
}

static ssize_t cpld1_getreg_store(struct device *dev, struct device_attribute *attr, const char *buf, size_t size)
{
    uint8_t addr;
    char *last;
    addr = (uint8_t)strtoul(buf, &last, 16);
    if (addr == 0 && buf == last) {
        return -EINVAL;
    }
    fpga_data->cpld1_read_addr = addr;
    return size;
}

struct device_attribute dev_attr_cpld1_getreg = __ATTR(getreg, 0600, cpld1_getreg_show, cpld1_getreg_store);

static ssize_t cpld1_scratch_show(struct device *dev, struct device_attribute *attr, char *buf)
{
    // CPLD register is one byte
    int value;
    struct i2c_client *client = fpga_data->cpld_i2c_clients[0];

    value = i2c_smbus_read_byte_data(client, 0x04);
    if(value < 0)
        return value;
    return sprintf(buf, "0x%.2x\n", value);
}

static ssize_t cpld1_scratch_store(struct device *dev, struct device_attribute *attr, const char *buf, size_t size)
{
    // CPLD register is one byte
    
    u8 value;
    ssize_t status;
    struct i2c_client *client = fpga_data->cpld_i2c_clients[0];

    status = kstrtou8(buf, 0, &value);
    if(status != 0)
        return status;
    status = i2c_smbus_write_byte_data(client, 0x04, value);
    if(status == 0)
        status = size;
    return status;
}
struct device_attribute dev_attr_cpld1_scratch = __ATTR(scratch, 0600, cpld1_scratch_show, cpld1_scratch_store);

static ssize_t cpld1_setreg_store(struct device *dev, struct device_attribute *attr, const char *buf, size_t size)
{

    uint8_t addr, value;
    struct i2c_client *client = fpga_data->cpld_i2c_clients[0];
    char *tok;
    char clone[size+1];
    char *pclone = clone;
    char *last;
    int err;

    strcpy(clone, buf);

    tok = strsep((char**)&pclone, " ");
    if (tok == NULL) {
        return -EINVAL;
    }
    addr = (uint8_t)strtoul(tok, &last, 16);
    if (addr == 0 && tok == last) {
        return -EINVAL;
    }
    tok = strsep((char**)&pclone, " ");
    if (tok == NULL) {
        return -EINVAL;
    }
    value = (uint8_t)strtoul(tok, &last, 16);
    if (value == 0 && tok == last) {
        return -EINVAL;
    }
    err = i2c_smbus_write_byte_data(client, addr, value);
    if (err < 0)
        return err;

    return size;
}
struct device_attribute dev_attr_cpld1_setreg = __ATTR(setreg, 0200, NULL, cpld1_setreg_store);

static struct attribute *cpld1_attrs[] = {
    &dev_attr_cpld1_getreg.attr,
    &dev_attr_cpld1_scratch.attr,
    &dev_attr_cpld1_setreg.attr,
    NULL,
};

static struct attribute_group cpld1_attr_grp = {
    .attrs = cpld1_attrs,
};

static ssize_t cpld2_getreg_show(struct device *dev, struct device_attribute *attr, char *buf)
{
    // CPLD register is one byte
    uint8_t data;
    struct i2c_client *client = fpga_data->cpld_i2c_clients[1];
    data = i2c_smbus_read_byte_data(client, fpga_data->cpld2_read_addr);
    if(data < 0)
        return data;
    return sprintf(buf, "0x%2.2x\n", data);
}

static ssize_t cpld2_getreg_store(struct device *dev, struct device_attribute *attr, const char *buf, size_t size)
{
    // CPLD register is one byte
    uint8_t addr;
    char *last;
    addr = (uint8_t)strtoul(buf, &last, 16);
    if (addr == 0 && buf == last) {
        return -EINVAL;
    }
    fpga_data->cpld2_read_addr = addr;
    return size;
}
struct device_attribute dev_attr_cpld2_getreg = __ATTR(getreg, 0600, cpld2_getreg_show, cpld2_getreg_store);

static ssize_t cpld2_scratch_show(struct device *dev, struct device_attribute *attr, char *buf)
{
    // CPLD register is one byte
    int value;
    struct i2c_client *client = fpga_data->cpld_i2c_clients[1];

    value = i2c_smbus_read_byte_data(client, 0x04);
    if(value < 0)
        return value;
    return sprintf(buf, "0x%.2x\n", value);
}

static ssize_t cpld2_scratch_store(struct device *dev, struct device_attribute *attr, const char *buf, size_t size)
{
    // CPLD register is one byte
    u8 value;
    ssize_t status;
    struct i2c_client *client = fpga_data->cpld_i2c_clients[1];

    status = kstrtou8(buf, 0, &value);
    if(status != 0)
        return status;
    status = i2c_smbus_write_byte_data(client, 0x04, value);
    if(status == 0)
        status = size;
    return status;
}
struct device_attribute dev_attr_cpld2_scratch = __ATTR(scratch, 0600, cpld2_scratch_show, cpld2_scratch_store);

static ssize_t cpld2_setreg_store(struct device *dev, struct device_attribute *attr, const char *buf, size_t size)
{
    uint8_t addr, value;
    struct i2c_client *client = fpga_data->cpld_i2c_clients[1];
    char *tok;
    char clone[size+1];
    char *pclone = clone;
    char *last;
    int err;

    strcpy(clone, buf);

    tok = strsep((char**)&pclone, " ");
    if (tok == NULL) {
        return -EINVAL;
    }
    addr = (uint8_t)strtoul(tok, &last, 16);
    if (addr == 0 && tok == last) {
        return -EINVAL;
    }
    tok = strsep((char**)&pclone, " ");
    if (tok == NULL) {
        return -EINVAL;
    }
    value = (uint8_t)strtoul(tok, &last, 16);
    if (value == 0 && tok == last) {
        return -EINVAL;
    }
    err = i2c_smbus_write_byte_data(client, addr, value);
    if (err < 0)
        return err;

    return size;
}
struct device_attribute dev_attr_cpld2_setreg = __ATTR(setreg, 0200, NULL, cpld2_setreg_store);

static struct attribute *cpld2_attrs[] = {
    &dev_attr_cpld2_getreg.attr,
    &dev_attr_cpld2_scratch.attr,
    &dev_attr_cpld2_setreg.attr,
    NULL,
};

static struct attribute_group cpld2_attr_grp = {
    .attrs = cpld2_attrs,
};

static ssize_t fan_cpld_getreg_show(struct device *dev, struct device_attribute *attr, char *buf)
{
    // CPLD register is one byte
    uint8_t data;
    struct i2c_client *client = fpga_data->cpld_i2c_clients[2];
    data = i2c_smbus_read_byte_data(client, fpga_data->fan_cpld_read_addr);
    if(data < 0)
        return data;
    return sprintf(buf, "0x%2.2x\n", data);
}

static ssize_t fan_cpld_getreg_store(struct device *dev, struct device_attribute *attr, const char *buf, size_t size)
{
    // CPLD register is one byte
    uint8_t addr;
    char *last;
    addr = (uint8_t)strtoul(buf, &last, 16);
    if (addr == 0 && buf == last) {
        return -EINVAL;
    }
    fpga_data->fan_cpld_read_addr = addr;
    return size;
}
struct device_attribute dev_attr_fan_cpld_getreg = __ATTR(getreg, 0600, fan_cpld_getreg_show, fan_cpld_getreg_store);

static ssize_t fan_cpld_scratch_show(struct device *dev, struct device_attribute *attr, char *buf)
{
    // CPLD register is one byte
    int value;
    struct i2c_client *client = fpga_data->cpld_i2c_clients[2];

    value = i2c_smbus_read_byte_data(client, 0x04);
    if(value < 0)
        return value;
    return sprintf(buf, "0x%.2x\n", value);
}

static ssize_t fan_cpld_scratch_store(struct device *dev, struct device_attribute *attr, const char *buf, size_t size)
{
    // CPLD register is one byte
    u8 value;
    ssize_t status;
    struct i2c_client *client = fpga_data->cpld_i2c_clients[2];

    status = kstrtou8(buf, 0, &value);
    if(status != 0)
        return status;
    status = i2c_smbus_write_byte_data(client, 0x04, value);
    if(status == 0)
        status = size;
    return status;
}
struct device_attribute dev_attr_fan_cpld_scratch = __ATTR(scratch, 0600, fan_cpld_scratch_show, fan_cpld_scratch_store);


static ssize_t fan_cpld_setreg_store(struct device *dev, struct device_attribute *attr, const char *buf, size_t size)
{
    uint8_t addr, value;
    struct i2c_client *client = fpga_data->cpld_i2c_clients[2];
    char *tok;
    char clone[size+1];
    char *pclone = clone;
    char *last;
    int err;

    strcpy(clone, buf);

    tok = strsep((char**)&pclone, " ");
    if (tok == NULL) {
        return -EINVAL;
    }
    addr = (uint8_t)strtoul(tok, &last, 16);
    if (addr == 0 && tok == last) {
        return -EINVAL;
    }
    tok = strsep((char**)&pclone, " ");
    if (tok == NULL) {
        return -EINVAL;
    }
    value = (uint8_t)strtoul(tok, &last, 16);
    if (value == 0 && tok == last) {
        return -EINVAL;
    }
    err = i2c_smbus_write_byte_data(client, addr, value);
    if (err < 0)
        return err;

    return size;
}

struct device_attribute dev_attr_fan_cpld_setreg = __ATTR(setreg, 0200, NULL, fan_cpld_setreg_store);

static struct attribute *fan_cpld_attrs[] = {
    &dev_attr_fan_cpld_getreg.attr,
    &dev_attr_fan_cpld_scratch.attr,
    &dev_attr_fan_cpld_setreg.attr,
    NULL,
};

static struct attribute_group fan_cpld_attr_grp = {
    .attrs = fan_cpld_attrs,
};

/* QSFP/SFP+ attributes */
static ssize_t sfp_txfault_show(struct device *dev, struct device_attribute *attr, char *buf)
{
    u8 value = 0;
	uint8_t reg = 0;
    struct sff_device_data *dev_data = dev_get_drvdata(dev);
    unsigned int portid = dev_data->portid;
    
	struct i2c_client *client1 = fpga_data->cpld_i2c_clients[0];
	struct i2c_client *client2 = fpga_data->cpld_i2c_clients[1];

	if(portid > 0 && portid <=24)
	{
		reg = (0x19 + ( portid -1)/8);
		value = i2c_smbus_read_byte_data(client1, reg);
		if(value < 0)
        	return value;
	}
	else if(portid > 24 && portid <=48)
	{
		reg = (0x19 + ( portid -25)/8);
		value = i2c_smbus_read_byte_data(client2, reg);
		if(value < 0)
        	return value;
	}
	
    value = (value & (0x1 << ((portid - 1) % 8)));
    return sprintf(buf, "%d\n", (value ? 1 : 0));
}
DEVICE_ATTR_RO(sfp_txfault);

static ssize_t sfp_rxlos_show(struct device *dev, struct device_attribute *attr, char *buf)
{
    u8 value = 0;
	uint8_t reg = 0;
    struct sff_device_data *dev_data = dev_get_drvdata(dev);
    unsigned int portid = dev_data->portid;
    
	struct i2c_client *client1 = fpga_data->cpld_i2c_clients[0];
	struct i2c_client *client2 = fpga_data->cpld_i2c_clients[1];

	if(portid > 0 && portid <=24)
	{
		reg = (0x16 + ( portid -1)/8);
		value = i2c_smbus_read_byte_data(client1, reg);
		if(value < 0)
        	return value;
	}
	else if(portid > 24 && portid <=48)
	{
		reg = (0x16 + ( portid -25)/8);
		value = i2c_smbus_read_byte_data(client2, reg);
		if(value < 0)
        	return value;
	}
   value = (value & (0x1 << ((portid - 1) % 8)));
    return sprintf(buf, "%d\n", (value ? 1 : 0));
}
DEVICE_ATTR_RO(sfp_rxlos);

static ssize_t sfp_modabs_show(struct device *dev, struct device_attribute *attr, char *buf)
{
    u8 value = 0;
	uint8_t reg = 0;
    struct sff_device_data *dev_data = dev_get_drvdata(dev);
    unsigned int portid = dev_data->portid;
    
	struct i2c_client *client1 = fpga_data->cpld_i2c_clients[0];
	struct i2c_client *client2 = fpga_data->cpld_i2c_clients[1];

	if(portid > 0 && portid <=24)
	{
		reg = (0x16 + ( portid -1)/8);
		value = i2c_smbus_read_byte_data(client1, reg);
		if(value < 0)
        	return value;
	}
	else if(portid > 24 && portid <=48)
	{
		reg = (0x16 + ( portid -25)/8);
		value = i2c_smbus_read_byte_data(client2, reg);
		if(value < 0)
        	return value;
	}
	
    value = (value & (0x1 << ((portid - 1) % 8)));
    return sprintf(buf, "%d\n", (value ? 1 : 0));
}
DEVICE_ATTR_RO(sfp_modabs);

static ssize_t sfp_pwren_show(struct device *dev, struct device_attribute *attr, char *buf)
{
    u8 value = 0;
	uint8_t reg = 0;
    struct sff_device_data *dev_data = dev_get_drvdata(dev);
    unsigned int portid = dev_data->portid;
    
	struct i2c_client *client1 = fpga_data->cpld_i2c_clients[0];
	struct i2c_client *client2 = fpga_data->cpld_i2c_clients[1];

	if(portid > 0 && portid <=24)
	{
		reg = (0x0c + ( portid -1)/8);
		value = i2c_smbus_read_byte_data(client1, reg);
		if(value < 0)
        	return value;
	}
	else if(portid > 24 && portid <=48)
	{
		reg = (0x0c + ( portid -25)/8);
		value = i2c_smbus_read_byte_data(client2, reg);
		if(value < 0)
        	return value;
	}
	
    value = (value & (0x1 << ((portid - 1) % 8)));
    return sprintf(buf, "%d\n", (value ? 1 : 0));
}
DEVICE_ATTR_RO(sfp_pwren);

static ssize_t sfp_txdisable_show(struct device *dev, struct device_attribute *attr, char *buf)
{
    u8 value = 0;
	uint8_t reg = 0;
    struct sff_device_data *dev_data = dev_get_drvdata(dev);
    unsigned int portid = dev_data->portid;
    
	struct i2c_client *client1 = fpga_data->cpld_i2c_clients[0];
	struct i2c_client *client2 = fpga_data->cpld_i2c_clients[1];

	if(portid > 0 && portid <=24)
	{
		reg = (0x1c + ( portid -1)/8);
		value = i2c_smbus_read_byte_data(client1, reg);
		if(value < 0)
        	return value;
	}
	else if(portid > 24 && portid <=48)
	{
		reg = (0x1c + ( portid -25)/8);
		value = i2c_smbus_read_byte_data(client2, reg);
		if(value < 0)
        	return value;
	}
	printk(KERN_INFO "before portid:%d value:0x%x\n", portid, value);
	value = (value & (0x1 << ((portid - 1) % 8)));
	printk(KERN_INFO "after portid:%d value:0x%x\n", portid, value);
    return sprintf(buf, "%d\n", (value ? 1 : 0));
}

static ssize_t sfp_txdisable_store(struct device *dev, struct device_attribute *attr, const char *buf, size_t size)
{
	int ret = 0;
    ssize_t status;
    long value;
    u8 data = 0, reg = 0;
    struct sff_device_data *dev_data = dev_get_drvdata(dev);
    unsigned int portid = dev_data->portid;
	struct i2c_client *client1 = fpga_data->cpld_i2c_clients[0];
	struct i2c_client *client2 = fpga_data->cpld_i2c_clients[1];
	struct i2c_client *client = NULL;
	
    status = kstrtol(buf, 0, &value);
    if (status == 0) {
        // check if value is 0 clear
        if(portid > 0 && portid <=24)
		{
			reg = (0x1c + ( portid -1)/8);
			client = client1;
			data = i2c_smbus_read_byte_data(client1, reg);
			if(data < 0)
		    	return data;
		}
		else if(portid > 24 && portid <=48)
		{
			reg = (0x1c + ( portid -25)/8);
			client = client2;
			data = i2c_smbus_read_byte_data(client2, reg);
			if(data < 0)
		    	return data;
		}
		
        if (!value)
            data = data & ~((u8)0x1 << ((portid - 1) % 8));
        else
            data = data | ((u8)0x1 << ((portid - 1) % 8));
		
		ret = i2c_smbus_write_byte_data(client, reg, data);
	    if (ret < 0)
	        return ret;
		
        status = size;
    }
    return status;
}
DEVICE_ATTR_RW(sfp_txdisable);

static ssize_t qsfp_lpmode_show(struct device *dev, struct device_attribute *attr, char *buf)
{
    u8 data = 0, reg_addr = 0;
    struct sff_device_data *dev_data = dev_get_drvdata(dev);
    unsigned int portid = dev_data->portid;
    struct i2c_client *client1 = fpga_data->cpld_i2c_clients[0];
	struct i2c_client *client2 = fpga_data->cpld_i2c_clients[1];

    if(portid >= 1 && portid <= 16)
	{
        reg_addr = (portid <= 8) ? LPMOD_CPLD1_1_8 : LPMOD_CPLD1_9_16;
		data = i2c_smbus_read_byte_data(client1, reg_addr);
		if(data < 0)
        	return data;
	}
	else if(portid >=17 && portid <= 32)
	{
        reg_addr = (portid <= 24) ? LPMOD_CPLD2_17_24 : LPMOD_CPLD2_25_32;
		data = i2c_smbus_read_byte_data(client2, reg_addr);
		if(data < 0)
        	return data;
	}

    printk(KERN_INFO "before portid:%d value:0x%x\n", portid, data);
    data = (data & (0x1 << ((portid - 1) % 8)));
    printk(KERN_INFO "before portid:%d value:0x%x\n", portid, data);
    return sprintf(buf, "%d\n", (data ? 1 : 0));
}

static ssize_t qsfp_lpmode_store(struct device *dev, struct device_attribute *attr, const char *buf, size_t size)
{
	int ret = 0;
    ssize_t status;
    long value = 0;
    u8 data = 0, reg_addr = 0;
    struct sff_device_data *dev_data = dev_get_drvdata(dev);
    unsigned int portid = dev_data->portid;
	struct i2c_client *client1 = fpga_data->cpld_i2c_clients[0];
	struct i2c_client *client2 = fpga_data->cpld_i2c_clients[1];
	struct i2c_client *client = NULL;
	
    status = kstrtol(buf, 0, &value);
    if (status == 0) {
        // if value is 0, disable the lpmode		
        if(portid >= 1 && portid <= 16)
        {
            client = client1;
            reg_addr = (portid <= 8) ? LPMOD_CPLD1_1_8 : LPMOD_CPLD1_9_16;
            data = i2c_smbus_read_byte_data(client1, reg_addr);
            if(data < 0)
                return data;
        }
        else if(portid >=17 && portid <= 32)
        {
            client = client2;
            reg_addr = (portid <= 24) ? LPMOD_CPLD2_17_24 : LPMOD_CPLD2_25_32;
            data = i2c_smbus_read_byte_data(client2, reg_addr);
            if(data < 0)
                return data;
        }

        if (!value)
            data = data | ((u8)0x1 << ((portid - 1) % 8));
        else
            data = data & ~((u8)0x1 << ((portid - 1) % 8));
		
        ret = i2c_smbus_write_byte_data(client, reg_addr, data);
	    if (ret < 0)
	        return ret;
        status = size;
    }
    return status;
}
DEVICE_ATTR_RW(qsfp_lpmode);

static ssize_t qsfp_reset_show(struct device *dev, struct device_attribute *attr, char *buf)
{
    u8 data = 0, reg_addr = 0;
    struct sff_device_data *dev_data = dev_get_drvdata(dev);
    unsigned int portid = dev_data->portid;
    struct i2c_client *client1 = fpga_data->cpld_i2c_clients[0];
	struct i2c_client *client2 = fpga_data->cpld_i2c_clients[1];

    if(portid >= 1 && portid <= 16)
	{
        reg_addr = (portid <= 8) ? RESET_CPLD1_1_8 : RESET_CPLD1_9_16;
		data = i2c_smbus_read_byte_data(client1, reg_addr);
		if(data < 0)
        	return data;
	}
	else if(portid >=17 && portid <= 32)
	{
        reg_addr = (portid <= 24) ? RESET_CPLD2_17_24 : RESET_CPLD2_25_32;
		data = i2c_smbus_read_byte_data(client2, reg_addr);
		if(data < 0)
        	return data;
	}

	data = (data & (0x1 << ((portid - 1) % 8)));
    return sprintf(buf, "%d\n", (data ? 1 : 0));
}

static ssize_t qsfp_reset_store(struct device *dev, struct device_attribute *attr, const char *buf, size_t size)
{
    int ret;
    ssize_t status;
    long value;
    u8 data = 0, reg_addr = 0;
    struct sff_device_data *dev_data = dev_get_drvdata(dev);
    unsigned int portid = dev_data->portid;
	struct i2c_client *client1 = fpga_data->cpld_i2c_clients[0];
	struct i2c_client *client2 = fpga_data->cpld_i2c_clients[1];
	struct i2c_client *client = NULL;
	
    status = kstrtol(buf, 0, &value);
    if (status == 0) {
        // if value is 0, disable the reset
        if(portid >= 1 && portid <= 16)
        {
            client = client1;
            reg_addr = (portid <= 8) ? RESET_CPLD1_1_8 : RESET_CPLD1_9_16;
            data = i2c_smbus_read_byte_data(client1, reg_addr);
            if(data < 0)
                return data;
        }
        else if(portid >=17 && portid <= 32)
        {
            client = client2;
            reg_addr = (portid <= 24) ? RESET_CPLD2_17_24 : RESET_CPLD2_25_32;
            data = i2c_smbus_read_byte_data(client2, reg_addr);
            if(data < 0)
                return data;
        }

        if (!value)
            data = data | ((u8)0x1 << ((portid - 1) % 8));
        else
            data = data & ~((u8)0x1 << ((portid - 1) % 8));
		
        ret = i2c_smbus_write_byte_data(client, reg_addr, data);
	    if (ret < 0)
	        return ret;
        status = size;
    }
	
    return status;
}
DEVICE_ATTR_RW(qsfp_reset);

static ssize_t qsfp_modprs_irq_show(struct device *dev, struct device_attribute *attr, char *buf)
{
    u8 data = 0, reg_addr = 0;
    struct sff_device_data *dev_data = dev_get_drvdata(dev);
    unsigned int portid = dev_data->portid;
    struct i2c_client *client1 = fpga_data->cpld_i2c_clients[0];
	struct i2c_client *client2 = fpga_data->cpld_i2c_clients[1];

	if(portid >= 1 && portid <= 16)
	{
        reg_addr = (portid <= 8) ? MODPRS_IRQ_CPLD1_1_8 : MODPRS_IRQ_CPLD1_9_16;
		data = i2c_smbus_read_byte_data(client1, reg_addr);
		if(data < 0)
        	return data;
	}
	else if(portid >=17 && portid <= 32)
	{
        reg_addr = (portid <= 24) ? MODPRS_IRQ_CPLD2_17_24 : MODPRS_IRQ_CPLD2_25_32;
		data = i2c_smbus_read_byte_data(client2, reg_addr);
		if(data < 0)
        	return data;
	}
	data = (data & (0x1 << ((portid - 1) % 8)));
    return sprintf(buf, "%d\n", (data ? 1 : 0));
}
DEVICE_ATTR_RO(qsfp_modprs_irq);

static ssize_t qsfp_modprs_show(struct device *dev, struct device_attribute *attr, char *buf)
{
    u8 data = 0, reg_addr = 0;
    struct sff_device_data *dev_data = dev_get_drvdata(dev);
    unsigned int portid = dev_data->portid;
    struct i2c_client *client1 = fpga_data->cpld_i2c_clients[0];
	struct i2c_client *client2 = fpga_data->cpld_i2c_clients[1];

	if(portid >= 1 && portid <= 16)
	{
        reg_addr = (portid <= 8) ? MODPRS_CPLD1_1_8 : MODPRS_CPLD1_9_16;
		data = i2c_smbus_read_byte_data(client1, reg_addr);
		if(data < 0)
        	return data;
	}
	else if(portid >=17 && portid <= 32)
	{
        reg_addr = (portid <= 24) ? MODPRS_CPLD2_17_24 : MODPRS_CPLD2_25_32;
		data = i2c_smbus_read_byte_data(client2, reg_addr);
		if(data < 0)
        	return data;
	}
	data = (data & (0x1 << ((portid - 1) % 8)));
    return sprintf(buf, "%d\n", (data ? 1 : 0));
}
DEVICE_ATTR_RO(qsfp_modprs);

#if 0
static ssize_t qsfp_pwren_show(struct device *dev, struct device_attribute *attr, char *buf)
{
    u8 data = 0;
    struct sff_device_data *dev_data = dev_get_drvdata(dev);
    unsigned int portid = dev_data->portid;
    struct i2c_client *client1 = fpga_data->cpld_i2c_clients[0];
	struct i2c_client *client2 = fpga_data->cpld_i2c_clients[1];

	if(portid > 48 && portid <= 52)
	{
		data = i2c_smbus_read_byte_data(client1, 0x0B);
		if(data < 0)
        	return data;
	}
	else if(portid > 52 && portid <= 56)
	{
		data = i2c_smbus_read_byte_data(client2, 0x0B);
		if(data < 0)
        	return data;
	}
	data = (data & (0x1 << ((portid - 1) % 8)));
    return sprintf(buf, "%d\n", (data ? 1 : 0));
}
DEVICE_ATTR_RO(qsfp_pwren);
#endif

static struct attribute *sff_attrs[] = {
    &dev_attr_sfp_txfault.attr,
    &dev_attr_sfp_rxlos.attr,
    &dev_attr_sfp_modabs.attr,
    &dev_attr_sfp_txdisable.attr,
    &dev_attr_sfp_pwren.attr,
    NULL,
};

static struct attribute *qsfp_attrs[] = {
    &dev_attr_qsfp_modprs_irq.attr,
    &dev_attr_qsfp_lpmode.attr,
    &dev_attr_qsfp_reset.attr,
    &dev_attr_qsfp_modprs.attr,
    //&dev_attr_qsfp_pwren.attr,
    NULL,
};


static struct attribute_group sff_attr_grp = {
    .attrs = sff_attrs,
};

static const struct attribute_group *sff_attr_grps[] = {
    &sff_attr_grp,
    NULL
};

static struct attribute_group qsfp_attr_grp = {
    .attrs = qsfp_attrs,
};

static const struct attribute_group *qsfp_attr_grps[] = {
    &qsfp_attr_grp,
    NULL
};

static ssize_t port_led_mode_show(struct device *dev, struct device_attribute *attr, char *buf)
{
    // value can be "nomal", "test"
    int led_mode_1, led_mode_2;
    struct i2c_client *cpld1 = fpga_data->cpld_i2c_clients[0];
    struct i2c_client *cpld2 = fpga_data->cpld_i2c_clients[1];

    led_mode_1 = i2c_smbus_read_byte_data(cpld1, 0x09);
    if (led_mode_1 < 0)
        return led_mode_1;

    led_mode_2 = i2c_smbus_read_byte_data(cpld2, 0x09);
    if (led_mode_2 < 0)
        return led_mode_2;

    return sprintf(buf, "%s %s\n",
                   led_mode_1 ? "test" : "normal",
                   led_mode_2 ? "test" : "normal");
}
static ssize_t port_led_mode_store(struct device *dev, struct device_attribute *attr, const char *buf, size_t size)
{
    int status;
    u8 led_mode_1;
    struct i2c_client *cpld1 = fpga_data->cpld_i2c_clients[0];
    struct i2c_client *cpld2 = fpga_data->cpld_i2c_clients[1];

    if (sysfs_streq(buf, "test")) {
        led_mode_1 = 0x01;
    } else if (sysfs_streq(buf, "normal")) {
        led_mode_1 = 0x00;
    } else {
        return -EINVAL;
    }

    status = i2c_smbus_write_byte_data(cpld1, 0x09, led_mode_1);
    if ( status < 0 )
        return status;

    status = i2c_smbus_write_byte_data(cpld2, 0x09, led_mode_1);
    if ( status < 0 )
        return status;

    return size;
}
DEVICE_ATTR_RW(port_led_mode);

// Only work when port_led_mode set to 1
static ssize_t port_led_color_show(struct device *dev, struct device_attribute *attr, char *buf)
{
    // value can be R/G/B/C/M/Y/W/OFF
    int led_color1, led_color2;

    struct i2c_client *cpld1 = fpga_data->cpld_i2c_clients[0];
    struct i2c_client *cpld2 = fpga_data->cpld_i2c_clients[1];

    led_color1 = i2c_smbus_read_byte_data(cpld1, 0x0A);
    if (led_color1 < 0)
        return led_color1;

    led_color2 = i2c_smbus_read_byte_data(cpld2, 0x0A);
    if (led_color2 < 0)
        return led_color2;

    return sprintf(buf, "CPLD1 %s CPLD2 %s\n",
                   led_color1 == 0x07 ? "off" : led_color1 == 0x06 ? "off" : led_color1 == 0x05 ?  "off" : led_color1 == 0x04 ? 
                    "off" : led_color1 == 0x03 ? "off" : led_color1 == 0x02 ?  "amber" : led_color1 == 0x01 ?  "green" : "off",
                   led_color2 == 0x07 ? "off" : led_color2 == 0x06 ? "cyan" : led_color2 == 0x05 ?  "magenta" : led_color2 == 0x04 ? 
                    "blue" : led_color2 == 0x03 ? "red" : led_color2 == 0x02 ?  "green" : led_color2 == 0x01 ?  "amber" : "white");
}

static ssize_t port_led_color_store(struct device *dev, struct device_attribute *attr, const char *buf, size_t size)
{
    ssize_t status;
    u8 led_color1;
    u8 led_color2;

    struct i2c_client *cpld1 = fpga_data->cpld_i2c_clients[0];
    struct i2c_client *cpld2 = fpga_data->cpld_i2c_clients[1];

    if (sysfs_streq(buf, "off")) {
        led_color1 = 0x07;
        led_color2 = 0x07;
    } else if (sysfs_streq(buf, "cyan")) {
        led_color1 = 0x07;
        led_color2 = 0x06;
    } else if (sysfs_streq(buf, "magenta")) {
        led_color1 = 0x07;
        led_color2 = 0x05;
    } else if (sysfs_streq(buf, "blue")) {
        led_color1 = 0x07;
        led_color2 = 0x04;
    } else if (sysfs_streq(buf, "red")) {
        led_color1 = 0x07;
        led_color2 = 0x03;
    } else if (sysfs_streq(buf, "green")) {
        led_color1 = 0x01;
        led_color2 = 0x02;
    } else if (sysfs_streq(buf, "amber")) {
        led_color1 = 0x02;
        led_color2 = 0x01;
    } else if (sysfs_streq(buf, "white")) {
        led_color1 = 0x07;
        led_color2 = 0x00;
    } else {
        status = -EINVAL;
        return status;
    }

    status = i2c_smbus_write_byte_data(cpld1, 0x0A, led_color1);
    if (status < 0)
        return status;

    status = i2c_smbus_write_byte_data(cpld2, 0x0A, led_color2);
    if (status < 0)
        return status;

    return size;
}
DEVICE_ATTR_RW(port_led_color);

static struct attribute *sff_led_test[] = {
    &dev_attr_port_led_mode.attr,
    &dev_attr_port_led_color.attr,
    NULL,
};

static struct attribute_group sff_led_test_grp = {
    .attrs = sff_led_test,
};

static struct device * switchboard_sff_init(int portid) 
{
    struct sff_device_data *new_data;
    struct device *new_device;

    new_data = kzalloc(sizeof(*new_data), GFP_KERNEL);
    if (!new_data) {
        printk(KERN_ALERT "Cannot alloc sff device data @port%d", portid);
        return NULL;
    }
    /* The QSFP port ID start from 1 */
    new_data->portid = portid + 1;
    //printk(KERN_INFO "Port number:%d\n", new_data->portid);
    new_data->port_type = fpga_i2c_bus_dev[portid].port_type;
    {
		new_device = device_create_with_groups(fpgafwclass, 
        	                                   sff_dev, 
        	                                   MKDEV(0, 0), 
        	                                   new_data, 
        	                                   qsfp_attr_grps, 
          	                                  "%s", 
        	                                   fpga_i2c_bus_dev[portid].calling_name);
    }
    if (IS_ERR(new_device)) {
        printk(KERN_ALERT "Cannot create sff device @port%d", portid);
        kfree(new_data);
        return NULL;
    }
    return new_device;
}

static void switchboard_dev_release( struct device * dev)
{
    return;
}

static struct platform_device switchboard_dev = {
    .name           = DRIVER_NAME,
    .id             = -1,
    .num_resources  = 0,
    .dev = {
        .release = switchboard_dev_release,
    }
};

static int switchboard_drv_probe(struct platform_device *pdev)
{
    int ret = 0;
    int portid_count;
	struct i2c_adapter *cpld_bus_adap1;
    struct i2c_adapter *cpld_bus_adap2;
	struct i2c_adapter *cpld_bus_adap7;
    struct i2c_client *cpld1_client;
    struct i2c_client *cpld2_client;
	struct i2c_client *fan_cpld_client;

    struct pci_dev *pci_dev = pci_get_device(PCI_VENDOR_ID_XILINX, 
                                             FPGA_DEVICE_ID, 
                                             NULL);
    if (pci_dev)
    {
        fpga_pci_probe(pci_dev);
        pci_dev_put(pci_dev);
    } 
    else 
    {
        ret = -ENODEV;
        goto err_exit;
    }

    fpga_data = devm_kzalloc(&pdev->dev, sizeof(struct switchboard_fpga_data),
                             GFP_KERNEL);
    if (!fpga_data)
    {
        ret = -ENOMEM;
        goto err_exit;
    }

    /* The device class need to be instantiated before this function called */
    BUG_ON(fpgafwclass == NULL);

	cpld_bus_adap1 = i2c_get_adapter(SWITCH_CPLD_ADAP_1);
    if (!cpld_bus_adap1)
    {
        dev_err(&pdev->dev, "cannot get switch board I2C adapter i2c-%d\n",SWITCH_CPLD_ADAP_1);
        ret = PTR_ERR(cpld_bus_adap1);
        goto err_exit;
    }

    cpld_bus_adap2 = i2c_get_adapter(SWITCH_CPLD_ADAP_2);
    if (!cpld_bus_adap2)
    {
        dev_err(&pdev->dev, "cannot get switch board I2C adapter i2c-%d\n",SWITCH_CPLD_ADAP_2);
        ret = PTR_ERR(cpld_bus_adap2);
        goto err_free_adap1;
    }

	cpld_bus_adap7 = i2c_get_adapter(SWITCH_CPLD_ADAP_7);
    if (!cpld_bus_adap7)
    {
        dev_err(&pdev->dev, "cannot get switch board I2C adapter i2c-%d\n",SWITCH_CPLD_ADAP_7);
        ret = PTR_ERR(cpld_bus_adap7);
        goto err_free_adap2;
    }

    //cpld1_client = i2c_new_dummy(cpld_bus_adap2, CPLD1_SLAVE_ADDR);
    cpld1_client = i2c_new_dummy_device(cpld_bus_adap2, CPLD1_SLAVE_ADDR);
    i2c_put_adapter(cpld_bus_adap2);
    if (!cpld1_client){
        dev_err(&pdev->dev, "cannot create i2c dummy device of CPLD1\n");
        ret = -ENODEV;
        goto err_free_adap7;
    }

    //cpld2_client = i2c_new_dummy(cpld_bus_adap7, CPLD2_SLAVE_ADDR);
    cpld2_client = i2c_new_dummy_device(cpld_bus_adap7, CPLD2_SLAVE_ADDR);
    
    i2c_put_adapter(cpld_bus_adap7);

    if (!cpld2_client){
        dev_err(&pdev->dev, "cannot create i2c dummy device of CPLD2\n");
        ret = ENODEV;
        goto err_free_cli_clpd1;
    }

    //fan_cpld_client = i2c_new_dummy(cpld_bus_adap1, FANCPLD_SLAVE_ADDR);
    fan_cpld_client = i2c_new_dummy_device(cpld_bus_adap1, FANCPLD_SLAVE_ADDR);

    i2c_put_adapter(cpld_bus_adap1);

    if (!fan_cpld_client){
        dev_err(&pdev->dev, "cannot create i2c dummy device of Fan CPLD\n");
        ret = ENODEV;
        goto err_free_cli_clpd2;
    }

    fpga = kobject_create_and_add("FPGA", &pdev->dev.kobj);
    if (!fpga) {
        ret = -ENOMEM;
        goto err_free_cli_fancpld;
    }

    ret = sysfs_create_group(fpga, &fpga_attr_grp);
    if (ret != 0) {
        printk(KERN_ERR "Cannot create FPGA sysfs attributes\n");
        goto err_remove_fpga;
    }

    cpld1 = kobject_create_and_add("CPLD1", &pdev->dev.kobj);
    if (!cpld1) {
        ret = -ENOMEM;
        goto err_remove_grp_fpga;
    }
    ret = sysfs_create_group(cpld1, &cpld1_attr_grp);
    if (ret != 0) {
        printk(KERN_ERR "Cannot create CPLD1 sysfs attributes\n");
        goto err_remove_cpld1;
    }

    cpld2 = kobject_create_and_add("CPLD2", &pdev->dev.kobj);
    if (!cpld2) {
        ret = -ENOMEM;
        goto err_remove_grp_cpld1;
    }
    ret = sysfs_create_group(cpld2, &cpld2_attr_grp);
    if (ret != 0) 
    {
        printk(KERN_ERR "Cannot create CPLD2 sysfs attributes\n");
        goto err_remove_cpld2;
    }

	fan_cpld = kobject_create_and_add("FCPLD", &pdev->dev.kobj);
    if (!fan_cpld) {
        ret = -ENOMEM;
        goto err_remove_grp_fan_cpld;
    }
    ret = sysfs_create_group(fan_cpld, &fan_cpld_attr_grp);
    if (ret != 0) 
    {
        printk(KERN_ERR "Cannot create FCPLD sysfs attributes\n");
        goto err_remove_fan_cpld;
    }

    sff_dev = device_create(fpgafwclass, NULL, MKDEV(0, 0), NULL, "sff_device");
    if (IS_ERR(sff_dev))
    {
        ret = PTR_ERR(sff_dev);
        goto err_remove_grp_fan_cpld;
    }

    ret = sysfs_create_group(&sff_dev->kobj, &sff_led_test_grp);
    if (ret != 0) {
        goto err_remove_sff;
    }

    ret = sysfs_create_link(&pdev->dev.kobj, &sff_dev->kobj, "SFF");
    if (ret != 0) {
        goto err_remove_grp_sff;
    }

    /* Init SFF devices */
    for (portid_count = 0; portid_count < SFF_PORT_TOTAL; portid_count++) {
        fpga_data->sff_devices[portid_count] = switchboard_sff_init(portid_count);
    }

    // Set default read address to VERSION
    fpga_data->fpga_read_addr = fpga_dev.data_base_addr + FPGA_VERSION;
    fpga_data->cpld1_read_addr = 0x00;
    fpga_data->cpld2_read_addr = 0x00;
    fpga_data->cpld_i2c_clients[0] = cpld1_client;
    fpga_data->cpld_i2c_clients[1] = cpld2_client;
	fpga_data->cpld_i2c_clients[2] = fan_cpld_client;
    mutex_init(&fpga_data->fpga_lock);

return 0;

err_remove_grp_sff:
    sysfs_remove_group(&sff_dev->kobj, &sff_led_test_grp);

err_remove_sff:
    device_destroy(fpgafwclass, MKDEV(0, 0));

err_remove_grp_fan_cpld:
    sysfs_remove_group(fan_cpld, &fan_cpld_attr_grp);

err_remove_fan_cpld:
    kobject_put(fan_cpld);	

err_remove_grp_cpld2:
    sysfs_remove_group(cpld2, &cpld2_attr_grp);

err_remove_cpld2:
    kobject_put(cpld2);

err_remove_grp_cpld1:
    sysfs_remove_group(cpld1, &cpld1_attr_grp);

err_remove_cpld1:
    kobject_put(cpld1);

err_remove_grp_fpga:
    sysfs_remove_group(fpga, &fpga_attr_grp);

err_remove_fpga:
    kobject_put(fpga);

err_free_cli_fancpld:
	i2c_unregister_device(fan_cpld_client);

err_free_cli_clpd2:
    i2c_unregister_device(cpld2_client);

err_free_cli_clpd1:
    i2c_unregister_device(cpld1_client);

err_free_adap7:
	i2c_put_adapter(cpld_bus_adap7);

err_free_adap2:
    i2c_put_adapter(cpld_bus_adap2);
	
err_free_adap1:
    i2c_put_adapter(cpld_bus_adap1);
	
err_exit:
    return ret;

}

/* move this on top of platform_probe() */
static int fpga_pci_probe(struct pci_dev *pdev)
{
    int err;
    struct device *dev = &pdev->dev;
    uint32_t fpga_version;

    /* Skip the reqions request and mmap the resource */ 
    /* bar0: data mmio region */
    fpga_dev.data_mmio_start = pci_resource_start(pdev, FPGA_MMIO_BAR);
    fpga_dev.data_mmio_len = pci_resource_len(pdev, FPGA_MMIO_BAR);
    //fpga_dev.data_base_addr = ioremap_nocache(fpga_dev.data_mmio_start, 
    //                                            fpga_dev.data_mmio_len);
    fpga_dev.data_base_addr = ioremap(fpga_dev.data_mmio_start, 
                                                fpga_dev.data_mmio_len);
    if (!fpga_dev.data_base_addr) {
        dev_err(dev, "cannot iomap region of size %lu\n",
                (unsigned long)fpga_dev.data_mmio_len);
        err = PTR_ERR(fpga_dev.data_base_addr);
        goto err_exit;
    }
	
#if 0    
    dev_info(dev, "data_mmio iomap base = 0x%lx \n",
             (unsigned long)fpga_dev.data_base_addr);
    dev_info(dev, "data_mmio_start = 0x%lx data_mmio_len = %lu\n",
             (unsigned long)fpga_dev.data_mmio_start,
             (unsigned long)fpga_dev.data_mmio_len);

    printk(KERN_INFO "FPGA PCIe driver probe OK.\n");
    printk(KERN_INFO "FPGA ioremap registers of size %lu\n", 
            (unsigned long)fpga_dev.data_mmio_len);
    printk(KERN_INFO "FPGA Virtual BAR %d at %8.8lx - %8.8lx\n", 
            FPGA_MMIO_BAR,
            (unsigned long)fpga_dev.data_base_addr,
            (unsigned long)(fpga_dev.data_base_addr + fpga_dev.data_mmio_len));
    printk(KERN_INFO "");
#endif

    fpga_version = ioread32(fpga_dev.data_base_addr);
    printk(KERN_INFO "FPGA VERSION : %8.8x\n", fpga_version);

    fpgafwclass = class_create(THIS_MODULE, CLASS_NAME);
    if (IS_ERR(fpgafwclass)) {
        printk(KERN_ALERT "Failed to register device class\n");
        err = PTR_ERR(fpgafwclass);
        goto mem_unmap;
    }
    return 0;

mem_unmap:
    iounmap(fpga_dev.data_base_addr);
err_exit:
    return err;
}

static void fpga_pci_remove(void)
{
    iounmap(fpga_dev.data_base_addr);
    class_unregister(fpgafwclass);
    class_destroy(fpgafwclass);
};

static int switchboard_drv_remove(struct platform_device *pdev)
{
    int portid_count;
    struct sff_device_data *rem_data;
    struct i2c_client *rem_cli;

    rem_cli = fpga_data->cpld_i2c_clients[0];
    if(rem_cli)
        i2c_unregister_device(rem_cli);

    rem_cli = fpga_data->cpld_i2c_clients[1];
    if(rem_cli)
    	i2c_unregister_device(rem_cli);

	rem_cli = fpga_data->cpld_i2c_clients[2];
    if(rem_cli)
    	i2c_unregister_device(rem_cli);

    for (portid_count = 0; portid_count < SFF_PORT_TOTAL; portid_count++) {
        if (fpga_data->sff_devices[portid_count] != NULL) {
            rem_data = dev_get_drvdata(fpga_data->sff_devices[portid_count]);
            device_unregister(fpga_data->sff_devices[portid_count]);
            put_device(fpga_data->sff_devices[portid_count]);
            kfree(rem_data);
        }
    }

    sysfs_remove_group(fpga, &fpga_attr_grp);
    sysfs_remove_group(cpld1, &cpld1_attr_grp);
    sysfs_remove_group(cpld2, &cpld2_attr_grp);
	sysfs_remove_group(fan_cpld, &fan_cpld_attr_grp);
    sysfs_remove_group(&sff_dev->kobj, &sff_led_test_grp);
    kobject_put(fpga);
    kobject_put(cpld1);
    kobject_put(cpld2);
	kobject_put(fan_cpld);
    device_destroy(fpgafwclass, MKDEV(0, 0));
    fpga_pci_remove();
    return 0;
}

static struct platform_driver switchboard_drv = {
    .probe  = switchboard_drv_probe,
    .remove = __exit_p(switchboard_drv_remove),
    .driver = {
        .name   = DRIVER_NAME,
    },
};

static int __init  switchboard_init(void)
{
    platform_device_register(&switchboard_dev);
    platform_driver_register(&switchboard_drv);
	printk(KERN_INFO "%s: version %s loaded successfully\n", MOD_NAME, MOD_VERSION);
	return 0;
}

static void __exit switchboard_exit(void)
{
    platform_driver_unregister(&switchboard_drv);
    platform_device_unregister(&switchboard_dev);
	printk(KERN_INFO "%s: unloaded successfully\n", DRIVER_NAME);
}

module_init(switchboard_init);
module_exit(switchboard_exit);

MODULE_AUTHOR("Huaqin Technology Co.,Ltd.");
MODULE_DESCRIPTION("Hua Qin SWITCHBOARD");
MODULE_VERSION(MOD_VERSION);
MODULE_LICENSE("GPL");

