/*
 **********************************************************************
 *
 * @filename  bms_xcvr_access.c
 *
 * @purpose   access EEPROM of transceiver module
 *
 * @create    2017/3/17
 *
 * @author    yencheng.lin <yencheng.lin@mic.com.tw>
 *
 * @history   2017/3/17: init version
 *
 **********************************************************************
 */

#include <stdio.h>
#include <errno.h>
#include <fcntl.h>
#include <string.h>
#include <unistd.h>
#include <sys/syslog.h>
#include <linux/i2c-dev.h>
#include "bms_xcvr_access.h"

#define DISABLE_MASK 0xFF

#define SFF_UPPER_PAGE_BYTE_START 128
#define HIGH_POWER_CLASS_MASK 0x03
#define LEGACY_POWER_CLASS_MASK 0xC0

#define XCVR_HW_INTR_MASK_START 100
#define XCVR_CHANNEL_INTR_MASK_START 242
#define XCVR_HW_INTR_MASK_PAGE 0
#define XCVR_CHANNEL_INTR_MASK_PAGE 3
#define XCVR_HW_INTR_MASK_BYTES 5
#define XCVR_CHANNEL_INTR_MASK_BYTES 6

/* TODO might be 0x50 or 0x51 */
unsigned char bms_xcvr_addr = 0x50;

static int bms_xcvr_i2c_open(unsigned char bus, int *i2c_fd);
static int bms_xcvr_i2c_read(unsigned char bus, unsigned char addr, unsigned short offset, unsigned char *val);
static int bms_xcvr_i2c_write(unsigned char bus, unsigned char addr, unsigned short offset, unsigned char val);

typedef struct {
    unsigned short page;
    unsigned short offset;
    unsigned char shift;
    unsigned char width;
} bms_xcvr_data_t;

bms_xcvr_data_t bms_xcvr_data_list[] = {
 /*page, offset, shift, width */
 {    0,      2,     0,     1 },/* "Data_Note_Ready" is bit0 of byte2 in the page0 */
 {    0,    127,     0,     8 },/* "Page Select" is byte128 in the page0 */
 {    0,      6,     0,     1 },/* "Initialization complete flag" is bit0 of byte 6 in the page0 */
 {    0,    129,     0,     8 },/* "Ext. Identifier" is bit0-1 of byte129 in the page0 */
 {    0,     93,     0,     3 },/* "Power Mode Control" is bit0-2 of byte 93 in the page0 */
};
int bms_xcvr_data_list_num = sizeof(bms_xcvr_data_list) / sizeof(bms_xcvr_data_list[0]);

/*
 * FEATURE:
 *   bms_xcvr_i2c_open
 * PURPOSE:
 *   low-level function to open an I2C adapter device file
 * PARAMETERS:
 *   bus                (IN) I2C bus to be looking for
 *   i2c_fd             (OUT) file descriptor
 * RETURNS:
 *   open success, this function returns .
 *   for other cases, negative errno is returned.
 */
static int
bms_xcvr_i2c_open(unsigned char bus,
                  int *i2c_fd)
{
    int err = 0;
    char dev_name[20];

    sprintf(dev_name, "/dev/i2c-%u", bus);
    if ((*i2c_fd = open(dev_name, O_RDWR)) < 0) {
        err = errno;
        syslog(LOG_DEBUG|LOG_USER,
            "[%s] could not open I2C adapter %s: %s\n",
            __func__, dev_name, strerror(err));
        return -err;
    }

    return err;
}

/*
 * FEATURE:
 *   bms_xcvr_i2c_read
 * PURPOSE:
 *   low-level function to read 8-bit data from an I2C slave component
 * PARAMETERS:
 *   bus                (IN) I2C bus to be looking for
 *   addr               (IN) I2C slave address of the transceiver
 *   offset             (IN) register offset
 *   val                (OUT) pointer of current value buffer
 * RETURNS:
 *   read success, this function returns 0.
 *   for other cases, negative errno is returned.
 */
