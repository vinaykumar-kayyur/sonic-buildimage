/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * optoe implementation for bf xcvr driver
 */

#define pr_fmt(fmt) "%s:%s: " fmt, KBUILD_MODNAME,  __func__

#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/hwmon-sysfs.h>
#include <linux/delay.h>
#include <linux/i2c.h>
#include "bf_module_util.h"
#include "bf_xcvr_driver.h"
#include "bf_fpga_i2c_util.h"

#define BF_FPGA_I2C_FUNTIONALITY I2C_SMBUS_I2C_BLOCK_DATA
#define BF_OPTOE_CLASS "optoe1" /* all QSFP ports on newport */
#define EEPROM_ADDR 0x50

/* fundamental unit of addressing for EEPROM */
#define OPTOE_PAGE_SIZE 128
/*
 * Single address devices (eg QSFP) have 256 pages, plus the unpaged
 * low 128 bytes.  If the device does not support paging, it is
 * only 2 'pages' long.
 */
#define OPTOE_ARCH_PAGES 256
#define ONE_ADDR_EEPROM_SIZE ((1 + OPTOE_ARCH_PAGES) * OPTOE_PAGE_SIZE)
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
#define QSFP_NOT_PAGEABLE (1<<2)
#define CMIS_NOT_PAGEABLE (1<<7)
#define TWO_ADDR_PAGEABLE_REG 0x40
#define TWO_ADDR_PAGEABLE (1<<4)
#define TWO_ADDR_0X51_REG 92
#define TWO_ADDR_0X51_SUPP (1<<6)
#define OPTOE_ID_REG 0
#define OPTOE_READ_OP 0
#define OPTOE_WRITE_OP 1
#define OPTOE_EOF 0  /* used for access beyond end of device */

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
#define CMIS_ADDR 3

/*-------------------------------------------------------------------------*/
static inline struct kobject* optoe_to_kobj(struct optoe_data *optoe)
{
    return &optoe->pdev->dev.kobj;
}

