/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * device attribute handler implementation for bf eeprom driver
 */

#define pr_fmt(fmt) "%s:%s: " fmt, KBUILD_MODNAME,  __func__

#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/hwmon-sysfs.h>
#include <linux/delay.h>
#include "bf_module_util.h"
#include "bf_eeprom_driver.h"
#include "bf_fpga_i2c_util.h"

#define MUX_CHN (0x40)
#define EEPROM_ADDR (0x51)
#define BUS_NO (32)
#define REGADDR_LEN (2)
#define PAGE_BITW (5)
#define PAGE_SZ (0x1 << PAGE_BITW)

extern struct bf_eeprom_drv_data *g_data;

ATTR_SHOW_STR_FUNC(bsp_ver, BSP_VERSION)

ATTR_SHOW_STR_FUNC(debug,
    "SYSEEPROM info:\n"
    "    I2C Bus id = 32\n"
    "    I2C mux chip addr = 0x74\n"
    "    I2C mux channel = 0x40 (6th)\n"
    "    SYSEEPROM chip addr = 0x51\n"
    "    SYSEEPROM reg addr size = 2 bytes\n"
    "\n"
    "Dump SYSEEPROM content:\n"
    "    Bytes 0-127:\n"
    "        $ fpga_util i2c_addr_read 0 32 0x74 0x40 0x51 128 2 0 0\n"
    "    Bytes 128-256:\n"
    "        $ fpga_util i2c_addr_read 0 32 0x74 0x40 0x51 128 2 0 128\n"
    "\n"
    "Reset its I2C bus:\n"
    "    $ echo 1 > /sys/switch/fpga/fpga1/reset_i2c32\n"
    "    $ sleep 1\n"
    "    $ echo 0 > /sys/switch/fpga/fpga1/reset_i2c32\n"
    "\n"
    "fpga_util usage:\n"
    "    fpga_util i2c_read <fpga_id> <bus> <mux_i2c_adr> <mux_chn> <i2c_addr> <length>\n"
    "    fpga_util i2c_write <fpga_id> <bus> <mux_i2c_adr> <mux_chn> <i2c_addr> <length> <byte1> [<byte2> ...]\n"
    "    fpga_util i2c_addr_read <fpga_id> <bus> <mux_i2c_adr> <mux_chn> <i2c_addr> <read_length> <write_length> <byte1> [<byte2> ...]\n"
    "    fpga_util reg_read <fpga_id> <reg_addr>\n"
    "    fpga_util reg_write <fpga_id> <reg_addr> <32bit data>\n"
)

inline void set_addr(uint8_t addr[REGADDR_LEN], loff_t off)
{
    addr[0] = (uint8_t) (( off >> 8) & 0xFF);
    addr[1] = (uint8_t) (off & 0xFF);
}

ssize_t eeprom_read(struct file *fp, struct kobject *kobj,
            struct bin_attribute *attr, char *buf, loff_t off, size_t count)
{
    uint8_t addr[REGADDR_LEN];
    size_t remain = count;
    uint8_t rd_sz;
    int ret;

    while(remain > 0) {
        rd_sz = (remain <= FPGA_I2C_MAX_DATA)? remain : FPGA_I2C_MAX_DATA;
        set_addr(addr, off);
        ret = bf_fpga_i2c_addr_read(BUS_NO, WITH_MUX, MUX_CHN, EEPROM_ADDR,
                                    addr, REGADDR_LEN, buf, rd_sz);
        if(ret != 0){
            bf_print("read sys eeprom fail (%s), addr(%lld), len(%d)\n",
                     bf_pltfm_err_str(ret), off, rd_sz);
            return count - remain;
        }
        buf += rd_sz;
        remain -= rd_sz;
        off += rd_sz;
    }
    return count;
}
ssize_t eeprom_write(struct file *fp, struct kobject *kobj,
            struct bin_attribute *attr, char *buf, loff_t off, size_t len)
{
    uint8_t addr[REGADDR_LEN];
    int ret;
    int chunk;
    ssize_t retval;
    size_t pending_len = 0, chunk_len = 0;
    loff_t chunk_offset = 0, chunk_start_offset = 0;
    loff_t chunk_end_offset = 0;

    if(off + len - 1 > EEPROM_SIZE)
        return -EINVAL;

    pending_len = len; /* amount remaining to transfer */
    retval = 0;  /* amount transferred */
    for(chunk = off >> PAGE_BITW ;
                chunk <= (off + len - 1) >> PAGE_BITW ; chunk++) {

        /* make sure each write won't exceed a physical page */
        chunk_start_offset = chunk * PAGE_SZ;
        chunk_end_offset = chunk_start_offset + PAGE_SZ;

        if (chunk_start_offset < off) {
            chunk_offset = off;
            if ((off + pending_len) < chunk_end_offset)
                chunk_len = pending_len;
            else
                chunk_len = chunk_end_offset - off;
        } else {
            chunk_offset = chunk_start_offset;
            if (pending_len < PAGE_SZ)
                chunk_len = pending_len;
            else
                chunk_len = PAGE_SZ;
        }

        set_addr(addr, chunk_offset);
        ret = bf_fpga_i2c_addr_write(BUS_NO, WITH_MUX, MUX_CHN, EEPROM_ADDR,
                                     addr, REGADDR_LEN, buf, chunk_len);
        if(ret != 0){
            bf_print("write sys eeprom fail (%s), addr(%lld), len(%ld)\n",
                     bf_pltfm_err_str(ret), chunk_offset, chunk_len);
            return retval;
        }

        buf += chunk_len;
        pending_len -= chunk_len;
        retval += chunk_len;
        mdelay(50);
    }

    return retval;
}
