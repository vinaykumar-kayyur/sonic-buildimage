/*
 * optoe.c - A driver to read and write the EEPROM on optical transceivers
 * (SFP, QSFP and similar I2C based devices)
 *
 * Copyright (C) 2014 Cumulus networks Inc.
 * Copyright (C) 2017 Finisar Corp.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Freeoftware Foundation; either version 2 of the License, or
 * (at your option) any later version.
 */

/*
 *	Description:
 *	a) Optical transceiver EEPROM read/write transactions are just like
 *		the at24 eeproms managed by the at24.c i2c driver
 *	b) The register/memory layout is up to 256 128 byte pages defined by
 *		a "pages valid" register and switched via a "page select"
 *		register as explained in below diagram.
 *	c) 256 bytes are mapped at a time. 'Lower page 00h' is the first 128
 *	        bytes of address space, and always references the same
 *	        location, independent of the page select register.
 *	        All mapped pages are mapped into the upper 128 bytes
 *	        (offset 128-255) of the i2c address.
 *	d) Devices with one I2C address (eg QSFP) use I2C address 0x50
 *		(A0h in the spec), and map all pages in the upper 128 bytes
 *		of that address.
 *	e) Devices with two I2C addresses (eg SFP) have 256 bytes of data
 *		at I2C address 0x50, and 256 bytes of data at I2C address
 *		0x51 (A2h in the spec).  Page selection and paged access
 *		only apply to this second I2C address (0x51).
 *	e) The address space is presented, by the driver, as a linear
 *	        address space.  For devices with one I2C client at address
 *	        0x50 (eg QSFP), offset 0-127 are in the lower
 *	        half of address 50/A0h/client[0].  Offset 128-255 are in
 *	        page 0, 256-383 are page 1, etc.  More generally, offset
 *	        'n' resides in page (n/128)-1.  ('page -1' is the lower
 *	        half, offset 0-127).
 *	f) For devices with two I2C clients at address 0x50 and 0x51 (eg SFP),
 *		the address space places offset 0-127 in the lower
 *	        half of 50/A0/client[0], offset 128-255 in the upper
 *	        half.  Offset 256-383 is in the lower half of 51/A2/client[1].
 *	        Offset 384-511 is in page 0, in the upper half of 51/A2/...
 *	        Offset 512-639 is in page 1, in the upper half of 51/A2/...
 *	        Offset 'n' is in page (n/128)-3 (for n > 383)
 *
 *	                    One I2c addressed (eg QSFP) Memory Map
 *
 *	                    2-Wire Serial Address: 1010000x
 *
 *	                    Lower Page 00h (128 bytes)
 *	                    =====================
 *	                   |                     |
 *	                   |                     |
 *	                   |                     |
 *	                   |                     |
 *	                   |                     |
 *	                   |                     |
 *	                   |                     |
 *	                   |                     |
 *	                   |                     |
 *	                   |                     |
 *	                   |Page Select Byte(127)|
 *	                    =====================
 *	                              |
 *	                              |
 *	                              |
 *	                              |
 *	                              V
 *	     ------------------------------------------------------------
 *	    |                 |                  |                       |
 *	    |                 |                  |                       |
 *	    |                 |                  |                       |
 *	    |                 |                  |                       |
 *	    |                 |                  |                       |
 *	    |                 |                  |                       |
 *	    |                 |                  |                       |
 *	    |                 |                  |                       |
 *	    |                 |                  |                       |
 *	    V                 V                  V                       V
 *	 ------------   --------------      ---------------     --------------
 *	|            | |              |    |               |   |              |
 *	|   Upper    | |     Upper    |    |     Upper     |   |    Upper     |
 *	|  Page 00h  | |    Page 01h  |    |    Page 02h   |   |   Page 03h   |
 *	|            | |   (Optional) |    |   (Optional)  |   |  (Optional   |
 *	|            | |              |    |               |   |   for Cable  |
 *	|            | |              |    |               |   |  Assemblies) |
 *	|    ID      | |     AST      |    |      User     |   |              |
 *	|  Fields    | |    Table     |    |   EEPROM Data |   |              |
 *	|            | |              |    |               |   |              |
 *	|            | |              |    |               |   |              |
 *	|            | |              |    |               |   |              |
 *	 ------------   --------------      ---------------     --------------
 *
 * The SFF 8436 (QSFP) spec only defines the 4 pages described above.
 * In anticipation of future applications and devices, this driver
 * supports access to the full architected range, 256 pages.
 *
 **/

/* #define DEBUG 1 */
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

/* The maximum length of a port name */
#define MAX_PORT_NAME_LEN 20

struct optoe_platform_data {
	u32		byte_len;		/* size (sum of all addr) */
	u16		page_size;		/* for writes */
	u8		flags;
	void		*dummy1;		/* backward compatibility */
	void		*dummy2;		/* backward compatibility */
	char port_name[MAX_PORT_NAME_LEN];
};

/* fundamental unit of addressing for EEPROM */
#define OPTOE_PAGE_SIZE 128
/*
 * Single address devices (eg QSFP) have 256 pages, plus the unpaged
 * low 128 bytes.  If the device does not support paging, it is
 * only 2 'pages' long.
 */
#define OPTOE_ARCH_PAGES 256
#define ONE_ADDR_EEPROM_SIZE ((1 + OPTOE_ARCH_PAGES) * OPTOE_PAGE_SIZE)	/* eeprom total size */
#define ONE_ADDR_EEPROM_UNPAGED_SIZE (2 * OPTOE_PAGE_SIZE)
/*
 * Dual address devices (eg SFP) have 256 pages, plus the unpaged
 * low 128 bytes, plus 256 bytes at 0x50.  If the device does not
 * support paging, it is 4 'pages' long.
 */
