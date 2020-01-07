/*
 *  PCA9555 16 bit I/O ports special for SFP
 *
 *  Copyright (C) 2019 Donald Liu <liumaodong@inspur.com>
 *
 *  Derived from drivers\gpio\gpio-pca953x.c
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; version 2 of the License.
 */

#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/module.h>
#include <linux/slab.h>
#include <linux/delay.h>
#include <linux/mutex.h>
#include <linux/sysfs.h>
#include <linux/jiffies.h>
#include <linux/i2c.h>
#include <linux/types.h>

#define PCA9641_CONTROL		0x01
#define PCA9641_STATUS		0x02
#define PCA9641_TIME		0x03

#define PCA9641_CTL_LOCK_REQ		BIT(0)
#define PCA9641_CTL_LOCK_GRANT		BIT(1)
#define PCA9641_CTL_BUS_CONNECT		BIT(2)
#define PCA9641_CTL_BUS_INIT		BIT(3)
#define PCA9641_CTL_SMBUS_SWRST		BIT(4)
#define PCA9641_CTL_IDLE_TIMER_DIS	BIT(5)
#define PCA9641_CTL_SMBUS_DIS		BIT(6)
#define PCA9641_CTL_PRIORITY		BIT(7)

#define PCA9641_STS_OTHER_LOCK		BIT(0)
#define PCA9641_STS_BUS_INIT_FAIL	BIT(1)
#define PCA9641_STS_BUS_HUNG		BIT(2)
#define PCA9641_STS_MBOX_EMPTY		BIT(3)
#define PCA9641_STS_MBOX_FULL		BIT(4)
#define PCA9641_STS_TEST_INT		BIT(5)
#define PCA9641_STS_SCL_IO		BIT(6)
#define PCA9641_STS_SDA_IO		BIT(7)

#define bus_idle(x, y)	(!((x) & PCA9641_CTL_LOCK_GRANT) && \
			!((y) & PCA9641_STS_OTHER_LOCK))
#define bus_grant(x)	((x) & PCA9641_CTL_LOCK_GRANT)
#define bus_connect(x, y) (((x) & PCA9641_CTL_BUS_CONNECT) && \
			!((y) & PCA9641_STS_BUS_INIT_FAIL))

/* arbitration timeouts, in jiffies */
#define ARB_TIMEOUT	(HZ)	/* 1000 ms until acquisition failure */

/* arbitration retry delays, in us */
#define POLL_DELAY	1000

struct pca9641 {
	int muxes_use_smbus;
	unsigned long poll_delay;
};

struct pca954x {
	int muxes_use_smbus;
};

#define PCA9555_INPUT0		0
#define PCA9555_INPUT1		1
#define PCA9555_OUTPUT0		2
#define PCA9555_OUTPUT1		3
#define PCA9555_INVERT0		4
#define PCA9555_INVERT1		5
#define PCA9555_DIRECTION0	6
#define PCA9555_DIRECTION1	7

#define GPIO_INPUT	1
#define GPIO_OUTPUT	0

struct sfpio_data {
	int use_smbus;
	const char *port_name;
	u8 group;
	u8 chip;
	u8 channel;
	u8 direction;
	
	struct attribute_group attr_group;

	struct i2c_client *client[8];
	struct i2c_client *client_pca9641;
	struct mutex *lock_pca9641;
	struct i2c_client *client_pca9546;
	struct kobject kobj;
};

struct sfpio_data sfpio_tbl[] = {
	//QSFP28 low power mode configuration
	{
		.port_name = "qsfp28_lpmode48",
		.group = 0,
		.chip = 0,
		.channel = 0,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "qsfp28_lpmode49",
		.group = 0,
		.chip = 0,
		.channel = 1,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "qsfp28_lpmode50",
		.group = 0,
		.chip = 0,
		.channel = 2,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "qsfp28_lpmode51",
		.group = 0,
		.chip = 0,
		.channel = 3,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "qsfp28_lpmode52",
		.group = 0,
		.chip = 0,
		.channel = 4,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "qsfp28_lpmode53",
		.group = 0,
		.chip = 0,
		.channel = 5,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "qsfp28_lpmode54",
		.group = 0,
		.chip = 0,
		.channel = 6,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "qsfp28_lpmode55",
		.group = 0,
		.chip = 0,
		.channel = 7,
		.direction = GPIO_OUTPUT,
	},

