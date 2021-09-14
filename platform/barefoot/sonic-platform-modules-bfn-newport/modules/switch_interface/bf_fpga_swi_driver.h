/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * FPGA switch interface driver related data structures and enum
 */

#ifndef __BF_FPGA_SWI_DRIVER_H__
#define __BF_FPGA_SWI_DRIVER_H__

#define NUM_DEV 1

enum fpga_sysfs_attributes
{
    FPGA_ALIAS_ATTR_ID,
    FPGA_TYPE_ATTR_ID,
    FPGA_HWVER_ATTR_ID,
    FPGA_BDVER_ATTR_ID,
    FPGA_RESET_I2C0_ATTR_ID,
    FPGA_RESET_I2C1_ATTR_ID,
    FPGA_RESET_I2C2_ATTR_ID,
    FPGA_RESET_I2C3_ATTR_ID,
    FPGA_RESET_I2C4_ATTR_ID,
    FPGA_RESET_I2C5_ATTR_ID,
    FPGA_RESET_I2C6_ATTR_ID,
    FPGA_RESET_I2C7_ATTR_ID,
    FPGA_RESET_I2C8_ATTR_ID,
    FPGA_RESET_I2C9_ATTR_ID,
    FPGA_RESET_I2C10_ATTR_ID,
    FPGA_RESET_I2C11_ATTR_ID,
    FPGA_RESET_I2C12_ATTR_ID,
    FPGA_RESET_I2C13_ATTR_ID,
    FPGA_RESET_I2C14_ATTR_ID,
    FPGA_RESET_I2C15_ATTR_ID,
    FPGA_RESET_I2C16_ATTR_ID,
    FPGA_RESET_I2C17_ATTR_ID,
    FPGA_RESET_I2C18_ATTR_ID,
    FPGA_RESET_I2C19_ATTR_ID,
    FPGA_RESET_I2C20_ATTR_ID,
    FPGA_RESET_I2C21_ATTR_ID,
    FPGA_RESET_I2C22_ATTR_ID,
    FPGA_RESET_I2C23_ATTR_ID,
    FPGA_RESET_I2C24_ATTR_ID,
    FPGA_RESET_I2C25_ATTR_ID,
    FPGA_RESET_I2C26_ATTR_ID,
    FPGA_RESET_I2C27_ATTR_ID,
    FPGA_RESET_I2C28_ATTR_ID,
    FPGA_RESET_I2C29_ATTR_ID,
    FPGA_RESET_I2C30_ATTR_ID,
    FPGA_RESET_I2C31_ATTR_ID,
    FPGA_RESET_I2C32_ATTR_ID,
    FPGA_RESET_I2C33_ATTR_ID,
    DEBUG_ATTR_ID,
    LOGLEVEL_ATTR_ID,
    NUM_DEV_ATTR_ID,
    FPGA_MAX_ATTR_ID
};

struct bf_fpga_swi_drv_data {
    struct kobject *root_kobj;
    int loglevel;
    struct platform_device pdev[NUM_DEV];
};

#endif // __BF_FPGA_SWI_DRIVER_H__
