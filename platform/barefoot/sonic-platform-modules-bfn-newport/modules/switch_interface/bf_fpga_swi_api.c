/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * device attribute handler implementation for bf fpga switch interface
 */

#define pr_fmt(fmt) "%s:%s: " fmt, KBUILD_MODNAME,  __func__

#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/hwmon-sysfs.h>
#include <linux/bitops.h>
#include "bf_module_util.h"
#include "bf_fpga_swi_driver.h"
#include "bf_fpga_i2c_util.h"
#include <bf_fpga_ioctl.h>
#include <bf_fpga_i2c_reg.h>


#define REG_BITS (32)

ATTR_SHOW_STR_FUNC(fpga_alias, "FPGA1")
ATTR_SHOW_STR_FUNC(fpga_type, "Xilinx Artix7")

ATTR_SHOW_STR_FUNC(debug,
    "FPGA reg addr list:\n"
    "    version_num = 0x3F000\n"
    "    build_date  = 0x3F004\n"
    "    reset_ctrl1 = 0x3F008, set 1 to reset, not self cleared.\n"
    "    reset_ctrl2 = 0x3F00C, set 1 to reset, not self cleared.\n"
    "\n"
    "Read FPGA reg:\n"
    "    $ fpga_util reg_read 0 <reg_addr>\n"
    "\n"
    "Write FPGA reg:\n"
    "    $ fpga_util reg_write 0 <reg_addr> <32bit_data>\n"
)

ATTR_SHOW_NUM_FUNC(devnum, NUM_DEV)

ssize_t reset_reg_show(struct device *dev, struct device_attribute *da,
                            char *buf)
{
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
    uint32_t reg_idx = attr->index - FPGA_RESET_I2C0_ATTR_ID;
    uint32_t reg_addr = (reg_idx < REG_BITS)? BF_FPGA_RESET_CTRL_1 :
                        BF_FPGA_RESET_CTRL_2;
    uint32_t bit_idx = reg_idx % REG_BITS;
    uint32_t val;
    int error;

    error = bf_fpga_reg_read32(reg_addr, &val);
    if(error)
        return error;

    return sprintf(buf, "%d\n", test_bit(bit_idx, (unsigned long*)&val)? 1 : 0);
}

ssize_t reset_reg_store(struct device *dev, struct device_attribute *da,
                            const char *buf, size_t count)
{
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
    uint32_t reg_idx = attr->index - FPGA_RESET_I2C0_ATTR_ID;
    uint32_t reg_addr = (reg_idx < REG_BITS)? BF_FPGA_RESET_CTRL_1 :
                        BF_FPGA_RESET_CTRL_2;
    uint32_t reg_val, bit_idx = reg_idx % REG_BITS;
    int error;
    long val;
    bool is_set;

    error = kstrtol(buf, 10, &val);
    if(error)
        return error;
    is_set = (val == 0)? false : true;

    error = bf_fpga_reg_read32(reg_addr, &reg_val);
    if(error)
        return error;

    assign_bit(bit_idx, (unsigned long*)&reg_val, is_set);
    error = bf_fpga_reg_write32(reg_addr, reg_val);
    if(error)
        return error;

    return count;
}

ssize_t fpga_ver_show(struct device *dev, struct device_attribute *da,
                            char *buf)
{
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
    uint32_t val, timestamp;

    if(attr->index != FPGA_HWVER_ATTR_ID)
        return 0;

    bf_fpga_reg_read32(BF_FPGA_VER_REG, &val);
    bf_fpga_reg_read32(BF_FPGA_BUILD_DATE, &timestamp);
    return sprintf(buf, "%d.%d date_%x\n", val >> 16, val & 0xFFFF, timestamp);
}