	//SFP28 Fault
	{
		.port_name = "sfp28_fault0",
		.group = 0,
		.chip = 1,
		.channel = 8,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault1",
		.group = 0,
		.chip = 1,
		.channel = 9,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault2",
		.group = 0,
		.chip = 1,
		.channel = 10,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault3",
		.group = 0,
		.chip = 1,
		.channel = 11,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault4",
		.group = 0,
		.chip = 1,
		.channel = 12,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault5",
		.group = 0,
		.chip = 1,
		.channel = 13,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault6",
		.group = 0,
		.chip = 1,
		.channel = 14,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault7",
		.group = 0,
		.chip = 1,
		.channel = 15,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault8",
		.group = 0,
		.chip = 1,
		.channel = 0,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault9",
		.group = 0,
		.chip = 1,
		.channel = 1,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault10",
		.group = 0,
		.chip = 1,
		.channel = 2,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault11",
		.group = 0,
		.chip = 1,
		.channel = 3,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault12",
		.group = 0,
		.chip = 1,
		.channel = 4,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault13",
		.group = 0,
		.chip = 1,
		.channel = 5,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault14",
		.group = 0,
		.chip = 1,
		.channel = 6,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault15",
		.group = 0,
		.chip = 1,
		.channel = 7,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault16",
		.group = 0,
		.chip = 2,
		.channel = 8,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault17",
		.group = 0,
		.chip = 2,
		.channel = 9,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault18",
		.group = 0,
		.chip = 2,
		.channel = 10,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault19",
		.group = 0,
		.chip = 2,
		.channel = 11,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault20",
		.group = 0,
		.chip = 2,
		.channel = 12,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault21",
		.group = 0,
		.chip = 2,
		.channel = 13,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault22",
		.group = 0,
		.chip = 2,
		.channel = 14,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault23",
		.group = 0,
		.chip = 2,
		.channel = 15,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault24",
		.group = 0,
		.chip = 2,
		.channel = 0,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault25",
		.group = 0,
		.chip = 2,
		.channel = 1,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault26",
		.group = 0,
		.chip = 2,
		.channel = 2,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault27",
		.group = 0,
		.chip = 2,
		.channel = 3,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault28",
		.group = 0,
		.chip = 2,
		.channel = 4,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault29",
		.group = 0,
		.chip = 2,
		.channel = 5,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault30",
		.group = 0,
		.chip = 2,
		.channel = 6,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault31",
		.group = 0,
		.chip = 2,
		.channel = 7,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault32",
		.group = 0,
		.chip = 3,
		.channel = 8,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault33",
		.group = 0,
		.chip = 3,
		.channel = 9,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault34",
		.group = 0,
		.chip = 3,
		.channel = 10,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault35",
		.group = 0,
		.chip = 3,
		.channel = 11,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault36",
		.group = 0,
		.chip = 3,
		.channel = 12,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault37",
		.group = 0,
		.chip = 3,
		.channel = 13,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault38",
		.group = 0,
		.chip = 3,
		.channel = 14,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault39",
		.group = 0,
		.chip = 3,
		.channel = 15,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault40",
		.group = 0,
		.chip = 3,
		.channel = 0,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault41",
		.group = 0,
		.chip = 3,
		.channel = 1,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault42",
		.group = 0,
		.chip = 3,
		.channel = 2,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault43",
		.group = 0,
		.chip = 3,
		.channel = 3,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault44",
		.group = 0,
		.chip = 3,
		.channel = 4,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault45",
		.group = 0,
		.chip = 3,
		.channel = 5,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault46",
		.group = 0,
		.chip = 3,
		.channel = 6,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_fault47",
		.group = 0,
		.chip = 3,
		.channel = 7,
		.direction = GPIO_INPUT,
	},

	//SFP28 los
	{
		.port_name = "sfp28_los0",
		.group = 0,
		.chip = 4,
		.channel = 8,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los1",
		.group = 0,
		.chip = 4,
		.channel = 9,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los2",
		.group = 0,
		.chip = 4,
		.channel = 10,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los3",
		.group = 0,
		.chip = 4,
		.channel = 11,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los4",
		.group = 0,
		.chip = 4,
		.channel = 12,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los5",
		.group = 0,
		.chip = 4,
		.channel = 13,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los6",
		.group = 0,
		.chip = 4,
		.channel = 14,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los7",
		.group = 0,
		.chip = 4,
		.channel = 15,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los8",
		.group = 0,
		.chip = 4,
		.channel = 0,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los9",
		.group = 0,
		.chip = 4,
		.channel = 1,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los10",
		.group = 0,
		.chip = 4,
		.channel = 2,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los11",
		.group = 0,
		.chip = 4,
		.channel = 3,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los12",
		.group = 0,
		.chip = 4,
		.channel = 4,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los13",
		.group = 0,
		.chip = 4,
		.channel = 5,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los14",
		.group = 0,
		.chip = 4,
		.channel = 6,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los15",
		.group = 0,
		.chip = 4,
		.channel = 7,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los16",
		.group = 0,
		.chip = 5,
		.channel = 8,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los17",
		.group = 0,
		.chip = 5,
		.channel = 9,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los18",
		.group = 0,
		.chip = 5,
		.channel = 10,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los19",
		.group = 0,
		.chip = 5,
		.channel = 11,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los20",
		.group = 0,
		.chip = 5,
		.channel = 12,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los21",
		.group = 0,
		.chip = 5,
		.channel = 13,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los22",
		.group = 0,
		.chip = 5,
		.channel = 14,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los23",
		.group = 0,
		.chip = 5,
		.channel = 15,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los24",
		.group = 0,
		.chip = 5,
		.channel = 0,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los25",
		.group = 0,
		.chip = 5,
		.channel = 1,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los26",
		.group = 0,
		.chip = 5,
		.channel = 2,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los27",
		.group = 0,
		.chip = 5,
		.channel = 3,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los28",
		.group = 0,
		.chip = 5,
		.channel = 4,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los29",
		.group = 0,
		.chip = 5,
		.channel = 5,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los30",
		.group = 0,
		.chip = 5,
		.channel = 6,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los31",
		.group = 0,
		.chip = 5,
		.channel = 7,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los32",
		.group = 0,
		.chip = 6,
		.channel = 8,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los33",
		.group = 0,
		.chip = 6,
		.channel = 9,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los34",
		.group = 0,
		.chip = 6,
		.channel = 10,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los35",
		.group = 0,
		.chip = 6,
		.channel = 11,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los36",
		.group = 0,
		.chip = 6,
		.channel = 12,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los37",
		.group = 0,
		.chip = 6,
		.channel = 13,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los38",
		.group = 0,
		.chip = 6,
		.channel = 14,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los39",
		.group = 0,
		.chip = 6,
		.channel = 15,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los40",
		.group = 0,
		.chip = 6,
		.channel = 0,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los41",
		.group = 0,
		.chip = 6,
		.channel = 1,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los42",
		.group = 0,
		.chip = 6,
		.channel = 2,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los43",
		.group = 0,
		.chip = 6,
		.channel = 3,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los44",
		.group = 0,
		.chip = 6,
		.channel = 4,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los45",
		.group = 0,
		.chip = 6,
		.channel = 5,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los46",
		.group = 0,
		.chip = 6,
		.channel = 6,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_los47",
		.group = 0,
		.chip = 6,
		.channel = 7,
		.direction = GPIO_INPUT,
	},
	