#define TWO_ADDR_EEPROM_SIZE ((3 + OPTOE_ARCH_PAGES) * OPTOE_PAGE_SIZE)
#define TWO_ADDR_EEPROM_UNPAGED_SIZE (4 * OPTOE_PAGE_SIZE)
#define TWO_ADDR_NO_0X51_SIZE (2 * OPTOE_PAGE_SIZE)

/* a few constants to find our way around the EEPROM */
#define OPTOE_PAGE_SELECT_REG   0x7F
#define ONE_ADDR_PAGEABLE_REG 0x02
#define ONE_ADDR_NOT_PAGEABLE (1<<2)
#define TWO_ADDR_PAGEABLE_REG 0x40
#define TWO_ADDR_PAGEABLE (1<<4)
#define TWO_ADDR_0X51_REG 92
#define TWO_ADDR_0X51_SUPP (1<<6)
#define OPTOE_ID_REG 0
#define OPTOE_READ_OP 0
#define OPTOE_WRITE_OP 1
#define OPTOE_EOF 0  /* used for access beyond end of device */

struct optoe_data {
	struct optoe_platform_data chip;
	int use_smbus;
	char port_name[MAX_PORT_NAME_LEN];

	/*
	 * Lock protects against activities from other Linux tasks,
	 * but not from changes by other I2C masters.
	 */
	struct mutex lock;
	struct bin_attribute bin;
	struct attribute_group attr_group;

	u8 *writebuf;
	unsigned int write_max;

	unsigned int num_addresses;
	
	/* dev_class: ONE_ADDR (QSFP) or TWO_ADDR (SFP) */
	int dev_class;

	struct i2c_client *client[2];
	struct i2c_client *client_pca9641;
	struct mutex *lock_pca9641;
	struct i2c_client *client_pca9548[7];
	int id;
	struct kobject kobj;
};

static struct kobj_type ktype_optoe_default = {
	.sysfs_ops	= &kobj_sysfs_ops,
};

/*
 * This parameter is to help this driver avoid blocking other drivers out
 * of I2C for potentially troublesome amounts of time. With a 100 kHz I2C
 * clock, one 256 byte read takes about 1/43 second which is excessive;
 * but the 1/170 second it takes at 400 kHz may be quite reasonable; and
 * at 1 MHz (Fm+) a 1/430 second delay could easily be invisible.
 *
 * This value is forced to be a power of two so that writes align on pages.
 */
static unsigned int io_limit = OPTOE_PAGE_SIZE;

/*
 * specs often allow 5 msec for a page write, sometimes 20 msec;
 * it's important to recover from write timeouts.
 */
static unsigned int write_timeout = 25;

/*
 * flags to distinguish one-address (QSFP family) from two-address (SFP family)
 * If the family is not known, figure it out when the device is accessed
 */
#define ONE_ADDR 1
#define TWO_ADDR 2

static const struct i2c_device_id optoe_ids[] = {
	{ "inspur-optoe", 0x00 },
	{ /* END OF LIST */ }
};
MODULE_DEVICE_TABLE(i2c, optoe_ids);

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

static int pca954x_select_chan(struct i2c_client *client_pca9548[7], u32 chan)
{
	u8 chip;
	u8 regval;
	int ret = 0;
	
	if (chan > 55) {
		return -ENODEV;
	}

	chip = chan / 8;
	regval = 1 << (chan % 8);
	
	// Other master may select some pca9548 channels while CPU lose control of pca9641
	ret = pca954x_reg_write(client_pca9548[0], 0);
	if (ret < 0)
		return ret;
	ret = pca954x_reg_write(client_pca9548[1], 0);
	if (ret < 0)
		return ret;
	ret = pca954x_reg_write(client_pca9548[2], 0);
	if (ret < 0)
		return ret;
	ret = pca954x_reg_write(client_pca9548[3], 0);
	if (ret < 0)
		return ret;
	ret = pca954x_reg_write(client_pca9548[4], 0);
	if (ret < 0)
		return ret;
	ret = pca954x_reg_write(client_pca9548[5], 0);
	if (ret < 0)
		return ret;
	ret = pca954x_reg_write(client_pca9548[6], 0);
	if (ret < 0)
		return ret;
	
	ret = pca954x_reg_write(client_pca9548[chip], regval);
	dev_dbg(&client_pca9548[chip]->dev, "pca954x chip %d: channel select return: %d\n", chip, ret);
	
	return ret;
}

static int pca954x_deselect_chan(struct i2c_client *client_pca9548[7], u32 chan)
{
	u8 chip;
	int ret = 0;
	
	if (chan > 55) {
		return -ENODEV;
	}

	chip = chan / 8;
	
	ret = pca954x_reg_write(client_pca9548[chip], 0);
	dev_dbg(&client_pca9548[chip]->dev, "pca954x chip %d: deselect channel return: %d\n", chip, ret);
	
	return ret;
}

/*-------------------------------------------------------------------------*/
/*
 * This routine computes the addressing information to be used for
 * a given r/w request.
 *
 * Task is to calculate the client (0 = i2c addr 50, 1 = i2c addr 51),
 * the page, and the offset.
 *
 * Handles both single address (eg QSFP) and two address (eg SFP).
 *     For SFP, offset 0-255 are on client[0], >255 is on client[1]
 *     Offset 256-383 are on the lower half of client[1]
 *     Pages are accessible on the upper half of client[1].
 *     Offset >383 are in 128 byte pages mapped into the upper half
 *
 *     For QSFP, all offsets are on client[0]
 *     offset 0-127 are on the lower half of client[0] (no paging)
 *     Pages are accessible on the upper half of client[1].
 *     Offset >127 are in 128 byte pages mapped into the upper half
 *
 *     Callers must not read/write beyond the end of a client or a page
 *     without recomputing the client/page.  Hence offset (within page)
 *     plus length must be less than or equal to 128.  (Note that this
 *     routine does not have access to the length of the call, hence
 *     cannot do the validity check.)
 *
 * Offset within Lower Page 00h and Upper Page 00h are not recomputed
 */