static int
bms_xcvr_i2c_read(unsigned char bus,
                  unsigned char addr,
                  unsigned short offset,
                  unsigned char *val)
{
    int err = 0, value;
    int i2c_fd = 0;

    if ((err = bms_xcvr_i2c_open(bus, &i2c_fd)) < 0) {goto quit;}
    if ((ioctl(i2c_fd, I2C_SLAVE_FORCE, addr)) < 0) {
        err = errno;
        return -err;
    }
    value = i2c_smbus_read_byte_data(i2c_fd, offset);
    if (value < 0) {
        err = errno;
        syslog(LOG_DEBUG|LOG_USER,
            "[%s] could not read register 0x%X: %s\n",
            __func__, offset, strerror(err));
        close(i2c_fd);
        return -err;
    }
    *val = value;

quit:
    close(i2c_fd);
    return err;
}

/*
 * FEATURE:
 *   bms_xcvr_i2c_write
 * PURPOSE:
 *   low-level function to write 8-bit data to an I2C slave component
 * PARAMETERS:
 *   bus                (IN) I2C bus to be looking for
 *   addr               (IN) I2C slave address of the transceiver
 *   offset             (IN) register offset
 *   val                (IN) new register value
 * RETURNS:
 *   write success, this function returns 0.
 *   for other cases, negative errno is returned.
 */
static int
bms_xcvr_i2c_write(unsigned char bus,
                   unsigned char addr,
                   unsigned short offset,
                   unsigned char val)
{
    int err = 0;
    int i2c_fd = 0;

    if ((err = bms_xcvr_i2c_open(bus, &i2c_fd)) < 0) {goto quit;}
    if ((ioctl(i2c_fd, I2C_SLAVE_FORCE, addr)) < 0) {
        err = errno;
        return -err;
    }
    if (i2c_smbus_write_byte_data(i2c_fd, offset, val) < 0) {
        err = errno;
        syslog(LOG_DEBUG|LOG_USER,
            "[%s] could not write register 0x%X: %s\n",
            __func__, offset, strerror(err));
        close(i2c_fd);
        return -err;
    }

quit:
    close(i2c_fd);
    return err;
}

/*
 * FEATURE:
 *   bms_xcvr_max_power_class
 * PURPOSE:
 *   setup max power class for high or legacy device
 * PARAMETERS:
 *   bus                (IN) I2C bus to be looking for
 *   addr               (IN) I2C slave address of transceiver
 *   legacy_power       (IN) 1 means power class 2-4 and 0 means power class 5-7
 * RETURNS:
 *   set success, this function returns 0.
 *   for other cases, negative errno is returned.
 */
int
bms_xcvr_max_power_class(unsigned char bus,
                         unsigned char addr,
                         unsigned char legacy_power)
{
    int err = 0, item = REG_POWER_MODE_CONTROL;
    unsigned short val = (legacy_power ? 0x1 : 0x5);

    err = bms_xcvr_i2c_write( bus, addr, bms_xcvr_data_list[item].offset, val);
    return err;
}

/*
 * FEATURE:
 *   bms_xcvr_min_power_class
 * PURPOSE:
 *   setup minpower class for high or legacy device
 * PARAMETERS:
 *   bus                (IN) I2C bus to be looking for
 *   addr               (IN) I2C slave address of transceiver
 * RETURNS:
 *   set success, this function returns 0.
 *   for other cases, negative errno is returned.
 */
int
bms_xcvr_min_power_class(unsigned char bus,
                         unsigned char addr)
{
    int err = 0, item = REG_POWER_MODE_CONTROL;
    unsigned short val = 0x7; /* Legacy device will skip bit2 */

    err = bms_xcvr_i2c_write( bus, addr, bms_xcvr_data_list[item].offset, val);
    return err;
}

/*
 * FEATURE:
 *   bms_xcvr_read
 * PURPOSE:
 *   read register of transceiver
 * PARAMETERS:
 *   bus                (IN) I2C bus to be looking for
 *   addr               (IN) I2C slave address of transceiver
 *   reg_item           (IN) the regitster of transceiver
 *   value              (OUT) pointer of current value buffer
 * RETURNS:
 *   read success, this function returns 0.
 *   for other cases, negative errno is returned.
 */