	//QSFP28 interrupt configuration
	{
		.port_name = "qsfp28_interrupt48",
		.group = 0,
		.chip = 7,
		.channel = 0,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "qsfp28_interrupt49",
		.group = 0,
		.chip = 7,
		.channel = 1,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "qsfp28_interrupt50",
		.group = 0,
		.chip = 7,
		.channel = 2,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "qsfp28_interrupt51",
		.group = 0,
		.chip = 7,
		.channel = 3,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "qsfp28_interrupt52",
		.group = 0,
		.chip = 7,
		.channel = 4,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "qsfp28_interrupt53",
		.group = 0,
		.chip = 7,
		.channel = 5,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "qsfp28_interrupt54",
		.group = 0,
		.chip = 7,
		.channel = 6,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "qsfp28_interrupt55",
		.group = 0,
		.chip = 7,
		.channel = 7,
		.direction = GPIO_INPUT,
	},
	
	//QSFP28 module present configuration
	{
		.port_name = "qsfp28_present48",
		.group = 0,
		.chip = 7,
		.channel = 8,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "qsfp28_present49",
		.group = 0,
		.chip = 7,
		.channel = 9,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "qsfp28_present50",
		.group = 0,
		.chip = 7,
		.channel = 10,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "qsfp28_present51",
		.group = 0,
		.chip = 7,
		.channel = 11,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "qsfp28_present52",
		.group = 0,
		.chip = 7,
		.channel = 12,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "qsfp28_present53",
		.group = 0,
		.chip = 7,
		.channel = 13,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "qsfp28_present54",
		.group = 0,
		.chip = 7,
		.channel = 14,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "qsfp28_present55",
		.group = 0,
		.chip = 7,
		.channel = 15,
		.direction = GPIO_INPUT,
	},
	
	//SFP28 disable configuration
	{
		.port_name = "sfp28_disable0",
		.group = 1,
		.chip = 0,
		.channel = 8,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable1",
		.group = 1,
		.chip = 0,
		.channel = 9,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable2",
		.group = 1,
		.chip = 0,
		.channel = 10,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable3",
		.group = 1,
		.chip = 0,
		.channel = 11,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable4",
		.group = 1,
		.chip = 0,
		.channel = 12,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable5",
		.group = 1,
		.chip = 0,
		.channel = 13,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable6",
		.group = 1,
		.chip = 0,
		.channel = 14,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable7",
		.group = 1,
		.chip = 0,
		.channel = 15,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable8",
		.group = 1,
		.chip = 0,
		.channel = 0,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable9",
		.group = 1,
		.chip = 0,
		.channel = 1,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable10",
		.group = 1,
		.chip = 0,
		.channel = 2,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable11",
		.group = 1,
		.chip = 0,
		.channel = 3,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable12",
		.group = 1,
		.chip = 0,
		.channel = 4,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable13",
		.group = 1,
		.chip = 0,
		.channel = 5,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable14",
		.group = 1,
		.chip = 0,
		.channel = 6,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable15",
		.group = 1,
		.chip = 0,
		.channel = 7,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable16",
		.group = 1,
		.chip = 1,
		.channel = 8,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable17",
		.group = 1,
		.chip = 1,
		.channel = 9,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable18",
		.group = 1,
		.chip = 1,
		.channel = 10,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable19",
		.group = 1,
		.chip = 1,
		.channel = 11,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable20",
		.group = 1,
		.chip = 1,
		.channel = 12,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable21",
		.group = 1,
		.chip = 1,
		.channel = 13,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable22",
		.group = 1,
		.chip = 1,
		.channel = 14,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable23",
		.group = 1,
		.chip = 1,
		.channel = 15,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable24",
		.group = 1,
		.chip = 1,
		.channel = 0,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable25",
		.group = 1,
		.chip = 1,
		.channel = 1,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable26",
		.group = 1,
		.chip = 1,
		.channel = 2,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable27",
		.group = 1,
		.chip = 1,
		.channel = 3,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable28",
		.group = 1,
		.chip = 1,
		.channel = 4,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable29",
		.group = 1,
		.chip = 1,
		.channel = 5,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable30",
		.group = 1,
		.chip = 1,
		.channel = 6,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable31",
		.group = 1,
		.chip = 1,
		.channel = 7,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable32",
		.group = 1,
		.chip = 2,
		.channel = 8,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable33",
		.group = 1,
		.chip = 2,
		.channel = 9,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable34",
		.group = 1,
		.chip = 2,
		.channel = 10,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable35",
		.group = 1,
		.chip = 2,
		.channel = 11,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable36",
		.group = 1,
		.chip = 2,
		.channel = 12,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable37",
		.group = 1,
		.chip = 2,
		.channel = 13,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable38",
		.group = 1,
		.chip = 2,
		.channel = 14,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable39",
		.group = 1,
		.chip = 2,
		.channel = 15,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable40",
		.group = 1,
		.chip = 2,
		.channel = 0,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable41",
		.group = 1,
		.chip = 2,
		.channel = 1,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable42",
		.group = 1,
		.chip = 2,
		.channel = 2,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable43",
		.group = 1,
		.chip = 2,
		.channel = 3,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable44",
		.group = 1,
		.chip = 2,
		.channel = 4,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable45",
		.group = 1,
		.chip = 2,
		.channel = 5,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable46",
		.group = 1,
		.chip = 2,
		.channel = 6,
		.direction = GPIO_OUTPUT,
	},
	{
		.port_name = "sfp28_disable47",
		.group = 1,
		.chip = 2,
		.channel = 7,
		.direction = GPIO_OUTPUT,
	},
	