static uint8_t optoe_translate_offset(struct optoe_data *optoe,
		loff_t *offset, struct i2c_client **client)
{
	unsigned int page = 0;

	*client = optoe->client[0];

	/* if SFP style, offset > 255, shift to i2c addr 0x51 */
	if (optoe->dev_class == TWO_ADDR) {
		if (*offset > 255) {
			/* like QSFP, but shifted to client[1] */
			*client = optoe->client[1];
			*offset -= 256;
		}
	}

	/*
	 * if offset is in the range 0-128...
	 * page doesn't matter (using lower half), return 0.
	 * offset is already correct (don't add 128 to get to paged area)
	 */
	if (*offset < OPTOE_PAGE_SIZE)
		return page;

	/* note, page will always be positive since *offset >= 128 */
	page = (*offset >> 7)-1;
	/* 0x80 places the offset in the top half, offset is last 7 bits */
	*offset = OPTOE_PAGE_SIZE + (*offset & 0x7f);

	return page;  /* note also returning client and offset */
}

static ssize_t optoe_eeprom_read(struct optoe_data *optoe,
		    struct i2c_client *client,
		    char *buf, unsigned int offset, size_t count)
{
	struct i2c_msg msg[2];
	u8 msgbuf[2];
	unsigned long timeout, read_time;
	int status, i;

	memset(msg, 0, sizeof(msg));

	switch (optoe->use_smbus) {
	case I2C_SMBUS_I2C_BLOCK_DATA:
		/*smaller eeproms can work given some SMBus extension calls */
		if (count > I2C_SMBUS_BLOCK_MAX)
			count = I2C_SMBUS_BLOCK_MAX;
		break;
	case I2C_SMBUS_WORD_DATA:
		/* Check for odd length transaction */
		count = (count == 1) ? 1 : 2;
		break;
	case I2C_SMBUS_BYTE_DATA:
		count = 1;
		break;
	default:
		/*
		 * When we have a better choice than SMBus calls, use a
		 * combined I2C message. Write address; then read up to
		 * io_limit data bytes.  msgbuf is u8 and will cast to our
		 * needs.
		 */
		i = 0;
		msgbuf[i++] = offset;

		msg[0].addr = client->addr;
		msg[0].buf = msgbuf;
		msg[0].len = i;

		msg[1].addr = client->addr;
		msg[1].flags = I2C_M_RD;
		msg[1].buf = buf;
		msg[1].len = count;
	}

	/*
	 * Reads fail if the previous write didn't complete yet. We may
	 * loop a few times until this one succeeds, waiting at least
	 * long enough for one entire page write to work.
	 */
	timeout = jiffies + msecs_to_jiffies(write_timeout);
	do {
		read_time = jiffies;

		switch (optoe->use_smbus) {
		case I2C_SMBUS_I2C_BLOCK_DATA:
			status = i2c_smbus_read_i2c_block_data(client, offset,
					count, buf);
			break;
		case I2C_SMBUS_WORD_DATA:
			status = i2c_smbus_read_word_data(client, offset);
			if (status >= 0) {
				buf[0] = status & 0xff;
				if (count == 2)
					buf[1] = status >> 8;
				status = count;
			}
			break;
		case I2C_SMBUS_BYTE_DATA:
			status = i2c_smbus_read_byte_data(client, offset);
			if (status >= 0) {
				buf[0] = status;
				status = count;
			}
			break;
		default:
			status = i2c_transfer(client->adapter, msg, 2);
			if (status == 2)
				status = count;
		}

		dev_dbg(&client->dev, "eeprom read %zu@%d --> %d (%ld)\n",
				count, offset, status, jiffies);

		if (status == count)  /* happy path */
			return count;

		if (status == -ENXIO) /* no module present */
			return status;

		/* REVISIT: at HZ=100, this is sloooow */
		usleep_range(1000, 2000);
	} while (time_before(read_time, timeout));

	return -ETIMEDOUT;
}

static ssize_t optoe_eeprom_write(struct optoe_data *optoe,
				struct i2c_client *client,
				const char *buf,
				unsigned int offset, size_t count)
{
	struct i2c_msg msg;
	ssize_t status;
	unsigned long timeout, write_time;
	unsigned int next_page_start;
	int i = 0;

	/* write max is at most a page
	 * (In this driver, write_max is actually one byte!)
	 */
	if (count > optoe->write_max)
		count = optoe->write_max;

	/* shorten count if necessary to avoid crossing page boundary */
	next_page_start = roundup(offset + 1, OPTOE_PAGE_SIZE);
	if (offset + count > next_page_start)
		count = next_page_start - offset;

	switch (optoe->use_smbus) {
	case I2C_SMBUS_I2C_BLOCK_DATA:
		/*smaller eeproms can work given some SMBus extension calls */
		if (count > I2C_SMBUS_BLOCK_MAX)
			count = I2C_SMBUS_BLOCK_MAX;
		break;
	case I2C_SMBUS_WORD_DATA:
		/* Check for odd length transaction */
		count = (count == 1) ? 1 : 2;
		break;
	case I2C_SMBUS_BYTE_DATA:
		count = 1;
		break;
	default:
		/* If we'll use I2C calls for I/O, set up the message */
		msg.addr = client->addr;
		msg.flags = 0;

		/* msg.buf is u8 and casts will mask the values */
		msg.buf = optoe->writebuf;

		msg.buf[i++] = offset;
		memcpy(&msg.buf[i], buf, count);
		msg.len = i + count;
		break;
	}

	/*
	 * Reads fail if the previous write didn't complete yet. We may
	 * loop a few times until this one succeeds, waiting at least
	 * long enough for one entire page write to work.
	 */
	timeout = jiffies + msecs_to_jiffies(write_timeout);
	do {
		write_time = jiffies;

		switch (optoe->use_smbus) {
		case I2C_SMBUS_I2C_BLOCK_DATA:
			status = i2c_smbus_write_i2c_block_data(client,
						offset, count, buf);
			if (status == 0)
				status = count;
			break;
		case I2C_SMBUS_WORD_DATA:
			if (count == 2) {
				status = i2c_smbus_write_word_data(client,
					offset, (u16)((buf[0])|(buf[1] << 8)));
			} else {
				/* count = 1 */
				status = i2c_smbus_write_byte_data(client,
					offset, buf[0]);
			}
			if (status == 0)
				status = count;
			break;
		case I2C_SMBUS_BYTE_DATA:
			status = i2c_smbus_write_byte_data(client, offset,
						buf[0]);
			if (status == 0)
				status = count;
			break;
		default:
			status = i2c_transfer(client->adapter, &msg, 1);
			if (status == 1)
				status = count;
			break;
		}

		dev_dbg(&client->dev, "eeprom write %zu@%d --> %ld (%lu)\n",
				count, offset, (long int) status, jiffies);

		if (status == count)
			return count;

		/* REVISIT: at HZ=100, this is sloooow */
		usleep_range(1000, 2000);
	} while (time_before(write_time, timeout));

	return -ETIMEDOUT;
}