int
bms_xcvr_read(unsigned char bus,
              unsigned char addr,
              int reg_item,
              unsigned char *value)
{
    int err = 0;
    unsigned short page = bms_xcvr_data_list[reg_item].page;
    unsigned short offset = bms_xcvr_data_list[reg_item].offset;
    unsigned char shift = bms_xcvr_data_list[reg_item].shift;
    unsigned char width = bms_xcvr_data_list[reg_item].width;
    unsigned char mask = ((((unsigned char)1) << (width)) - 1);
    unsigned char val = 0;

    if (offset >= SFF_UPPER_PAGE_BYTE_START) {
        val = page;
        if ((err = bms_xcvr_i2c_write( bus, addr, bms_xcvr_data_list[REG_PAGE_SELECT].offset, val)) < 0) {goto quit;}
    }
    if ((err = bms_xcvr_i2c_read( bus, addr, offset, &val)) < 0) {goto quit;}
    *value = ((val >> shift) & mask);
quit:
    return err;
}

/*
 * FEATURE:
 *   bms_xcvr_intr_mask
 * PURPOSE:
 *   mask interrupt for initianl process
 * PARAMETERS:
 *   bus                (IN) I2C bus to be looking for
 *   addr               (IN) I2C slave address of transceiver
 * RETURNS:
 *   set success, this function returns 0.
 *   for other cases, negative errno is returned.
 */
int
bms_xcvr_intr_mask(unsigned char bus,
                   unsigned char addr)
{
    int err = 0, i = 0, bytes = 0;
    unsigned short val = 0;

    /* Switch to register "Hardware Interrupt Pin Masks".
     * It starts from byte 100 of page 0 and includes the following 5 bytes.
     * When interrupt pin masks are 0xFF, the hardware interrupt will not trigger interrupt pin of transceiver.
     */
    val = XCVR_HW_INTR_MASK_PAGE;
    if ((err = bms_xcvr_i2c_write( bus, addr, bms_xcvr_data_list[REG_PAGE_SELECT].offset, val)) < 0) {goto quit;}
    bytes = XCVR_HW_INTR_MASK_BYTES;
    val = DISABLE_MASK;
    for (i = 0; i < bytes; i++) {
        if ((err = bms_xcvr_i2c_write( bus, addr, (XCVR_HW_INTR_MASK_START + i), val)) < 0) {goto quit;}
    }

    /* Switch to register "Channel Masks".
     * It starts from byte 242 of page 3 and includes the following 6 bytes.
     * When interrupt pin masks are 0xFF, the channel interrupt will not trigger interrupt pin of transceiver.
     */
    val = XCVR_CHANNEL_INTR_MASK_PAGE;
    if ((err = bms_xcvr_i2c_write( bus, addr, bms_xcvr_data_list[REG_PAGE_SELECT].offset, val)) < 0) {goto quit;}
    bytes = XCVR_CHANNEL_INTR_MASK_BYTES;
    val = DISABLE_MASK;
    for (i = 0; i < bytes; i++) {
        if ((err = bms_xcvr_i2c_write( bus, addr, (XCVR_CHANNEL_INTR_MASK_START + i), val)) < 0) {goto quit;}
    }
quit:
    return err;
}

/*
 * FEATURE:
 *   bms_xcvr_check_power_class
 * PURPOSE:
 *   check power class from transceiver register
 * PARAMETERS:
 *   xcvr_power_data    (IN) power data is from Power Class byte
 *   xcvr_power_class   (OUT) pointer of current value buffer
 * RETURNS:
 *   no.
 */
void
bms_xcvr_check_power_class(unsigned char xcvr_power_data,
                           unsigned char *xcvr_power_class)
{
    unsigned char value, power_class = 0;
    value = xcvr_power_data & HIGH_POWER_CLASS_MASK;
    if (value == 0)
        value = xcvr_power_data & LEGACY_POWER_CLASS_MASK;
    switch (value) {
        case 0x00: power_class = 1; break;
        case 0x40: power_class = 2; break;
        case 0x80: power_class = 3; break;
        case 0xC0: power_class = 4; break;
        case 0x01: power_class = 5; break;
        case 0x02: power_class = 6; break;
        case 0x03: power_class = 7; break;
        default: power_class = 1; break;
    }
    *xcvr_power_class = power_class;
}