	//SFP28 present configuration
	{
		.port_name = "sfp28_present0",
		.group = 1,
		.chip = 3,
		.channel = 8,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present1",
		.group = 1,
		.chip = 3,
		.channel = 9,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present2",
		.group = 1,
		.chip = 3,
		.channel = 10,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present3",
		.group = 1,
		.chip = 3,
		.channel = 11,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present4",
		.group = 1,
		.chip = 3,
		.channel = 12,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present5",
		.group = 1,
		.chip = 3,
		.channel = 13,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present6",
		.group = 1,
		.chip = 3,
		.channel = 14,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present7",
		.group = 1,
		.chip = 3,
		.channel = 15,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present8",
		.group = 1,
		.chip = 3,
		.channel = 0,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present9",
		.group = 1,
		.chip = 3,
		.channel = 1,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present10",
		.group = 1,
		.chip = 3,
		.channel = 2,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present11",
		.group = 1,
		.chip = 3,
		.channel = 3,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present12",
		.group = 1,
		.chip = 3,
		.channel = 4,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present13",
		.group = 1,
		.chip = 3,
		.channel = 5,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present14",
		.group = 1,
		.chip = 3,
		.channel = 6,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present15",
		.group = 1,
		.chip = 3,
		.channel = 7,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present16",
		.group = 1,
		.chip = 4,
		.channel = 8,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present17",
		.group = 1,
		.chip = 4,
		.channel = 9,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present18",
		.group = 1,
		.chip = 4,
		.channel = 10,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present19",
		.group = 1,
		.chip = 4,
		.channel = 11,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present20",
		.group = 1,
		.chip = 4,
		.channel = 12,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present21",
		.group = 1,
		.chip = 4,
		.channel = 13,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present22",
		.group = 1,
		.chip = 4,
		.channel = 14,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present23",
		.group = 1,
		.chip = 4,
		.channel = 15,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present24",
		.group = 1,
		.chip = 4,
		.channel = 0,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present25",
		.group = 1,
		.chip = 4,
		.channel = 1,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present26",
		.group = 1,
		.chip = 4,
		.channel = 2,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present27",
		.group = 1,
		.chip = 4,
		.channel = 3,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present28",
		.group = 1,
		.chip = 4,
		.channel = 4,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present29",
		.group = 1,
		.chip = 4,
		.channel = 5,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present30",
		.group = 1,
		.chip = 4,
		.channel = 6,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present31",
		.group = 1,
		.chip = 4,
		.channel = 7,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present32",
		.group = 1,
		.chip = 5,
		.channel = 8,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present33",
		.group = 1,
		.chip = 5,
		.channel = 9,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present34",
		.group = 1,
		.chip = 5,
		.channel = 10,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present35",
		.group = 1,
		.chip = 5,
		.channel = 11,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present36",
		.group = 1,
		.chip = 5,
		.channel = 12,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present37",
		.group = 1,
		.chip = 5,
		.channel = 13,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present38",
		.group = 1,
		.chip = 5,
		.channel = 14,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present39",
		.group = 1,
		.chip = 5,
		.channel = 15,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present40",
		.group = 1,
		.chip = 5,
		.channel = 0,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present41",
		.group = 1,
		.chip = 5,
		.channel = 1,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present42",
		.group = 1,
		.chip = 5,
		.channel = 2,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present43",
		.group = 1,
		.chip = 5,
		.channel = 3,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present44",
		.group = 1,
		.chip = 5,
		.channel = 4,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present45",
		.group = 1,
		.chip = 5,
		.channel = 5,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present46",
		.group = 1,
		.chip = 5,
		.channel = 6,
		.direction = GPIO_INPUT,
	},
	{
		.port_name = "sfp28_present47",
		.group = 1,
		.chip = 5,
		.channel = 7,
		.direction = GPIO_INPUT,
	},
};

static struct kobj_type ktype_sfpio_default = {
	.sysfs_ops	= &kobj_sysfs_ops,
};

static const struct i2c_device_id sfpio_ids[] = {
	{ "inspur-sfpio", 0x00 },
	{ /* END OF LIST */ }
};
MODULE_DEVICE_TABLE(i2c, sfpio_ids);

/*
 * Read from chip register.
 */
static int pca9641_reg_read(struct i2c_client *client, u8 command)
{
	struct pca9641 *data = i2c_get_clientdata(client);
	int ret;
	u8 val;

	if (data->muxes_use_smbus == true) {
		ret = i2c_smbus_read_byte_data(client, command);
	} else {
		struct i2c_msg msg[2] = {
			{
				.addr = client->addr,
				.flags = 0,
				.len = 1,
				.buf = &command
			},
			{
				.addr = client->addr,
				.flags = I2C_M_RD,
				.len = 1,
				.buf = &val
			}
		};

		ret = i2c_transfer(client->adapter, msg, 2);
		if (ret == 2)
			ret = val;
		else if (ret >= 0)
			ret = -EIO;
	}

	if (ret < 0)
		dev_err(&client->dev, "[DD] pca9641 addr: %x, reg read command: %x, return: %d\n", client->addr, command, ret);

	return ret;
}

/*
 * Write to chip register.
 */
static int pca9641_reg_write(struct i2c_client *client, u8 command, u8 val)
{
	struct pca9641 *data = i2c_get_clientdata(client);
	int ret;

	if (data->muxes_use_smbus == true) {
		ret = i2c_smbus_write_byte_data(client, command, val);
	} else {
		struct i2c_msg msg;
		char buf[2];

		msg.addr = client->addr;
		msg.flags = 0;
		msg.len = 2;
		buf[0] = command;
		buf[1] = val;
		msg.buf = buf;
		ret = i2c_transfer(client->adapter, &msg, 1);
		if (ret == 1)
			ret = 0;
		else if (ret >= 0)
			ret = -EIO;
	}

	if (ret < 0)
		dev_err(&client->dev, "[DD] pca9641 addr: %x, reg write command: %x, write value: %x, return: %d\n", client->addr, command, val, ret);

	return ret;
}