static ssize_t optoe_eeprom_update_client(struct optoe_data *optoe,
				char *buf, loff_t off,
				size_t count, int opcode)
{
	struct i2c_client *client;
	ssize_t retval = 0;
	uint8_t page = 0;
	loff_t phy_offset = off;
	int ret = 0;

	page = optoe_translate_offset(optoe, &phy_offset, &client);
	dev_dbg(&client->dev,
		"%s off %lld  page:%d phy_offset:%lld, count:%ld, opcode:%d\n",
		__func__, off, page, phy_offset, (long int) count, opcode);
	if (page > 0) {
		ret = optoe_eeprom_write(optoe, client, &page,
			OPTOE_PAGE_SELECT_REG, 1);
		if (ret < 0) {
			dev_dbg(&client->dev,
				"Write page register for page %d failed ret:%d!\n",
					page, ret);
			return ret;
		}
	}

	while (count) {
		ssize_t	status;

		if (opcode == OPTOE_READ_OP) {
			status =  optoe_eeprom_read(optoe, client,
				buf, phy_offset, count);
		} else {
			status =  optoe_eeprom_write(optoe, client,
				buf, phy_offset, count);
		}
		if (status <= 0) {
			if (retval == 0)
				retval = status;
			break;
		}
		buf += status;
		phy_offset += status;
		count -= status;
		retval += status;
	}


	if (page > 0) {
		/* return the page register to page 0 (why?) */
		page = 0;
		ret = optoe_eeprom_write(optoe, client, &page,
			OPTOE_PAGE_SELECT_REG, 1);
		if (ret < 0) {
			dev_err(&client->dev,
				"Restore page register to 0 failed:%d!\n", ret);
			/* error only if nothing has been transferred */
			if (retval == 0)
				retval = ret;
		}
	}
	return retval;
}

/*
 * Figure out if this access is within the range of supported pages.
 * Note this is called on every access because we don't know if the
 * module has been replaced since the last call.
 * If/when modules support more pages, this is the routine to update
 * to validate and allow access to additional pages.
 *
 * Returns updated len for this access:
 *     - entire access is legal, original len is returned.
 *     - access begins legal but is too long, len is truncated to fit.
 *     - initial offset exceeds supported pages, return OPTOE_EOF (zero)
 */
static ssize_t optoe_page_legal(struct optoe_data *optoe,
		loff_t off, size_t len)
{
	struct i2c_client *client = optoe->client[0];
	u8 regval;
	int status;
	size_t maxlen;

	if (off < 0)
		return -EINVAL;
	if (optoe->dev_class == TWO_ADDR) {
		/* SFP case */
		/* if only using addr 0x50 (first 256 bytes) we're good */
		if ((off + len) <= TWO_ADDR_NO_0X51_SIZE)
			return len;
		/* if offset exceeds possible pages, we're not good */
		if (off >= TWO_ADDR_EEPROM_SIZE)
			return OPTOE_EOF;
		/* in between, are pages supported? */
		status = optoe_eeprom_read(optoe, client, &regval,
				TWO_ADDR_PAGEABLE_REG, 1);
		if (status < 0)
			return status;  /* error out (no module?) */
		if (regval & TWO_ADDR_PAGEABLE) {
			/* Pages supported, trim len to the end of pages */
			maxlen = TWO_ADDR_EEPROM_SIZE - off;
		} else {
			/* pages not supported, trim len to unpaged size */
			if (off >= TWO_ADDR_EEPROM_UNPAGED_SIZE)
				return OPTOE_EOF;

			/* will be accessing addr 0x51, is that supported? */
			/* byte 92, bit 6 implies DDM support, 0x51 support */
			status = optoe_eeprom_read(optoe, client, &regval,
						TWO_ADDR_0X51_REG, 1);
			if (status < 0)
				return status;
			if (regval & TWO_ADDR_0X51_SUPP) {
				/* addr 0x51 is OK */
				maxlen = TWO_ADDR_EEPROM_UNPAGED_SIZE - off;
			} else {
				/* addr 0x51 NOT supported, trim to 256 max */
				if (off >= TWO_ADDR_NO_0X51_SIZE)
					return OPTOE_EOF;
				maxlen = TWO_ADDR_NO_0X51_SIZE - off;
			}
		}
		len = (len > maxlen) ? maxlen : len;
		dev_dbg(&client->dev,
			"page_legal, SFP, off %lld len %ld\n",
			off, (long int) len);
	} else {
		/* QSFP case */
		/* if no pages needed, we're good */
		if ((off + len) <= ONE_ADDR_EEPROM_UNPAGED_SIZE)
			return len;
		/* if offset exceeds possible pages, we're not good */
		if (off >= ONE_ADDR_EEPROM_SIZE)
			return OPTOE_EOF;
		/* in between, are pages supported? */
		status = optoe_eeprom_read(optoe, client, &regval,
				ONE_ADDR_PAGEABLE_REG, 1);
		if (status < 0)
			return status;  /* error out (no module?) */
		if (regval & ONE_ADDR_NOT_PAGEABLE) {
			/* pages not supported, trim len to unpaged size */
			if (off >= ONE_ADDR_EEPROM_UNPAGED_SIZE)
				return OPTOE_EOF;
			maxlen = ONE_ADDR_EEPROM_UNPAGED_SIZE - off;
		} else {
			/* Pages supported, trim len to the end of pages */
			maxlen = ONE_ADDR_EEPROM_SIZE - off;
		}
		len = (len > maxlen) ? maxlen : len;
		dev_dbg(&client->dev,
			"page_legal, QSFP, off %lld len %ld\n",
			off, (long int) len);
	}
	return len;
}