static inline int get_pdev_id(struct optoe_data *optoe)
{
    return optoe->pdev->id;
}

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
        loff_t *offset)
{
    unsigned int page = 0;

    /* if SFP style, offset > 255, shift to i2c addr 0x51 */
    if (optoe->dev_class == TWO_ADDR) {
        if (*offset > 255) {
            /* like QSFP, but shifted to client[1] */
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
            char *buf, uint8_t offset, size_t count)
{
    unsigned long timeout, read_time;
    int status;
    int bus_no = get_pdev_id(optoe);

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
        return -EINVAL;
    }

    /*
     * Reads fail if the previous write didn't complete yet. We may
     * loop a few times until this one succeeds, waiting at least
     * long enough for one entire page write to work.
     */
    timeout = jiffies + msecs_to_jiffies(write_timeout);
    do {
        read_time = jiffies;

        status = bf_fpga_i2c_addr_read(bus_no, WITHOUT_MUX, 0, EEPROM_ADDR,
                                           &offset, buf, 1, count);
        if (status == 0)
            status = count;
        else
            bf_print("bus%d eeprom read %zu@%d --> %d (%ld)\n",
                     bus_no, count, offset, status, jiffies);

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
                char *buf,
                uint8_t offset, size_t count)
{
    ssize_t status;
    unsigned long timeout, write_time;
    unsigned int next_page_start;
    int bus_no = get_pdev_id(optoe);

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
        return -EINVAL;
    }

    /*
     * Reads fail if the previous write didn't complete yet. We may
     * loop a few times until this one succeeds, waiting at least
     * long enough for one entire page write to work.
     */
    timeout = jiffies + msecs_to_jiffies(write_timeout);
    do {
        write_time = jiffies;


        status = bf_fpga_i2c_addr_write(bus_no, WITHOUT_MUX, 0, EEPROM_ADDR,
                                            &offset, 1, buf, count);
        if (status == 0)
            status = count;
        else
            bf_print("bus%d eeprom write %zu@%d --> %ld (%lu)\n",
                     bus_no, count, offset, (long int) status, jiffies);

        if (status == count)
            return count;

        /* REVISIT: at HZ=100, this is sloooow */
        usleep_range(1000, 2000);
    } while (time_before(write_time, timeout));

    return -ETIMEDOUT;
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
    u8 regval;
    int not_pageable;
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
        status = optoe_eeprom_read(optoe, &regval,
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
            status = optoe_eeprom_read(optoe, &regval,
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
        // bf_print( "page_legal, SFP, off %lld len %ld\n", off, (long int) len);
    } else {
        /* QSFP case, CMIS case */
        /* if no pages needed, we're good */
        if ((off + len) <= ONE_ADDR_EEPROM_UNPAGED_SIZE)
            return len;
        /* if offset exceeds possible pages, we're not good */
        if (off >= ONE_ADDR_EEPROM_SIZE)
            return OPTOE_EOF;
        /* in between, are pages supported? */
        status = optoe_eeprom_read(optoe, &regval,
                ONE_ADDR_PAGEABLE_REG, 1);
        if (status < 0)
            return status;  /* error out (no module?) */

        if (optoe->dev_class == ONE_ADDR) {
            not_pageable = QSFP_NOT_PAGEABLE;
        } else {
            not_pageable = CMIS_NOT_PAGEABLE;
        }
        // bf_print("Paging Register: 0x%x; not_pageable mask: 0x%x\n",
        //          regval, not_pageable);

        if (regval & not_pageable) {
            /* pages not supported, trim len to unpaged size */
            if (off >= ONE_ADDR_EEPROM_UNPAGED_SIZE)
                return OPTOE_EOF;
            maxlen = ONE_ADDR_EEPROM_UNPAGED_SIZE - off;
        } else {
            /* Pages supported, trim len to the end of pages */
            maxlen = ONE_ADDR_EEPROM_SIZE - off;
        }
        len = (len > maxlen) ? maxlen : len;
        // bf_print( "page_legal, QSFP, off %lld len %ld\n", off, (long int) len);
    }
    return len;
}

static ssize_t optoe_eeprom_update_client(struct optoe_data *optoe,
                char *buf, loff_t off,
                size_t count, int opcode)
{
    ssize_t retval = 0;
    uint8_t page = 0;
    loff_t phy_offset = off;
    int ret = 0;

    page = optoe_translate_offset(optoe, &phy_offset);
    // bf_print("%s off %lld  page:%d phy_offset:%lld, count:%ld, opcode:%d\n",
    //          __func__, off, page, phy_offset, (long int) count, opcode);
    if (page > 0) {
        ret = optoe_eeprom_write(optoe, &page,
            OPTOE_PAGE_SELECT_REG, 1);
        if (ret < 0) {
            bf_print( "Write page register for page %d failed ret:%d!\n",
                      page, ret);
            return ret;
        }
    }

    while (count) {
        ssize_t    status;

        if (opcode == OPTOE_READ_OP) {
            status =  optoe_eeprom_read(optoe,
                buf, phy_offset, count);
        } else {
            status =  optoe_eeprom_write(optoe,
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
        ret = optoe_eeprom_write(optoe, &page,
            OPTOE_PAGE_SELECT_REG, 1);
        if (ret < 0) {
            bf_print( "Restore page register to 0 failed:%d!\n", ret);
            /* error only if nothing has been transferred */
            if (retval == 0)
                retval = ret;
        }
    }
    return retval;
}

ssize_t optoe_read_write(struct optoe_data *optoe,
        char *buf, loff_t off, size_t len, int opcode)
{
    int chunk;
    int status = 0;
    ssize_t retval;
    size_t pending_len = 0, chunk_len = 0;
    loff_t chunk_offset = 0, chunk_start_offset = 0;
    loff_t chunk_end_offset = 0;

    bf_print("off %lld  len:%ld, opcode:%s\n",
             off, (long int) len,
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

        // bf_print(
        //     "sff_r/w: off %lld, len %ld, chunk_start_offset %lld, chunk_offset %lld, chunk_len %ld, pending_len %ld\n",
        //     off, (long int) len, chunk_start_offset, chunk_offset,
        //     (long int) chunk_len, (long int) pending_len);

        /*
         * note: chunk_offset is from the start of the EEPROM,
         * not the start of the chunk
         */
        status = optoe_eeprom_update_client(optoe, buf,
                chunk_offset, chunk_len, opcode);
        if (status != chunk_len) {
            /* This is another 'no device present' path */
            bf_print("o_u_c: chunk %d c_offset %lld c_len %ld failed %d!\n",
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
    struct device *dev = kobj_to_dev(kobj);
    struct optoe_data *optoe = dev_get_platdata(dev);
    return optoe_read_write(optoe, buf, off, count, OPTOE_READ_OP);
}


static ssize_t optoe_bin_write(struct file *filp, struct kobject *kobj,
        struct bin_attribute *attr,
        char *buf, loff_t off, size_t count)
{
    struct device *dev = kobj_to_dev(kobj);
    struct optoe_data *optoe = dev_get_platdata(dev);
    return optoe_read_write(optoe, buf, off, count, OPTOE_WRITE_OP);
}

int optoe_probe(struct platform_device *pdev, struct optoe_data *optoe)
{
    int err;
    const int use_smbus = BF_FPGA_I2C_FUNTIONALITY;
    int num_addresses = 0;
    unsigned int write_max = 1;

    if (!optoe) {
        err = -ENOMEM;
        goto exit;
    }
    mutex_init(&optoe->lock);
    optoe->pdev = pdev;

    /* determine whether this is a one-address or two-address module */
    if ((strcmp(BF_OPTOE_CLASS, "optoe1") == 0) ||
        (strcmp(BF_OPTOE_CLASS, "sff8436") == 0)) {
        /* one-address (eg QSFP) family */
        optoe->dev_class = ONE_ADDR;
        optoe->byte_len = ONE_ADDR_EEPROM_SIZE;
        num_addresses = 1;
    } else if ((strcmp(BF_OPTOE_CLASS, "optoe2") == 0) ||
           (strcmp(BF_OPTOE_CLASS, "24c04") == 0)) {
        /* SFP family */
        optoe->dev_class = TWO_ADDR;
        optoe->byte_len = TWO_ADDR_EEPROM_SIZE;
        num_addresses = 2;
    } else if (strcmp(BF_OPTOE_CLASS, "optoe3") == 0) {
        /* CMIS spec */
        optoe->dev_class = CMIS_ADDR;
        optoe->byte_len = ONE_ADDR_EEPROM_SIZE;
        num_addresses = 1;
    } else {     /* those were the only choices */
        err = -EINVAL;
        goto exit;
    }

    optoe->use_smbus = use_smbus;
    optoe->num_addresses = num_addresses;

    if (write_max > io_limit)
        write_max = io_limit;
    if (use_smbus && write_max > I2C_SMBUS_BLOCK_MAX)
        write_max = I2C_SMBUS_BLOCK_MAX;
    optoe->write_max = write_max;

    /*
     * Export the EEPROM bytes through sysfs, since that's convenient.
     * By default, only root should see the data (maybe passwords etc)
     */
    sysfs_bin_attr_init(&optoe->bin);
    optoe->bin.attr.name = "eeprom";
    optoe->bin.attr.mode = 0644;
    optoe->bin.read = optoe_bin_read;
    optoe->bin.write = optoe_bin_write;
    optoe->bin.size = optoe->byte_len;
    /* create the sysfs eeprom file */
    err = sysfs_create_bin_file(&pdev->dev.kobj, &optoe->bin);
    if (err)
        goto exit;

    return 0;

exit:
    bf_print("probe error %d\n", err);
    return err;
}

void optoe_remove(struct optoe_data *optoe)
{
    sysfs_remove_bin_file(optoe_to_kobj(optoe), &optoe->bin);
}