static int pca9641_arbitrate(struct i2c_client *client)
{
	struct pca9641 *data = i2c_get_clientdata(client);
	int reg_ctl, reg_sts, ret;

	reg_ctl = pca9641_reg_read(client, PCA9641_CONTROL);
	if (reg_ctl < 0)
		return reg_ctl;
	reg_sts = pca9641_reg_read(client, PCA9641_STATUS);
	if (reg_sts < 0)
		return reg_sts;

	if (!bus_grant(reg_ctl)) {
		/*
		 * Bus is not granted to us, try to lock.
		 */
		ret = pca9641_reg_write(client, PCA9641_CONTROL, PCA9641_CTL_LOCK_REQ | PCA9641_CTL_BUS_INIT);
		if (ret < 0)
			return ret;
		
		if (bus_idle(reg_ctl, reg_sts)) {
			data->poll_delay = 0;
			
			dev_dbg(&client->dev, "[CC] pca9641 bus idle, try to get ownership\n");
		} else {
			data->poll_delay = POLL_DELAY;
			
			dev_dbg(&client->dev, "[CC] pca9641 bus locked by BMC, try to get ownership\n");
		}

	} else {
		if (bus_connect(reg_ctl, reg_sts)) {
			/*
		 	 * Bus is on, and we own it. We are done with acquisition.
		 	 */
			dev_dbg(&client->dev, "[CC] pca9641 get ownership succeed\n");
			
			return 1;
		} else {
			/*
		 	 * Bus is locked, try to connect.
		 	 */
			reg_ctl |= (PCA9641_CTL_BUS_CONNECT | PCA9641_CTL_BUS_INIT);
			ret = pca9641_reg_write(client, PCA9641_CONTROL, reg_ctl);
			if (ret < 0)
				return ret;
			data->poll_delay = 0;
			
			dev_dbg(&client->dev, "[CC] pca9641 locked, try to connect\n");
		}
	}
	
	return 0;
}

static int pca9641_select_chan(struct i2c_client *client, u32 chan)
{
	struct pca9641 *data = i2c_get_clientdata(client);
	int ret;
	unsigned long timeout = jiffies + ARB_TIMEOUT;
		/* give up after this time */

	do {
		ret = pca9641_arbitrate(client);
		if (ret)
			return ret < 0 ? ret : 0;

		if (data->poll_delay == POLL_DELAY)
			msleep(data->poll_delay / 1000);
	} while (time_is_after_eq_jiffies(timeout));

	dev_dbg(&client->dev, "[CC] pca9641 channel select timeout.\n");

	return -ETIMEDOUT;
}

static int pca9641_release_chan(struct i2c_client *client, u32 chan)
{
	int ret;
	
	ret = pca9641_reg_write(client, PCA9641_CONTROL, 0);
	dev_dbg(&((struct i2c_client *)client)->dev, "[CC] pca9641 chan released\n");
	
	return ret;
}

/* Write to mux register. */
static int pca954x_reg_write(struct i2c_client *client, u8 val)
{
	struct pca954x *data = i2c_get_clientdata(client);
	int ret;

	if (data->muxes_use_smbus == true) {
		ret = i2c_smbus_write_byte(client, val);
	} else {
		struct i2c_msg msg;
		char buf[1];

		msg.addr = client->addr;
		msg.flags = 0;
		msg.len = 1;
		buf[0] = val;
		msg.buf = buf;
		ret = i2c_transfer(client->adapter, &msg, 1);
		
		if (ret == 1)
			ret = 0;
		else if (ret >= 0)
			ret = -EIO;
	}

	if (ret < 0)
		dev_err(&client->dev, "[DD] pca954x addr: %x, write value: %x, return: %d\n", client->addr, val, ret);

	return ret;
}

static int pca954x_select_chan(struct i2c_client *client_pca954x, u32 chan)
{
	int ret = 0;
	
	if (chan > 7) {
		return -ENODEV;
	}
	
	ret = pca954x_reg_write(client_pca954x, 1 << chan);
	dev_dbg(&client_pca954x->dev, "pca954x chip: channel select return: %d\n", ret);
	
	return ret;
}

static int pca954x_deselect_chan(struct i2c_client *client_pca954x, u32 chan)
{
	int ret = 0;
	
	ret = pca954x_reg_write(client_pca954x, 0);
	dev_dbg(&client_pca954x->dev, "pca954x chip: deselect channel return: %d\n", ret);
	
	return ret;
}

/*
 * Read from chip register.
 */
static int pca9555_word_read(struct sfpio_data *sfpio, u8 command)
{
	struct i2c_client *client;
	int use_smbus;
	int ret;
	u8 buf[2];
	
	client = sfpio->client[sfpio->chip];
	use_smbus = sfpio->use_smbus;

	if (use_smbus == true) {
		ret = i2c_smbus_read_word_data(client, command);
	} else {
		struct i2c_msg msg[2] = {
			{
				.addr = client->addr,
				.flags = 0,
				.len = 1,
				.buf = &command
			},
			{
				.addr = client->addr,
				.flags = I2C_M_RD,
				.len = 2,
				.buf = buf
			}
		};
		ret = i2c_transfer(client->adapter, msg, 2);
		if (ret == 2)
			ret = buf[0] | ((u16)buf[1] << 8);
		else if (ret >= 0)
			ret = -EIO;
	}

	if (ret < 0)
		dev_err(&client->dev, "[DD] pca9555 addr: %x, reg read command: %x, return: %d\n", client->addr, command, ret);

	return ret;
}

/*
 * Write to chip register.
 */