static ssize_t optoe_read_write(struct optoe_data *optoe,
		char *buf, loff_t off, size_t len, int opcode)
{
	struct i2c_client *client = optoe->client[0];
	int chunk;
	int status = 0;
	ssize_t retval;
	size_t pending_len = 0, chunk_len = 0;
	loff_t chunk_offset = 0, chunk_start_offset = 0;
	loff_t chunk_end_offset = 0;

	dev_dbg(&client->dev,
		"%s: off %lld  len:%ld, opcode:%s\n",
		__func__, off, (long int) len,
		(opcode == OPTOE_READ_OP) ? "r" : "w");
	if (unlikely(!len))
		return len;

	/*
	 * Read data from chip, protecting against concurrent updates
	 * from this host, but not from other I2C masters.
	 */
	mutex_lock(&optoe->lock);

	/*
	 * Confirm this access fits within the device suppored addr range
	 */
	status = optoe_page_legal(optoe, off, len);
	if ((status == OPTOE_EOF) || (status < 0)) {
		mutex_unlock(&optoe->lock);
		return status;
	}
	len = status;

	/*
	 * For each (128 byte) chunk involved in this request, issue a
	 * separate call to sff_eeprom_update_client(), to
	 * ensure that each access recalculates the client/page
	 * and writes the page register as needed.
	 * Note that chunk to page mapping is confusing, is different for
	 * QSFP and SFP, and never needs to be done.  Don't try!
	 */
	pending_len = len; /* amount remaining to transfer */
	retval = 0;  /* amount transferred */
	for (chunk = off >> 7; chunk <= (off + len - 1) >> 7; chunk++) {

		/*
		 * Compute the offset and number of bytes to be read/write
		 *
		 * 1. start at an offset not equal to 0 (within the chunk)
		 *    and read/write less than the rest of the chunk
		 * 2. start at an offset not equal to 0 and read/write the rest
		 *    of the chunk
		 * 3. start at offset 0 (within the chunk) and read/write less
		 *    than entire chunk
		 * 4. start at offset 0 (within the chunk), and read/write
		 *    the entire chunk
		 */
		chunk_start_offset = chunk * OPTOE_PAGE_SIZE;
		chunk_end_offset = chunk_start_offset + OPTOE_PAGE_SIZE;

		if (chunk_start_offset < off) {
			chunk_offset = off;
			if ((off + pending_len) < chunk_end_offset)
				chunk_len = pending_len;
			else
				chunk_len = chunk_end_offset - off;
		} else {
			chunk_offset = chunk_start_offset;
			if (pending_len < OPTOE_PAGE_SIZE)
				chunk_len = pending_len;
			else
				chunk_len = OPTOE_PAGE_SIZE;
		}

		dev_dbg(&client->dev,
			"sff_r/w: off %lld, len %ld, chunk_start_offset %lld, chunk_offset %lld, chunk_len %ld, pending_len %ld\n",
			off, (long int) len, chunk_start_offset, chunk_offset,
			(long int) chunk_len, (long int) pending_len);

		/*
		 * note: chunk_offset is from the start of the EEPROM,
		 * not the start of the chunk
		 */
		status = optoe_eeprom_update_client(optoe, buf,
				chunk_offset, chunk_len, opcode);
		if (status != chunk_len) {
			/* This is another 'no device present' path */
			dev_dbg(&client->dev,
			"o_u_c: chunk %d c_offset %lld c_len %ld failed %d!\n",
			chunk, chunk_offset, (long int) chunk_len, status);
			if (status > 0)
				retval += status;
			if (retval == 0)
				retval = status;
			break;
		}
		buf += status;
		pending_len -= status;
		retval += status;
	}
	mutex_unlock(&optoe->lock);

	return retval;
}

static ssize_t optoe_bin_read(struct file *filp, struct kobject *kobj,
		struct bin_attribute *attr,
		char *buf, loff_t off, size_t count)
{
	ssize_t ret;
	struct i2c_client *client_pca9641;
	struct mutex *lock_pca9641;
	struct i2c_client **client_pca9548;
	struct optoe_data *optoe = container_of(kobj, struct optoe_data, kobj);

	client_pca9641 = optoe->client_pca9641;
	lock_pca9641 = optoe->lock_pca9641;
	client_pca9548 = optoe->client_pca9548;

	mutex_lock(lock_pca9641);
	ret = pca9641_select_chan(client_pca9641, 0);
	if (ret < 0)
		goto err;
	
	ret = pca954x_select_chan(client_pca9548, optoe->id);
	if (ret < 0)
		goto err_1;
	
	ret = optoe_read_write(optoe, buf, off, count, OPTOE_READ_OP);
	
	pca954x_deselect_chan(client_pca9548, optoe->id);
	
	pca9641_release_chan(client_pca9641, 0);
	mutex_unlock(lock_pca9641);
	
	return ret;

err_1:
	pca9641_release_chan(client_pca9641, 0);
err:
	mutex_unlock(lock_pca9641);
	return ret;
}

