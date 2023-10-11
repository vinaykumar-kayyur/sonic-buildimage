/*================================================================
*   Copyright (C) 2020 Huaqin Technology Co.,Ltd.
*                 All rights reserved.
*   Building 10, No, 399, Keyuan Road, Pudong, Shanghai
*   
*   
*   File Name   : cpld_hq.c
*   Author      : carl.wang (carl.wang@huaqin.com)
*   Created Time: Thu Dec 14 16:12:51 2020
*   Description : cpld_hq.c -- the CPLD driver is for all CPLD.
*   The driver implement sysfs to access CPLD registers via LPC bus.
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
#include <linux/platform_device.h>
#include <linux/types.h>
#include <uapi/linux/stat.h>
#include <linux/string.h>

#define CPLD_DRIVER_NAME 	"sys_cpld"
#define CPLD_DRIVER_VER		"0.0.1"		
/**
 * CPLD register address for read and write.
 */
/*
 * Base CPLD:0xA100 ~ 0xA1DF
 * COMe CPLD:0xA1E0 ~ 0xA1FF
 * */
#define BASE_CPLD_ADDR 		0xA100
#define COME_CPLD_ADDR		0xA1E0
#define VERSION_ADDR 		0xA100

#define BASE_PCB_VER_ADDR	0xA100
#define BASE_H_VER_ADDR		0xA101
#define BASE_M_VER_ADDR		0xA102
#define BASE_L_VER_ADDR		0xA103
#define BASE_SCRATCH_ADDR	0xA104

#define COME_PCB_VER_ADDR	0xA1E0
#define COME_H_VER_ADDR		0xA1E1
#define COME_M_VER_ADDR		0xA1E2
#define COME_L_VER_ADDR		0xA1E3
#define COME_SCRATCH_ADDR	0xA1E4

#define CPLD_REGISTER_SIZE 	0xFF

struct cpld_hq_data {
    struct mutex       cpld_lock;
    uint16_t           read_addr;
	uint16_t		   base_addr;
};

struct cpld_hq_data *cpld_data;

static ssize_t get_cpld_reg_address(struct device *dev, struct device_attribute *attr, char *buf)
{
    int len = 0;
    // CPLD register is one byte
    mutex_lock(&cpld_data->cpld_lock);
    len = sprintf(buf, "0x%2.2x\n",inb(cpld_data->read_addr));
    mutex_unlock(&cpld_data->cpld_lock);
    return len;
}

/**
 * Store the register address
 * @param  buf     address wanted to be read value of
 * @return         number of bytes stored, or an error code
 */
static ssize_t set_cpld_reg_address(struct device *dev, struct device_attribute *devattr,
                                    const char *buf, size_t count)
{
    uint32_t addr;
    char *last;

	mutex_lock(&cpld_data->cpld_lock);
    addr = (uint32_t)strtoul(buf, &last, 16);
    if (addr == 0 && buf == last) {
        return -EINVAL;
    }
	
    cpld_data->read_addr = cpld_data->base_addr + addr;
	mutex_unlock(&cpld_data->cpld_lock);
    return count;
}

static DEVICE_ATTR( getreg, 0600, get_cpld_reg_address, set_cpld_reg_address);

static ssize_t setreg_store(struct device *dev, struct device_attribute *devattr,
                const char *buf, size_t count)
{
    // CPLD register is one byte
    uint16_t addr;
    uint8_t value;
    char *tok;
    char clone[count+1];
    char *pclone = clone;
    char *last;

    strcpy(clone, buf);

    mutex_lock(&cpld_data->cpld_lock);
    tok = strsep((char**)&pclone, " ");
    if(tok == NULL){
        mutex_unlock(&cpld_data->cpld_lock);
        return -EINVAL;
    }
    addr = (uint16_t)strtoul(tok, &last,16);
    if(addr == 0 && tok == last){
        mutex_unlock(&cpld_data->cpld_lock);
        return -EINVAL;
    }

    tok = strsep((char**)&pclone, " ");
    if(tok == NULL){
        mutex_unlock(&cpld_data->cpld_lock);
        return -EINVAL;
    }
    value = (uint8_t)strtoul(tok, &last,16);
    if(value == 0 && tok == last){
        mutex_unlock(&cpld_data->cpld_lock);
        return -EINVAL;
    }

    outb(value, cpld_data->base_addr + addr);
    mutex_unlock(&cpld_data->cpld_lock);
    return count;
}
//static DEVICE_ATTR_WO(setreg);
static DEVICE_ATTR( setreg, 0200, NULL , setreg_store);	
/**
 * Read all CPLD register in binary mode.
 * @return number of byte read.
 */
static ssize_t dump_read(struct file *filp, struct kobject *kobj,
                struct bin_attribute *attr, char *buf,
                loff_t off, size_t count)
{
    unsigned long i = 0;
    ssize_t status;

    mutex_lock(&cpld_data->cpld_lock);
    begin:
        if(i < count){
            buf[i++] = inb(VERSION_ADDR + off);
            off++;
            msleep(1);
            goto begin;
        }
        status = count;
    exit:
        mutex_unlock(&cpld_data->cpld_lock);
    return status;
}
				