static int pca9555_word_write(struct sfpio_data *sfpio, u8 command, u16 val)
{
	struct i2c_client *client;
	int use_smbus;
	int ret;

	client = sfpio->client[sfpio->chip];
	use_smbus = sfpio->use_smbus;

	if (use_smbus == true) {
		ret = i2c_smbus_write_word_data(client, command, val);
	} else {
		struct i2c_msg msg;
		u8 buf[3];

		msg.addr = client->addr;
		msg.flags = 0;
		msg.len = 3;
		buf[0] = command;
		buf[1] = val & 0xff;
		buf[2] = (val >> 8) & 0xff;
		msg.buf = buf;
		ret = i2c_transfer(client->adapter, &msg, 1);
		if (ret == 1)
			ret = 0;
		else if (ret >= 0)
			ret = -EIO;
	}

	if (ret < 0)
		dev_err(&client->dev, "[DD] pca9555 addr: %x, reg write command: %x, write value: %x, return: %d\n", client->addr, command, val, ret);

	return ret;
}

static int sfpio_remove(struct i2c_client *client)
{
	struct sfpio_data *sfpio;
	struct i2c_client *client_dummy[7];
	struct i2c_client *client_pca9641;
	struct pca9641 *data;
	struct mutex *lock_pca9641;
	struct i2c_client *client_pca9546;
	int i;

	sfpio = i2c_get_clientdata(client);
	
	memcpy(client_dummy, &sfpio->client[1], sizeof(client_dummy));
	client_pca9641 = sfpio->client_pca9641;
	lock_pca9641 = sfpio->lock_pca9641;
	client_pca9546 = sfpio->client_pca9546;
	data = i2c_get_clientdata(client_pca9641);
	
	for (i = 0; i < sizeof(sfpio_tbl) / sizeof(struct sfpio_data); i++) {
		sysfs_remove_group(&sfpio[i].kobj, &sfpio[i].attr_group);
		kobject_put(&sfpio[i].kobj);
	}
	
	for (i = 0; i < 7; i++) {
		i2c_unregister_device(client_dummy[i]);
	}
	
	i2c_unregister_device(client_pca9546);

	kfree(lock_pca9641);

	kfree(data);

	i2c_unregister_device(client_pca9641);

	return 0;
}

static ssize_t show_port_value(struct kobject *kobj, struct kobj_attribute *attr, char *buf)
{
	int ret;
	int value;
	ssize_t count;
	struct i2c_client *client[8];
	struct i2c_client *client_pca9641;
	struct mutex *lock_pca9641;
	struct i2c_client *client_pca9546;
	struct sfpio_data *sfpio = container_of(kobj, struct sfpio_data, kobj);
	
	memcpy(client, sfpio->client, sizeof(client));
	client_pca9641 = sfpio->client_pca9641;
	lock_pca9641 = sfpio->lock_pca9641;
	client_pca9546 = sfpio->client_pca9546;
	
	mutex_lock(lock_pca9641);
	ret = pca9641_select_chan(client_pca9641, 0);
	if (ret < 0) {
		goto err;
	}
	
	ret = pca954x_select_chan(client_pca9546, sfpio->group);
	if (ret < 0) {
		goto err_1;
	}

	if (sfpio->direction == GPIO_INPUT) {
		value = pca9555_word_read(sfpio, PCA9555_INPUT0);
		if (value < 0) {
			goto err_2;
		}
		dev_dbg(&client[sfpio->chip]->dev, "show_port_value GPIO_INPUT, read value=%d\n", value);
		value = 1 & (value >> sfpio->channel);
		
	} else {
		value = pca9555_word_read(sfpio, PCA9555_OUTPUT0);
		if (value < 0) {
			goto err_2;
		}
		dev_dbg(&client[sfpio->chip]->dev, "show_port_value GPIO_OUTPUT, read value=%d\n", value);
		value = 1 & (value >> sfpio->channel);
		
	}
	count = sprintf(buf, "%d\n", value);
	
	pca954x_deselect_chan(client_pca9546, sfpio->group);
	
	pca9641_release_chan(client_pca9641, 0);
	mutex_unlock(lock_pca9641);
	
	dev_dbg(&client[sfpio->chip]->dev, "group=%d, chip=%d, channel=%d, count=%ld\n", sfpio->group, sfpio->chip, sfpio->channel, count);
	return count;
	
err_2:
	pca954x_deselect_chan(client_pca9546, sfpio->group);
err_1:
	pca9641_release_chan(client_pca9641, 0);
err:
	mutex_unlock(lock_pca9641);
	return ret;
}

static ssize_t set_port_value(struct kobject *kobj, struct kobj_attribute *attr, const char *buf, size_t count)
{
	int ret;
	int value;
	int gpio_value;
	struct i2c_client *client[8];
	struct i2c_client *client_pca9641;
	struct mutex *lock_pca9641;
	struct i2c_client *client_pca9546;
	struct sfpio_data *sfpio = container_of(kobj, struct sfpio_data, kobj);

	if (kstrtoint(buf, 0, &gpio_value) != 0 ||
		gpio_value < 0 || gpio_value > 1)
		return -EINVAL;
	
	memcpy(client, sfpio->client, sizeof(client));
	client_pca9641 = sfpio->client_pca9641;
	lock_pca9641 = sfpio->lock_pca9641;
	client_pca9546 = sfpio->client_pca9546;
	
	mutex_lock(lock_pca9641);
	ret = pca9641_select_chan(client_pca9641, 0);
	if (ret < 0) {
		goto err;
	}
	
	ret = pca954x_select_chan(client_pca9546, sfpio->group);
	if (ret < 0) {
		goto err_1;
	}

	if (sfpio->direction == GPIO_OUTPUT) {
		value = pca9555_word_read(sfpio, PCA9555_OUTPUT0);
		if (value < 0) {
			goto err_2;
		}
		dev_dbg(&client[sfpio->chip]->dev, "set_port_value GPIO_OUTPUT, read value=%d\n", value);
		value = (value & ~(1 << sfpio->channel)) | (gpio_value << sfpio->channel);
		dev_dbg(&client[sfpio->chip]->dev, "set_port_value GPIO_OUTPUT, write value=%d\n", value);
		ret = pca9555_word_write(sfpio, PCA9555_OUTPUT0, value);
		if (ret < 0) {
			goto err_2;
		}
	} else {
		ret = -EIO;
		goto err_2;
	}
	
	pca954x_deselect_chan(client_pca9546, sfpio->group);
	
	pca9641_release_chan(client_pca9641, 0);
	mutex_unlock(lock_pca9641);
	
	dev_dbg(&client[sfpio->chip]->dev, "group=%d, chip=%d, channel=%d, count=%lu, ret=%d\n", sfpio->group, sfpio->chip, sfpio->channel, count, ret);
	return count;
	
err_2:
	pca954x_deselect_chan(client_pca9546, sfpio->group);
err_1:
	pca9641_release_chan(client_pca9641, 0);
err:
	mutex_unlock(lock_pca9641);
	return ret;
}