static ssize_t optoe_bin_write(struct file *filp, struct kobject *kobj,
		struct bin_attribute *attr,
		char *buf, loff_t off, size_t count)
{
	ssize_t ret;
	struct i2c_client *client_pca9641;
	struct mutex *lock_pca9641;
	struct i2c_client **client_pca9548;
	struct optoe_data *optoe = container_of(kobj, struct optoe_data, kobj);
	
	client_pca9641 = optoe->client_pca9641;
	lock_pca9641 = optoe->lock_pca9641;
	client_pca9548 = optoe->client_pca9548;

	mutex_lock(lock_pca9641);
	ret = pca9641_select_chan(client_pca9641, 0);
	if (ret < 0) {
		goto err;
	}
	
	ret = pca954x_select_chan(client_pca9548, optoe->id);
	if (ret < 0) {
		goto err_1;
	}
	
	ret = optoe_read_write(optoe, buf, off, count, OPTOE_WRITE_OP);
	
	pca954x_deselect_chan(client_pca9548, optoe->id);
	
	pca9641_release_chan(client_pca9641, 0);
	mutex_unlock(lock_pca9641);
	
	return ret;

err_1:
	pca9641_release_chan(client_pca9641, 0);
err:
	mutex_unlock(lock_pca9641);
	return ret;
}

static int optoe_remove(struct i2c_client *client)
{
	struct optoe_data *optoe;
	int i;
	struct i2c_client *client_pca9641;
	struct pca9641 *data;
	struct mutex *lock_pca9641;
	struct i2c_client *client_pca9548[7];
	struct i2c_client *client_dummy;

	optoe = i2c_get_clientdata(client);
	
	client_pca9641 = optoe[0].client_pca9641;
	lock_pca9641 = optoe[0].lock_pca9641;
	memcpy(client_pca9548, optoe[0].client_pca9548, sizeof(client_pca9548));
	client_dummy = optoe[0].client[1];
	data = i2c_get_clientdata(client_pca9641);
	
	for (i = 0; i < 56; i++) {
		sysfs_remove_group(&optoe[i].kobj, &optoe[i].attr_group);
		sysfs_remove_bin_file(&optoe[i].kobj, &optoe[i].bin);
		kobject_put(&optoe[i].kobj);
		kfree(optoe[i].writebuf);
	}
	
	kfree(optoe);

	i2c_unregister_device(client_dummy);

	for (i = 0; i < 7; i++) {
		i2c_unregister_device(client_pca9548[i]);
	}
	
	kfree(lock_pca9641);

	kfree(data);

	i2c_unregister_device(client_pca9641);
	
	return 0;
}

static ssize_t show_dev_class(struct kobject *kobj, struct kobj_attribute *attr, char *buf)
{
	ssize_t count;
	struct optoe_data *optoe = container_of(kobj, struct optoe_data, kobj);
	
	mutex_lock(&optoe->lock);
	count = sprintf(buf, "%d\n", optoe->dev_class);
	mutex_unlock(&optoe->lock);
	
	return count;
}

static ssize_t set_dev_class(struct kobject *kobj, struct kobj_attribute *attr, const char *buf, size_t count)
{
	int dev_class;
	struct optoe_data *optoe = container_of(kobj, struct optoe_data, kobj);
	
	/*
	 * dev_class is actually the number of i2c addresses used, thus
	 * legal values are "1" (QSFP class) and "2" (SFP class)
	 */

	if (kstrtoint(buf, 0, &dev_class) != 0 ||
		dev_class < 1 || dev_class > 2)
		return -EINVAL;

	mutex_lock(&optoe->lock);
	optoe->dev_class = dev_class;
	mutex_unlock(&optoe->lock);

	return count;
}

/*
 * if using the EEPROM CLASS driver, we don't report a port_name,
 * the EEPROM CLASS drive handles that.  Hence all this code is
 * only compiled if we are NOT using the EEPROM CLASS driver.
 */
static ssize_t show_port_name(struct kobject *kobj, struct kobj_attribute *attr, char *buf)
{
	ssize_t count;
	struct optoe_data *optoe = container_of(kobj, struct optoe_data, kobj);

	mutex_lock(&optoe->lock);
	count = sprintf(buf, "%s\n", optoe->port_name);
	mutex_unlock(&optoe->lock);

	return count;
}

static ssize_t set_port_name(struct kobject *kobj, struct kobj_attribute *attr, const char *buf, size_t count)
{
	char port_name[MAX_PORT_NAME_LEN];
	struct optoe_data *optoe = container_of(kobj, struct optoe_data, kobj);

	/* no checking, this value is not used except by show_port_name */

	if (sscanf(buf, "%19s", port_name) != 1)
		return -EINVAL;

	mutex_lock(&optoe->lock);
	strcpy(optoe->port_name, port_name);
	mutex_unlock(&optoe->lock);

	return count;
}

static struct kobj_attribute attr_port_name = __ATTR(port_name, 0664, show_port_name, set_port_name);

static struct kobj_attribute attr_dev_class = __ATTR(dev_class, 0664, show_dev_class, set_dev_class);

static struct attribute *optoe_attrs[] = {
	&attr_port_name.attr,
	&attr_dev_class.attr,
	NULL,
};

