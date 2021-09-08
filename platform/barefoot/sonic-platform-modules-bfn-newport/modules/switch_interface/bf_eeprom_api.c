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

ATTR_SHOW_STR_FUNC(debug, //SEAN TODO
    "+++DUMMY content+++\n"
    "eeprom present:\n"
    "  0-->present\n"
    "  1-->unpresent\n"
    "  bit0-->eeprom1, bit4-->eeprom2\n"
    "  eg:\n"
    "  1.show present info: i2cget -f -y 2 0x1d 0x34\n"
    "\n"
    "eeprom data:\n"
    "                    path\n"
    "  eeprom1             81-0058\n"
    "  eeprom2             82-0058\n"
    "                    sysfs\n"
    "  temp     :    temp1_input\n"
    "  fan_speed:    fan1_input\n"
    "  i_in     :    curr1_input\n"
    "  v_in     :    in1_input\n"
    "  p_in     :    power1_input\n"
    "  i_out    :    curr2_input\n"
    "  v_out    :    in2_input\n"
    "  p_out    :    power2_input\n"
    "  eg:\n"
    "  1.show data info: cat /sys/bus/i2c/devices/$path/hwmon/hwmon*/$sysfs\n"
    "eeprom vendor, model, serial, version:\n"
    "  eeprom1-->$bus = 81, $addr = 0x50\n"
    "  eeprom2-->$bus = 82, $addr = 0x50\n"
    "  eg:\n"
    "  1.show all info: i2cdump -f -y $bus $addr\n"
    "---DUMMY content---\n"
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
                                    addr, buf, REGADDR_LEN, rd_sz);
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