static ssize_t show_port_direction(struct kobject *kobj, struct kobj_attribute *attr, char *buf)
{
	ssize_t count;
	struct sfpio_data *sfpio = container_of(kobj, struct sfpio_data, kobj);

	if (sfpio->direction == GPIO_INPUT) {
		count = sprintf(buf, "%s\n", "input");
	} else {
		count = sprintf(buf, "%s\n", "output");
	}

	return count;
}

static struct kobj_attribute attr_port_value_readonly = __ATTR(port_value, 0444, show_port_value, NULL);
static struct kobj_attribute attr_port_value_readwrite = __ATTR(port_value, 0664, show_port_value, set_port_value);

static struct kobj_attribute attr_port_direction = __ATTR(port_direction, 0444, show_port_direction, NULL);

static struct attribute *sfpio_input_attrs[] = {
	&attr_port_value_readonly.attr,
	&attr_port_direction.attr,
	NULL,
};

static struct attribute *sfpio_output_attrs[] = {
	&attr_port_value_readwrite.attr,
	&attr_port_direction.attr,
	NULL,
};

static struct attribute_group sfpio_input_attr_group = {
	.attrs = sfpio_input_attrs,
};

static struct attribute_group sfpio_output_attr_group = {
	.attrs = sfpio_output_attrs,
};

static struct i2c_board_info pca9641_i2c_board_info = {
	I2C_BOARD_INFO("pca9641_0x70", 0x70),
};

static struct i2c_board_info pca9546_i2c_board_info = {
	I2C_BOARD_INFO("pca9546_0x71", 0x71),
};

static int set_gpio_direction(struct sfpio_data *sfpio)
{
	int ret;
	int direction;
	struct i2c_client *client[8];
	struct i2c_client *client_pca9641;
	struct mutex *lock_pca9641;
	struct i2c_client *client_pca9546;
	
	memcpy(client, sfpio->client, sizeof(client));
	client_pca9641 = sfpio->client_pca9641;
	lock_pca9641 = sfpio->lock_pca9641;
	client_pca9546 = sfpio->client_pca9546;
	
	mutex_lock(lock_pca9641);
	ret = pca9641_select_chan(client_pca9641, 0);
	if (ret < 0) {
		goto err;
	}
	ret = pca954x_select_chan(client_pca9546, sfpio->group);
	if (ret < 0) {
		goto err_1;
	}
	direction = pca9555_word_read(sfpio, PCA9555_DIRECTION0);
	if (direction < 0) {
		goto err_2;
	}
	dev_dbg(&client[sfpio->chip]->dev, "set_gpio_direction, read direction=%d\n", direction);
	if (sfpio->direction == GPIO_INPUT) {
		direction = direction | (1 << sfpio->channel);
		dev_dbg(&client[sfpio->chip]->dev, "set_gpio_direction GPIO_INPUT, write direction=%d\n", direction);
	} else {
		direction = direction & ~(1 << sfpio->channel);
		dev_dbg(&client[sfpio->chip]->dev, "set_gpio_direction GPIO_OUTPUT, write direction=%d\n", direction);
	}
	
	ret = pca9555_word_write(sfpio, PCA9555_DIRECTION0, direction);
	
	pca954x_deselect_chan(client_pca9546, sfpio->group);
	
	pca9641_release_chan(client_pca9641, 0);
	mutex_unlock(lock_pca9641);
	
	dev_dbg(&client[sfpio->chip]->dev, "group=%d, chip=%d, channel=%d, ret=%d\n", sfpio->group, sfpio->chip, sfpio->channel, ret);
	return ret;
	
err_2:
	pca954x_deselect_chan(client_pca9546, sfpio->group);
err_1:
	pca9641_release_chan(client_pca9641, 0);
err:
	mutex_unlock(lock_pca9641);
	return ret;
}