static struct attribute_group optoe_attr_group = {
	.attrs = optoe_attrs,
};

static struct i2c_board_info pca9641_i2c_board_info = {
	I2C_BOARD_INFO("pca9641_0x09", 0x09),
};

static struct i2c_board_info pca9548_i2c_board_info[7] = {
	{
		I2C_BOARD_INFO("pca9548_0x70", 0x70),
	},
	{
		I2C_BOARD_INFO("pca9548_0x71", 0x71),
	},
	{
		I2C_BOARD_INFO("pca9548_0x72", 0x72),
	},
	{
		I2C_BOARD_INFO("pca9548_0x73", 0x73),
	},
	{
		I2C_BOARD_INFO("pca9548_0x74", 0x74),
	},
	{
		I2C_BOARD_INFO("pca9548_0x75", 0x75),
	},
	{
		I2C_BOARD_INFO("pca9548_0x76", 0x76),
	},
};

static int optoe_probe(struct i2c_client *client,
			const struct i2c_device_id *id)
{
	int err;
	int use_smbus = 0;
	int muxes_use_smbus = false;
	struct optoe_platform_data chip;
	struct optoe_data *optoe;
	int num_addresses = 0;
	char port_name[MAX_PORT_NAME_LEN];
	struct i2c_client *client_pca9641;
	struct pca9641 *pca9641_data;
	struct mutex *lock_pca9641;
	struct i2c_client *client_pca9548[7];
	struct pca954x *pca9548_data;
	struct i2c_client *client_dummy;
	int i, j, k;
	
	dev_dbg(&client->dev, "probe start\n");
	
	if (client->addr != 0x50) {
		err = -EINVAL;
		dev_err(&client->dev, "probe, bad i2c addr: 0x%x\n", client->addr);
		goto exit;
	}
	
	/* Use I2C operations unless we're stuck with SMBus extensions. */
	if (!i2c_check_functionality(client->adapter, I2C_FUNC_I2C)) {
		/* check the i2c functionality for pca9548 and pca9641 */
		if (!i2c_check_functionality(client->adapter, I2C_FUNC_SMBUS_BYTE | I2C_FUNC_SMBUS_BYTE_DATA)) {
			err = -ENODEV;
			dev_err(&client->dev, "i2c functionality check for pca9641 and pca9548 failed.\n");
			goto exit;
		}
		muxes_use_smbus = true;

		if (i2c_check_functionality(client->adapter,
				I2C_FUNC_SMBUS_READ_I2C_BLOCK)) {
			use_smbus = I2C_SMBUS_I2C_BLOCK_DATA;
		} else if (i2c_check_functionality(client->adapter,
				I2C_FUNC_SMBUS_READ_WORD_DATA)) {
			use_smbus = I2C_SMBUS_WORD_DATA;
		} else if (i2c_check_functionality(client->adapter,
				I2C_FUNC_SMBUS_READ_BYTE_DATA)) {
			use_smbus = I2C_SMBUS_BYTE_DATA;
		} else {
			err = -EPFNOSUPPORT;
			dev_err(&client->dev, "i2c functionality check for optoe failed.\n");
			goto exit;
		}
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
	pca9641_data->muxes_use_smbus = muxes_use_smbus;
	i2c_set_clientdata(client_pca9641, pca9641_data);
	
	lock_pca9641 = kzalloc(sizeof(struct mutex), GFP_KERNEL);
	if (!lock_pca9641) {
		err = -ENOMEM;
		dev_err(&client->dev, "memory allocate for pca9641 mutex failed.\n");
		goto exit_2;
	}
	mutex_init(lock_pca9641);
	
	for (i = 0; i < 7; i++) {
		client_pca9548[i] = i2c_new_device(client->adapter, &pca9548_i2c_board_info[i]);
		if (!client_pca9548[i]) {
			err = -ENODEV;
			dev_err(&client->dev, "create pca9548_%d i2c client failed.\n", i);
			goto exit_3;
		}
	}

	pca9548_data = kzalloc(sizeof(struct pca954x), GFP_KERNEL);
	if (!pca9548_data) {
		err = -ENOMEM;
		dev_err(&client->dev, "memory allocate for pca9548 data failed.\n");
		goto exit_3;
	}
	pca9548_data->muxes_use_smbus = muxes_use_smbus;
	for (k = 0; k < 7; k++) {
		i2c_set_clientdata(client_pca9548[k], pca9548_data);
	}
	
	/* SFF-8472 spec requires that the second I2C address be 0x51 */
	client_dummy = i2c_new_dummy(client->adapter, 0x51);
	if (!client_dummy) {
		err = -EADDRINUSE;
		dev_err(&client->dev, "address 0x51 unavailable\n");
		goto exit_4;
	}
	
	optoe = kzalloc(sizeof(struct optoe_data) * 56, GFP_KERNEL);
	if (!optoe) {
		err = -ENOMEM;
		dev_err(&client->dev, "memory allocate for optoe failed.\n");
		goto exit_5;
	}
	
	for (j = 0; j < 56; j++) {
		dev_dbg(&client->dev, "building optoe[%d] chip\n", j);
		strcpy(port_name, "unitialized");
		chip.flags = 0;

		mutex_init(&optoe[j].lock);
		
		/* determine whether this is a one-address or two-address module */
		if (j < 48) {
			/* SFP family */
			optoe[j].dev_class = TWO_ADDR;
			chip.byte_len = TWO_ADDR_EEPROM_SIZE;
			num_addresses = 2;
		} else {
			/* one-address (eg QSFP) family */
			optoe[j].dev_class = ONE_ADDR;
			chip.byte_len = ONE_ADDR_EEPROM_SIZE;
			num_addresses = 1;
		}
		
		dev_dbg(&client->dev, "optoe[%d] dev_class: %d\n", j, optoe[j].dev_class);
		optoe[j].use_smbus = use_smbus;
		optoe[j].chip = chip;
		optoe[j].num_addresses = num_addresses;
		memcpy(optoe[j].port_name, port_name, MAX_PORT_NAME_LEN);
		optoe[j].id = j;
		
		/*
		 * Export the EEPROM bytes through sysfs, since that's convenient.
		 * By default, only root should see the data (maybe passwords etc)
		 */
		sysfs_bin_attr_init(&optoe[j].bin);
		optoe[j].bin.attr.name = "eeprom";
		optoe[j].bin.attr.mode = 0444;
		optoe[j].bin.read = optoe_bin_read;
		optoe[j].bin.size = chip.byte_len;
	
		if (!use_smbus ||
				(i2c_check_functionality(client->adapter,
					I2C_FUNC_SMBUS_WRITE_I2C_BLOCK)) ||
				i2c_check_functionality(client->adapter,
					I2C_FUNC_SMBUS_WRITE_WORD_DATA) ||
				i2c_check_functionality(client->adapter,
					I2C_FUNC_SMBUS_WRITE_BYTE_DATA)) {
			/*
			 * NOTE: AN-2079
			 * Finisar recommends that the host implement 1 byte writes
			 * only since this module only supports 32 byte page boundaries.
			 * 2 byte writes are acceptable for PE and Vout changes per
			 * Application Note AN-2071.
			 */
			unsigned int write_max = 1;
	
			optoe[j].bin.write = optoe_bin_write;
			optoe[j].bin.attr.mode |= 0200;
	
			if (write_max > io_limit)
				write_max = io_limit;
			if (use_smbus && write_max > I2C_SMBUS_BLOCK_MAX)
				write_max = I2C_SMBUS_BLOCK_MAX;
			optoe[j].write_max = write_max;
	
			/* buffer (data + address at the beginning) */
			optoe[j].writebuf = kmalloc(write_max + 2, GFP_KERNEL);
			if (!optoe[j].writebuf) {
				err = -ENOMEM;
				dev_err(&client->dev, "memory allocate for optoe[%d] writebuf failed.\n", j);
				goto err;
			}
		} else {
			dev_warn(&client->dev,
				"optoe[%d]: cannot write due to controller restrictions.\n", j);
		}
	
		optoe[j].client[0] = client;
		optoe[j].client[1] = client_dummy;
		optoe[j].client_pca9641 = client_pca9641;
		optoe[j].lock_pca9641 = lock_pca9641;
		memcpy(optoe[j].client_pca9548, client_pca9548, sizeof(client_pca9548));
		
		err = kobject_init_and_add(&optoe[j].kobj, &ktype_optoe_default, &client->dev.kobj, "optoe%d", j);
		if (err < 0) {
			dev_err(&client->dev, "optoe[%d] failed to create sysfs entry\n", j);
			goto err_1;
		}
		
		/* create the sysfs eeprom file */
		err = sysfs_create_bin_file(&optoe[j].kobj, &optoe[j].bin);
		if (err) {
			dev_err(&client->dev, "optoe[%d] failed to create sysfs bin attribute.\n", j);
			goto err_2;
		}

		optoe[j].attr_group = optoe_attr_group;

		err = sysfs_create_group(&optoe[j].kobj, &optoe[j].attr_group);
		if (err) {
			dev_err(&client->dev, "optoe[%d] failed to create sysfs attribute group.\n", j);
			goto err_3;
		}
		
		dev_info(&client->dev, "optoe[%d], %zu byte EEPROM, %s\n",
			j, optoe[j].bin.size, optoe[j].bin.write ? "read/write" : "read-only");
		
		if (use_smbus == I2C_SMBUS_WORD_DATA ||
			use_smbus == I2C_SMBUS_BYTE_DATA) {
			dev_notice(&client->dev,
				"optoe[%d], falling back to %s reads, performance will suffer\n",
				j, use_smbus == I2C_SMBUS_WORD_DATA ? "word" : "byte");
		}
		
	}
	
	i2c_set_clientdata(client, optoe);

	return 0;

err_3:
	sysfs_remove_bin_file(&optoe[j].kobj, &optoe[j].bin);
err_2:
	kobject_put(&optoe[j].kobj);
err_1:
	kfree(optoe[j].writebuf);
err:
	for (j--; j >= 0; j--) {
		sysfs_remove_group(&optoe[j].kobj, &optoe[j].attr_group);
		sysfs_remove_bin_file(&optoe[j].kobj, &optoe[j].bin);
		kobject_put(&optoe[j].kobj);
		kfree(optoe[j].writebuf);
	}
	
	kfree(optoe);
exit_5:
	i2c_unregister_device(client_dummy);
exit_4:
	kfree(pca9548_data);
exit_3:
	for (i--; i >= 0; i--) {
		i2c_unregister_device(client_pca9548[i]);
	}
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

static struct i2c_driver optoe_driver = {
	.driver = {
		.name = "inspur-optoe",
		.owner = THIS_MODULE,
	},
	.probe = optoe_probe,
	.remove = optoe_remove,
	.id_table = optoe_ids,
};

static int __init optoe_init(void)
{

	if (!io_limit) {
		pr_err("optoe: io_limit must not be 0!\n");
		return -EINVAL;
	}

	io_limit = rounddown_pow_of_two(io_limit);
	return i2c_add_driver(&optoe_driver);
}
module_init(optoe_init);

static void __exit optoe_exit(void)
{
	i2c_del_driver(&optoe_driver);
}
module_exit(optoe_exit);

MODULE_DESCRIPTION("Driver for optical transceiver (SFP, QSFP, ...) EEPROMs");
MODULE_AUTHOR("DON BOLLINGER <don@thebollingers.org>");
MODULE_LICENSE("GPL");