static BIN_ATTR_RO(dump, CPLD_REGISTER_SIZE);

static struct attribute *cpld_hq_attrs[] = {
    &dev_attr_getreg.attr,
    &dev_attr_setreg.attr,
    NULL,
};

static struct bin_attribute *cpld_hq_bin_attrs[] = {
    &bin_attr_dump,
    NULL,
};

static struct attribute_group cpld_hq_attrs_group = {
    .attrs = cpld_hq_attrs,
    .bin_attrs = cpld_hq_bin_attrs,
};

static struct resource cpld_hq_resources[] = {
    {
        .start  = 0xA100,
        .end    = 0xA1FF,
        .flags  = IORESOURCE_IO,
    },
};

static void cpld_hq_dev_release( struct device * dev)
{
    return;
}

static struct platform_device cpld_hq_dev = {
    .name           = CPLD_DRIVER_NAME,
    .id             = -1,
    .num_resources  = ARRAY_SIZE(cpld_hq_resources),
    .resource       = cpld_hq_resources,
    .dev = {
        .release = cpld_hq_dev_release,
    }
};

static int cpld_hq_drv_remove(struct platform_device *pdev)
{
    sysfs_remove_group(&pdev->dev.kobj, &cpld_hq_attrs_group);
    return 0;
}

static int cpld_hq_drv_probe(struct platform_device *pdev)
{
    struct resource *resource;
    int err = 0;
    
    cpld_data = devm_kzalloc(&pdev->dev, sizeof(struct cpld_hq_data), GFP_KERNEL);
    if(!cpld_data)
        return -ENOMEM;
    
    mutex_init(&cpld_data->cpld_lock);
	
    cpld_data ->read_addr = VERSION_ADDR;
	cpld_data ->base_addr = BASE_CPLD_ADDR;
	
    resource = platform_get_resource(pdev, IORESOURCE_IO, 0);
    if(unlikely(!resource))
    {
        printk(KERN_ERR "Specified Resource Not Available...\n");
        return -ENODEV;
    }

    err = sysfs_create_group(&pdev->dev.kobj, &cpld_hq_attrs_group);
    if(err) {
        printk(KERN_ERR "Cannot create sysfs for system CPLD\n");
        return err;
    }

	printk(KERN_INFO "CPLD Probe driver");
    printk(KERN_INFO "BASE CPLD Address:ox%2.2x\n", BASE_CPLD_ADDR);
	printk(KERN_INFO "COMe CPLD Address:ox%2.2x\n", COME_CPLD_ADDR);
	
    printk(KERN_INFO "BASE CPLD PCB version:0x%2.2x\n", inb(BASE_PCB_VER_ADDR));
    printk(KERN_INFO "BASE CPLD H version:0x%2.2x\n", inb(BASE_H_VER_ADDR));
    printk(KERN_INFO "BASE CPLD M version:0x%2.2x\n", inb(BASE_M_VER_ADDR));
    printk(KERN_INFO "BASE CPLD L version:0x%2.2x\n", inb(BASE_L_VER_ADDR));

	printk(KERN_INFO "COME CPLD PCB version:0x%2.2x\n", inb(COME_PCB_VER_ADDR));
    printk(KERN_INFO "COME CPLD H version:0x%2.2x\n", inb(COME_H_VER_ADDR));
    printk(KERN_INFO "COME CPLD M version:0x%2.2x\n", inb(COME_M_VER_ADDR));
    printk(KERN_INFO "COME CPLD L version:0x%2.2x\n", inb(COME_L_VER_ADDR));	

    printk(KERN_INFO "GPIO base address:0x%x\n", inl(0x48));
    return 0;
}

static struct platform_driver cpld_hq_drv = {
    .probe = cpld_hq_drv_probe,
    .remove = __exit_p(cpld_hq_drv_remove),
    .driver = {
        .name = CPLD_DRIVER_NAME,
    },
};

static int __init cpld_hq_init(void)
{
    /*Register Platform device and Platform Driver*/
    platform_device_register(&cpld_hq_dev);
    platform_driver_register(&cpld_hq_drv);
	printk(KERN_INFO "%s: version %s loaded successfully\n", CPLD_DRIVER_NAME, CPLD_DRIVER_VER);
	return 0;
}

static void __exit cpld_hq_exit(void)
{
    /*Unregister Platform device and Platform Driver*/
    platform_driver_unregister(&cpld_hq_drv);
    platform_device_unregister(&cpld_hq_dev);
	printk(KERN_INFO "%s: unloaded successfully\n", CPLD_DRIVER_NAME);
}

module_init(cpld_hq_init);
module_exit(cpld_hq_exit);

MODULE_AUTHOR("Huaqin Technology Co.,Ltd.");
MODULE_DESCRIPTION("Hua Qin Common CPLD");
MODULE_VERSION(CPLD_DRIVER_VER);
MODULE_LICENSE("GPL");