static int sfpio_probe(struct i2c_client *client,
			const struct i2c_device_id *id)
{
	int err;
	int use_smbus = false;
	struct i2c_client *client_pca9641;
	struct pca9641 *pca9641_data;
	struct mutex *lock_pca9641;
	struct i2c_client *client_pca9546;
	struct pca954x *pca9546_data;
	struct i2c_client *client_dummy[7];
	int i, j;
	
	dev_dbg(&client->dev, "probe start\n");
	
	if (client->addr != 0x20) {
		err = -EINVAL;
		dev_err(&client->dev, "probe, bad i2c addr: 0x%x\n", client->addr);
		goto exit;
	}
	
	/* Use I2C operations unless we're stuck with SMBus extensions. */
	if (!i2c_check_functionality(client->adapter, I2C_FUNC_I2C)) {
		/* check the i2c functionality for pca9641 and pca9546 and pca9555 */
		if (!i2c_check_functionality(client->adapter, I2C_FUNC_SMBUS_BYTE | I2C_FUNC_SMBUS_BYTE_DATA | I2C_FUNC_SMBUS_WORD_DATA)) {
			err = -ENODEV;
			dev_err(&client->dev, "i2c functionality check for pca9641 and pca9546 and pca9555 failed.\n");
			goto exit;
		}
		use_smbus = true;
	}
	
	client_pca9641 = i2c_new_device(client->adapter, &pca9641_i2c_board_info);
	if (!client_pca9641) {
		err = -ENODEV;
		dev_err(&client->dev, "create pca9641 i2c client failed.\n");
		goto exit;
	}
	
	pca9641_data = kzalloc(sizeof(struct pca9641), GFP_KERNEL);
	if (!pca9641_data) {
		err = -ENOMEM;
		dev_err(&client->dev, "memory allocate for pca9641 data failed.\n");
		goto exit_1;
	}
	pca9641_data->muxes_use_smbus = use_smbus;
	i2c_set_clientdata(client_pca9641, pca9641_data);
	
	lock_pca9641 = kzalloc(sizeof(struct mutex), GFP_KERNEL);
	if (!lock_pca9641) {
		err = -ENOMEM;
		dev_err(&client->dev, "memory allocate for pca9641 mutex failed.\n");
		goto exit_2;
	}
	mutex_init(lock_pca9641);
	
	client_pca9546 = i2c_new_device(client->adapter, &pca9546_i2c_board_info);
	if (!client_pca9546) {
		err = -ENODEV;
		dev_err(&client->dev, "create pca9546 i2c client failed.\n");
		goto exit_3;
	}

	pca9546_data = kzalloc(sizeof(struct pca954x), GFP_KERNEL);
	if (!pca9546_data) {
		err = -ENOMEM;
		dev_err(&client->dev, "memory allocate for pca9546 data failed.\n");
		goto exit_4;
	}
	pca9546_data->muxes_use_smbus = use_smbus;
	i2c_set_clientdata(client_pca9546, pca9546_data);
	
	for (i = 0; i < 7; i++) {
		client_dummy[i] = i2c_new_dummy(client->adapter, 0x21 + i);
		if (!client_dummy[i]) {
			err = -EADDRINUSE;
			dev_err(&client->dev, "address 0x%x unavailable\n", 0x21 + i);
			goto exit_5;
		}
	}

	for (j = 0; j < sizeof(sfpio_tbl) / sizeof(struct sfpio_data); j++) {
		dev_dbg(&client->dev, "building sfpio_tbl[%d] chip\n", j);
	
		sfpio_tbl[j].use_smbus = use_smbus;
		sfpio_tbl[j].client[0] = client;
		memcpy(&sfpio_tbl[j].client[1], client_dummy, sizeof(client_dummy));
		sfpio_tbl[j].client_pca9641 = client_pca9641;
		sfpio_tbl[j].lock_pca9641 = lock_pca9641;
		sfpio_tbl[j].client_pca9546 = client_pca9546;
		
		/* set gpio direction */
		err = set_gpio_direction(&sfpio_tbl[j]);
		if (err < 0) {
			dev_err(&client->dev, "sfpio_tbl[%d] failed to set gpio direction\n", j);
			goto err;
		}
		
		/* init kobject */
		err = kobject_init_and_add(&sfpio_tbl[j].kobj, &ktype_sfpio_default, &client->dev.kobj, sfpio_tbl[j].port_name);
		if (err < 0) {
			dev_err(&client->dev, "sfpio_tbl[%d] failed to create sysfs entry\n", j);
			goto err;
		}
		
		/* create sysfs group */
		if (sfpio_tbl[j].direction == GPIO_INPUT) {
			sfpio_tbl[j].attr_group = sfpio_input_attr_group;
		} else {
			sfpio_tbl[j].attr_group = sfpio_output_attr_group;
		}

		err = sysfs_create_group(&sfpio_tbl[j].kobj, &sfpio_tbl[j].attr_group);
		if (err) {
			dev_err(&client->dev, "sfpio_tbl[%d] failed to create sysfs attribute group.\n", j);
			goto err_1;
		}
	}
	
	i2c_set_clientdata(client, sfpio_tbl);

	return 0;

err_1:
	kobject_put(&sfpio_tbl[j].kobj);
err:
	for (j--; j >= 0; j--) {
		sysfs_remove_group(&sfpio_tbl[j].kobj, &sfpio_tbl[j].attr_group);
		kobject_put(&sfpio_tbl[j].kobj);
	}
	
exit_5:
	for (i--; i >= 0; i--) {
		i2c_unregister_device(client_dummy[i]);
	}
	kfree(pca9546_data);
exit_4:
	i2c_unregister_device(client_pca9546);
exit_3:
	kfree(lock_pca9641);
exit_2:
	kfree(pca9641_data);
exit_1:
	i2c_unregister_device(client_pca9641);
exit:
	dev_dbg(&client->dev, "probe error %d\n", err);

	return err;
}

/*-------------------------------------------------------------------------*/

static struct i2c_driver sfpio_driver = {
	.driver = {
		.name = "inspur-sfpio",
		.owner = THIS_MODULE,
	},
	.probe = sfpio_probe,
	.remove = sfpio_remove,
	.id_table = sfpio_ids,
};

static int __init sfpio_init(void)
{
	return i2c_add_driver(&sfpio_driver);
}
module_init(sfpio_init);

static void __exit sfpio_exit(void)
{
	i2c_del_driver(&sfpio_driver);
}
module_exit(sfpio_exit);

MODULE_DESCRIPTION("PCA9555 16 bit I/O ports special for SFP");
MODULE_AUTHOR("Donald Liu <liumaodong@inspur.com>");
MODULE_LICENSE("GPL");
