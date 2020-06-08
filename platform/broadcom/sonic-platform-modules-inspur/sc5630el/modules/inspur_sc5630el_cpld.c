/*
 * A hwmon driver for the inspur_sc5630el_cpld
 *
 * Copyright (C) 2019 Inspur .
 * Jim Chen <jimchen@inspur.com>
 * This program is free software: you can redistribute it and/or modify 
 * it under the terms of the GNU General Public License as published by 
 * the Free Software Foundation, either version 3 of the License, or 
 * any later version. 
 *
 * This program is distributed in the hope that it will be useful, 
 * but WITHOUT ANY WARRANTY; without even the implied warranty of 
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
 * GNU General Public License for more details. 
 * see <http://www.gnu.org/licenses/>
 *
 * Based on ad7414.c
 * Copyright 2006 Stefan Roese <sr at denx.de>, DENX Software Engineering
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * see <http://www.gnu.org/licenses/>
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
 */


/* ----------------------------------------------------------------------------
 * Include files
 * ----------------------------------------------------------------------------
 */
#include <linux/module.h>
#include <linux/i2c.h>
#include <linux/slab.h>
#include <linux/list.h>
#include <linux/dmi.h>
#include <linux/hwmon.h>
#include <linux/hwmon-sysfs.h>
#include <linux/err.h>
#include <linux/mutex.h>

/* ---------------------------------------------------------------------------
 * Constant
 * ----------------------------------------------------------------------------
 */
#define DRIVER_NAME        "inspur_cpld"

//CPLD version register
#define CPLD_VERSION_REG     0x0 
#define FIRST_VERSiON_BITS   0xC0
#define SECOND_VERSiON_BITS   0x30
#define THIRD_VERSiON_BITS   0xF

//Psu present register
#define PSU_PRESENT_REG     0xD           
#define PSU0_PRESENT_BIT    0x2
#define PSU1_PRESENT_BIT    0x4

//Psu power register
#define PSU_POWER_REG      0xD  
#define PSU0_POWER_BIT     0x8  
#define PSU1_POWER_BIT     0x10  

//All status register
#define ALL_FSM_STATE    0x04


//System status led register
/*
00 system init
01 system init finish
10 system init finish fatal error
*/
#define SYS_LED_REG      0xF
#define SYS_STATUS_LED_BITS     0x03

//System fan led register
/*
00 all fan ok
01 one fan fail
10 more than 2 fan fail
*/
#define SYS_FAN_LED_REG     0x10
#define SYS_FAN_LED_BITS    0x03

//System psu led register
/*
00 all psu ok
01 one psu fail
10 more than 2 fan fail
*/
#define SYS_PSU_LED_REG    0x11
#define SYS_PSU_LED_BITS   0x3

//System bmc led register
/*
00:bmc ok
01:bmc fail
*/
#define SYS_BMC_LED_REG    0x12 
#define SYS_BMC_LED_BITS   0x1

//System loc led register
/*
00:locled off
01:locled on
*/
#define SYS_LOC_LED_REG    0x13 
#define SYS_LOC_LED_BITS   0x1



//System os led register
/*
00:bmc ok
01:bmc fail
*/
#define SYS_OS_LED_REG    0x1E
#define SYS_OS_LED_BITS   0x1
#define SYS_PORT_LED_BITS   0x4

//Port Reset register
#define PORT_RESET_REG    0xE
#define P0_RESET_BITS   0x1
#define P1_RESET_BITS   0x2
#define P2_RESET_BITS   0x4
#define P3_RESET_BITS   0x8
#define P4_RESET_BITS   0x10
#define P5_RESET_BITS   0x20
#define P6_RESET_BITS   0x40
#define P7_RESET_BITS   0x80

//Port fault 0 register
#define PORT_FAULT0_REG    0x14
#define P0_FAULT_BITS   0x1
#define P1_FAULT_BITS   0x2
#define P2_FAULT_BITS   0x4
#define P3_FAULT_BITS   0x8
#define P4_FAULT_BITS   0x10
#define P5_FAULT_BITS   0x20
#define P6_FAULT_BITS   0x40
#define P7_FAULT_BITS   0x80
//Port fault 1 register
#define PORT_FAULT1_REG    0x15
//Port fault 2 register
#define PORT_FAULT2_REG    0x16
//Port fault 3 register
#define PORT_FAULT3_REG    0x17
//Port fault 4 register
#define PORT_FAULT4_REG    0x18
//Port fault 5 register
#define PORT_FAULT5_REG    0x19
//Port fault 6 register
#define PORT_FAULT6_REG    0x1A

#define CPLD_MB_BASE_REG	0x00


//BMC Reset register
/*
00:bmc ok
01:bmc fail
*/

#define ALL_RESET_REG    0x1D
#define ALL_RESET1_BIT   0x1
#define ALL_RESET2_BIT   0x2
#define ALL_RESET3_BIT   0x4
#define ALL_RESET4_BIT   0x8
#define ALL_RESET5_BIT   0x10
#define ALL_RESET6_BIT   0x20
#define ALL_RESET7_BIT   0x40
#define ALL_RESET8_BIT   0x80

static ssize_t psu_show_status(struct device *dev, struct device_attribute *attr, char *buf);
static ssize_t cpld_show_version(struct device *dev, struct device_attribute *attr, char *buf);
static ssize_t sys_led_read(struct device *dev, struct device_attribute *attr, char *buf);
static ssize_t sys_led_write(struct device *dev, struct device_attribute *attr, const char *buf, size_t count);

static ssize_t port_reset_read(struct device *dev, struct device_attribute *attr, char *buf);
static ssize_t port_reset_write(struct device *dev, struct device_attribute *attr, const char *buf, size_t count);

static ssize_t bmc_reset_read(struct device *dev, struct device_attribute *attr, char *buf);
static ssize_t bmc_reset_write(struct device *dev, struct device_attribute *attr, const char *buf, size_t count);

static ssize_t port_fault_read(struct device *dev, struct device_attribute *attr, char *buf);
static ssize_t port_fault_write(struct device *dev, struct device_attribute *attr, const char *buf, size_t count);

static LIST_HEAD(cpld_client_list);
static struct mutex	 list_lock;

struct cpld_client_node {
    struct i2c_client *client;
    struct list_head   list;
};

/* Addresses scanned for inspur_sc5630el_cpld */
static const unsigned short normal_i2c[] = { 0x68, I2C_CLIENT_END };

struct inspur_cpld_data {
  struct device      *hwmon_dev;
  struct mutex        update_lock;
  char model_name[9]; /* Model name, read from eeprom */
};


enum sysfs_cpld_attributes {
  PSU1_PRESENT,
  PSU2_PRESENT,
  PSU1_POWER_GOOD,
  PSU2_POWER_GOOD,
  FIRST_CPLD_VERSION,
  SECOND_CPLD_VERSION,
  THIRD_CPLD_VERSION,
  SYS_STATUS_LED,
  P0_RESET,
  P1_RESET,
  P2_RESET,
  P3_RESET,
  P4_RESET,
  P5_RESET,
  P6_RESET,
  P7_RESET,
  PWR_LED,
  FAN_LED,
  BMC_LED,
  LOC_LED,
  OS_CONTORL,
  P0_FAULT,
  P1_FAULT,
  P2_FAULT,
  P3_FAULT,
  P4_FAULT,
  P5_FAULT,
  P6_FAULT,
  P7_FAULT,
  P8_FAULT,
  P9_FAULT,
  P10_FAULT,
  P11_FAULT,
  P12_FAULT,
  P13_FAULT,
  P14_FAULT,
  P15_FAULT,
  P16_FAULT,
  P17_FAULT,
  P18_FAULT,
  P19_FAULT,
  P20_FAULT,
  P21_FAULT,
  P22_FAULT,
  P23_FAULT,
  P24_FAULT,
  P25_FAULT,
  P26_FAULT,
  P27_FAULT,
  P28_FAULT,
  P29_FAULT,
  P30_FAULT,
  P31_FAULT,
  P32_FAULT,
  P33_FAULT,
  P34_FAULT,
  P35_FAULT,
  P36_FAULT,
  P37_FAULT,
  P38_FAULT,
  P39_FAULT,
  P40_FAULT,
  P41_FAULT,
  P42_FAULT,
  P43_FAULT,
  P44_FAULT,
  P45_FAULT,
  P46_FAULT,
  P47_FAULT,
  P48_FAULT,
  P49_FAULT,
  P50_FAULT,
  P51_FAULT,
  P52_FAULT,
  P53_FAULT,
  P54_FAULT,
  P55_FAULT,
  BMC_RESET,
  CPU_RESET,
  SWITCH_RESET,
  I210_RESET,
  R54210_1_RESET,
  R54210_2_RESET,
  R5387_RESET,
  DEBUG_RESET,
  PORT_CONTROL,
};

/* ------------------------------------------------------------------------------
 * Register sysfs/i2c
 * ----------------------------------------------------------------------------
 */
static SENSOR_DEVICE_ATTR(psu1_present, S_IRUGO, psu_show_status, NULL, PSU1_PRESENT);
static SENSOR_DEVICE_ATTR(psu2_present, S_IRUGO, psu_show_status, NULL, PSU2_PRESENT);
static SENSOR_DEVICE_ATTR(psu1_power_good, S_IRUGO, psu_show_status, NULL, PSU1_POWER_GOOD);
static SENSOR_DEVICE_ATTR(psu2_power_good, S_IRUGO, psu_show_status, NULL, PSU2_POWER_GOOD);
static SENSOR_DEVICE_ATTR(p0_reset,  (0660), port_reset_read, port_reset_write, P0_RESET);
static SENSOR_DEVICE_ATTR(p1_reset,  (0660), port_reset_read, port_reset_write, P1_RESET);
static SENSOR_DEVICE_ATTR(p2_reset,  (0660), port_reset_read, port_reset_write, P2_RESET);
static SENSOR_DEVICE_ATTR(p3_reset,  (0660), port_reset_read, port_reset_write, P3_RESET);
static SENSOR_DEVICE_ATTR(p4_reset,  (0660), port_reset_read, port_reset_write, P4_RESET);
static SENSOR_DEVICE_ATTR(p5_reset,  (0660), port_reset_read, port_reset_write, P5_RESET);
static SENSOR_DEVICE_ATTR(p6_reset,  (0660), port_reset_read, port_reset_write, P6_RESET);
static SENSOR_DEVICE_ATTR(p7_reset,  (0660), port_reset_read, port_reset_write, P7_RESET);
static SENSOR_DEVICE_ATTR(sys_status_led,  (0660), sys_led_read, sys_led_write, SYS_STATUS_LED);
static SENSOR_DEVICE_ATTR(pwr_led,  (0660), sys_led_read, sys_led_write, PWR_LED);
static SENSOR_DEVICE_ATTR(fan_led,  (0660), sys_led_read, sys_led_write, FAN_LED);
static SENSOR_DEVICE_ATTR(bmc_led,  (0660), sys_led_read, sys_led_write, BMC_LED);
static SENSOR_DEVICE_ATTR(loc_led,  (0660), sys_led_read, sys_led_write, LOC_LED);
static SENSOR_DEVICE_ATTR(os_control,  (0660), sys_led_read, sys_led_write, OS_CONTORL);
static SENSOR_DEVICE_ATTR(first_cpld_version, S_IRUGO, cpld_show_version, NULL, FIRST_CPLD_VERSION);
static SENSOR_DEVICE_ATTR(second_cpld_version, S_IRUGO, cpld_show_version, NULL, SECOND_CPLD_VERSION);
static SENSOR_DEVICE_ATTR(third_cpld_version, S_IRUGO, cpld_show_version, NULL, THIRD_CPLD_VERSION);
static SENSOR_DEVICE_ATTR(port_control,  (0660), sys_led_read, sys_led_write, PORT_CONTROL);

static SENSOR_DEVICE_ATTR(p0_fault,  (0660), port_fault_read, port_fault_write, P0_FAULT);
static SENSOR_DEVICE_ATTR(p1_fault,  (0660), port_fault_read, port_fault_write, P1_FAULT);
static SENSOR_DEVICE_ATTR(p2_fault,  (0660), port_fault_read, port_fault_write, P2_FAULT);
static SENSOR_DEVICE_ATTR(p3_fault,  (0660), port_fault_read, port_fault_write, P3_FAULT);
static SENSOR_DEVICE_ATTR(p4_fault,  (0660), port_fault_read, port_fault_write, P4_FAULT);
static SENSOR_DEVICE_ATTR(p5_fault,  (0660), port_fault_read, port_fault_write, P5_FAULT);
static SENSOR_DEVICE_ATTR(p6_fault,  (0660), port_fault_read, port_fault_write, P6_FAULT);
static SENSOR_DEVICE_ATTR(p7_fault,  (0660), port_fault_read, port_fault_write, P7_FAULT);
static SENSOR_DEVICE_ATTR(p8_fault,  (0660), port_fault_read, port_fault_write, P8_FAULT);
static SENSOR_DEVICE_ATTR(p9_fault,  (0660), port_fault_read, port_fault_write, P9_FAULT);
static SENSOR_DEVICE_ATTR(p10_fault,  (0660), port_fault_read, port_fault_write, P10_FAULT);
static SENSOR_DEVICE_ATTR(p11_fault,  (0660), port_fault_read, port_fault_write, P11_FAULT);
static SENSOR_DEVICE_ATTR(p12_fault,  (0660), port_fault_read, port_fault_write, P12_FAULT);
static SENSOR_DEVICE_ATTR(p13_fault,  (0660), port_fault_read, port_fault_write, P13_FAULT);
static SENSOR_DEVICE_ATTR(p14_fault,  (0660), port_fault_read, port_fault_write, P14_FAULT);
static SENSOR_DEVICE_ATTR(p15_fault,  (0660), port_fault_read, port_fault_write, P15_FAULT);
static SENSOR_DEVICE_ATTR(p16_fault,  (0660), port_fault_read, port_fault_write, P16_FAULT);
static SENSOR_DEVICE_ATTR(p17_fault,  (0660), port_fault_read, port_fault_write, P17_FAULT);
static SENSOR_DEVICE_ATTR(p18_fault,  (0660), port_fault_read, port_fault_write, P18_FAULT);
static SENSOR_DEVICE_ATTR(p19_fault,  (0660), port_fault_read, port_fault_write, P19_FAULT);
static SENSOR_DEVICE_ATTR(p20_fault,  (0660), port_fault_read, port_fault_write, P20_FAULT);
static SENSOR_DEVICE_ATTR(p21_fault,  (0660), port_fault_read, port_fault_write, P21_FAULT);
static SENSOR_DEVICE_ATTR(p22_fault,  (0660), port_fault_read, port_fault_write, P22_FAULT);
static SENSOR_DEVICE_ATTR(p23_fault,  (0660), port_fault_read, port_fault_write, P23_FAULT);
static SENSOR_DEVICE_ATTR(p24_fault,  (0660), port_fault_read, port_fault_write, P24_FAULT);
static SENSOR_DEVICE_ATTR(p25_fault,  (0660), port_fault_read, port_fault_write, P25_FAULT);
static SENSOR_DEVICE_ATTR(p26_fault,  (0660), port_fault_read, port_fault_write, P26_FAULT);
static SENSOR_DEVICE_ATTR(p27_fault,  (0660), port_fault_read, port_fault_write, P27_FAULT);
static SENSOR_DEVICE_ATTR(p28_fault,  (0660), port_fault_read, port_fault_write, P28_FAULT);
static SENSOR_DEVICE_ATTR(p29_fault,  (0660), port_fault_read, port_fault_write, P29_FAULT);
static SENSOR_DEVICE_ATTR(p30_fault,  (0660), port_fault_read, port_fault_write, P30_FAULT);
static SENSOR_DEVICE_ATTR(p31_fault,  (0660), port_fault_read, port_fault_write, P31_FAULT);
static SENSOR_DEVICE_ATTR(p32_fault,  (0660), port_fault_read, port_fault_write, P32_FAULT);
static SENSOR_DEVICE_ATTR(p33_fault,  (0660), port_fault_read, port_fault_write, P33_FAULT);
static SENSOR_DEVICE_ATTR(p34_fault,  (0660), port_fault_read, port_fault_write, P34_FAULT);
static SENSOR_DEVICE_ATTR(p35_fault,  (0660), port_fault_read, port_fault_write, P35_FAULT);
static SENSOR_DEVICE_ATTR(p36_fault,  (0660), port_fault_read, port_fault_write, P36_FAULT);
static SENSOR_DEVICE_ATTR(p37_fault,  (0660), port_fault_read, port_fault_write, P37_FAULT);
static SENSOR_DEVICE_ATTR(p38_fault,  (0660), port_fault_read, port_fault_write, P38_FAULT);
static SENSOR_DEVICE_ATTR(p39_fault,  (0660), port_fault_read, port_fault_write, P39_FAULT);
static SENSOR_DEVICE_ATTR(p40_fault,  (0660), port_fault_read, port_fault_write, P40_FAULT);
static SENSOR_DEVICE_ATTR(p41_fault,  (0660), port_fault_read, port_fault_write, P41_FAULT);
static SENSOR_DEVICE_ATTR(p42_fault,  (0660), port_fault_read, port_fault_write, P42_FAULT);
static SENSOR_DEVICE_ATTR(p43_fault,  (0660), port_fault_read, port_fault_write, P43_FAULT);
static SENSOR_DEVICE_ATTR(p44_fault,  (0660), port_fault_read, port_fault_write, P44_FAULT);
static SENSOR_DEVICE_ATTR(p45_fault,  (0660), port_fault_read, port_fault_write, P45_FAULT);
static SENSOR_DEVICE_ATTR(p46_fault,  (0660), port_fault_read, port_fault_write, P46_FAULT);
static SENSOR_DEVICE_ATTR(p47_fault,  (0660), port_fault_read, port_fault_write, P47_FAULT);
static SENSOR_DEVICE_ATTR(p48_fault,  (0660), port_fault_read, port_fault_write, P48_FAULT);
static SENSOR_DEVICE_ATTR(p49_fault,  (0660), port_fault_read, port_fault_write, P49_FAULT);
static SENSOR_DEVICE_ATTR(p50_fault,  (0660), port_fault_read, port_fault_write, P50_FAULT);
static SENSOR_DEVICE_ATTR(p51_fault,  (0660), port_fault_read, port_fault_write, P51_FAULT);
static SENSOR_DEVICE_ATTR(p52_fault,  (0660), port_fault_read, port_fault_write, P52_FAULT);
static SENSOR_DEVICE_ATTR(p53_fault,  (0660), port_fault_read, port_fault_write, P53_FAULT);
static SENSOR_DEVICE_ATTR(p54_fault,  (0660), port_fault_read, port_fault_write, P54_FAULT);
static SENSOR_DEVICE_ATTR(p55_fault,  (0660), port_fault_read, port_fault_write, P55_FAULT);

static SENSOR_DEVICE_ATTR(bmc_reset,  (0660), bmc_reset_read, bmc_reset_write, BMC_RESET);
static SENSOR_DEVICE_ATTR(cpu_reset,  (0660), bmc_reset_read, bmc_reset_write, CPU_RESET);
static SENSOR_DEVICE_ATTR(switch_reset,  (0660), bmc_reset_read, bmc_reset_write, SWITCH_RESET);
static SENSOR_DEVICE_ATTR(i210_reset,  (0660), bmc_reset_read, bmc_reset_write, I210_RESET);
static SENSOR_DEVICE_ATTR(r54210_1_reset,  (0660), bmc_reset_read, bmc_reset_write, R54210_1_RESET);
static SENSOR_DEVICE_ATTR(r54210_2_reset,  (0660), bmc_reset_read, bmc_reset_write, R54210_2_RESET);
static SENSOR_DEVICE_ATTR(r5387_reset,  (0660), bmc_reset_read, bmc_reset_write, R5387_RESET);
static SENSOR_DEVICE_ATTR(debug_reset,  (0660), bmc_reset_read, bmc_reset_write, DEBUG_RESET);



static struct attribute *inspur_sc5630el_cpld_attributes[] = {
  &sensor_dev_attr_psu1_present.dev_attr.attr,
  &sensor_dev_attr_psu2_present.dev_attr.attr,
  &sensor_dev_attr_psu1_power_good.dev_attr.attr,
  &sensor_dev_attr_psu2_power_good.dev_attr.attr,
  &sensor_dev_attr_first_cpld_version.dev_attr.attr,
  &sensor_dev_attr_second_cpld_version.dev_attr.attr,
  &sensor_dev_attr_third_cpld_version.dev_attr.attr,
  &sensor_dev_attr_p0_reset.dev_attr.attr,
  &sensor_dev_attr_p1_reset.dev_attr.attr,
  &sensor_dev_attr_p2_reset.dev_attr.attr,
  &sensor_dev_attr_p3_reset.dev_attr.attr,
  &sensor_dev_attr_p4_reset.dev_attr.attr,
  &sensor_dev_attr_p5_reset.dev_attr.attr,
  &sensor_dev_attr_p6_reset.dev_attr.attr,
  &sensor_dev_attr_p7_reset.dev_attr.attr,
  &sensor_dev_attr_sys_status_led.dev_attr.attr,
  &sensor_dev_attr_pwr_led.dev_attr.attr,
  &sensor_dev_attr_fan_led.dev_attr.attr,
  &sensor_dev_attr_bmc_led.dev_attr.attr,
  &sensor_dev_attr_loc_led.dev_attr.attr,
  &sensor_dev_attr_os_control.dev_attr.attr,
  &sensor_dev_attr_p0_fault.dev_attr.attr,
  &sensor_dev_attr_p1_fault.dev_attr.attr,
  &sensor_dev_attr_p2_fault.dev_attr.attr,
  &sensor_dev_attr_p3_fault.dev_attr.attr,
  &sensor_dev_attr_p4_fault.dev_attr.attr,
  &sensor_dev_attr_p5_fault.dev_attr.attr,
  &sensor_dev_attr_p6_fault.dev_attr.attr,
  &sensor_dev_attr_p7_fault.dev_attr.attr,
  &sensor_dev_attr_p8_fault.dev_attr.attr,
  &sensor_dev_attr_p9_fault.dev_attr.attr,
  &sensor_dev_attr_p10_fault.dev_attr.attr,
  &sensor_dev_attr_p11_fault.dev_attr.attr,
  &sensor_dev_attr_p12_fault.dev_attr.attr,
  &sensor_dev_attr_p13_fault.dev_attr.attr,
  &sensor_dev_attr_p14_fault.dev_attr.attr,
  &sensor_dev_attr_p15_fault.dev_attr.attr,
  &sensor_dev_attr_p16_fault.dev_attr.attr,
  &sensor_dev_attr_p17_fault.dev_attr.attr,
  &sensor_dev_attr_p18_fault.dev_attr.attr,
  &sensor_dev_attr_p19_fault.dev_attr.attr,
  &sensor_dev_attr_p20_fault.dev_attr.attr,
  &sensor_dev_attr_p21_fault.dev_attr.attr,
  &sensor_dev_attr_p22_fault.dev_attr.attr,
  &sensor_dev_attr_p23_fault.dev_attr.attr,
  &sensor_dev_attr_p24_fault.dev_attr.attr,
  &sensor_dev_attr_p25_fault.dev_attr.attr,
  &sensor_dev_attr_p26_fault.dev_attr.attr,
  &sensor_dev_attr_p27_fault.dev_attr.attr,
  &sensor_dev_attr_p28_fault.dev_attr.attr,
  &sensor_dev_attr_p29_fault.dev_attr.attr,
  &sensor_dev_attr_p30_fault.dev_attr.attr,
  &sensor_dev_attr_p31_fault.dev_attr.attr,
  &sensor_dev_attr_p32_fault.dev_attr.attr,
  &sensor_dev_attr_p33_fault.dev_attr.attr,
  &sensor_dev_attr_p34_fault.dev_attr.attr,
  &sensor_dev_attr_p35_fault.dev_attr.attr,
  &sensor_dev_attr_p36_fault.dev_attr.attr,
  &sensor_dev_attr_p37_fault.dev_attr.attr,
  &sensor_dev_attr_p38_fault.dev_attr.attr,
  &sensor_dev_attr_p39_fault.dev_attr.attr,
  &sensor_dev_attr_p40_fault.dev_attr.attr,
  &sensor_dev_attr_p41_fault.dev_attr.attr,
  &sensor_dev_attr_p42_fault.dev_attr.attr,
  &sensor_dev_attr_p43_fault.dev_attr.attr,
  &sensor_dev_attr_p44_fault.dev_attr.attr,
  &sensor_dev_attr_p45_fault.dev_attr.attr,
  &sensor_dev_attr_p46_fault.dev_attr.attr,
  &sensor_dev_attr_p47_fault.dev_attr.attr,
  &sensor_dev_attr_p48_fault.dev_attr.attr,
  &sensor_dev_attr_p49_fault.dev_attr.attr,
  &sensor_dev_attr_p50_fault.dev_attr.attr,
  &sensor_dev_attr_p51_fault.dev_attr.attr,
  &sensor_dev_attr_p52_fault.dev_attr.attr,
  &sensor_dev_attr_p53_fault.dev_attr.attr,
  &sensor_dev_attr_p54_fault.dev_attr.attr,
  &sensor_dev_attr_p55_fault.dev_attr.attr,
  &sensor_dev_attr_bmc_reset.dev_attr.attr,
  &sensor_dev_attr_cpu_reset.dev_attr.attr,
  &sensor_dev_attr_switch_reset.dev_attr.attr,
  &sensor_dev_attr_i210_reset.dev_attr.attr,
  &sensor_dev_attr_r54210_1_reset.dev_attr.attr,
  &sensor_dev_attr_r54210_2_reset.dev_attr.attr,
  &sensor_dev_attr_r5387_reset.dev_attr.attr,
  &sensor_dev_attr_debug_reset.dev_attr.attr,
  &sensor_dev_attr_port_control.dev_attr.attr,
  NULL
};

static const struct attribute_group inspur_sc5630el_cpld_group = {
  .attrs = inspur_sc5630el_cpld_attributes,
};

/* ----------------------------------------------------------------------------
 * Sysfs hooks function for read/write operation
 * ----------------------------------------------------------------------------
 */
static ssize_t psu_show_status(struct device *dev, struct device_attribute *attr, char *buf)
{
    int val = 0, res = 0;
	u8 data_num = 0;
    u8 command;
    struct i2c_client *client = to_i2c_client(dev);
    struct sensor_device_attribute *sda = to_sensor_dev_attr(attr);
	u8 ret_data[14];
    switch(sda->index) {
        case PSU1_PRESENT:
		case PSU2_PRESENT:
		  command = PSU_PRESENT_REG;	
		  break;
        case PSU1_POWER_GOOD:
        case PSU2_POWER_GOOD:
          command = PSU_POWER_REG;
          break;
    }
/*current cpld not support random read, so use sequential read*/	
#if 0
    val = i2c_smbus_read_byte_data(client, command);
    if (val < 0) {
        dev_dbg(&client->dev, "cpld(0x%x) reg(0x1) err %d\n", client->addr, val);
    }
#else
	data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 14, ret_data);
	if (data_num != 14)
		dev_dbg(&client->dev, "should be read 13 regs, but now only read %d\n", data_num);
	val=ret_data[13];
#endif

    switch(sda->index) {
        case PSU1_PRESENT:
		  res = (val & PSU0_PRESENT_BIT ? 1 : 0 );	
		  break;
        case PSU2_PRESENT:
          res = (val & PSU1_PRESENT_BIT ? 1 : 0 );
          break;
        case PSU1_POWER_GOOD:
		  res = (val & PSU0_POWER_BIT ? 1 : 0 );
		  break;	
        case PSU2_POWER_GOOD:
          res = (val & PSU1_POWER_BIT ? 1 : 0 );
          break;
    }

    return sprintf(buf, "%d\n", res);
}



static ssize_t sys_led_read(struct device *dev, struct device_attribute *attr, char *buf)
{
    int val = 0, res = 0;
	u8 data_num = 0;
    u8 command;
	unsigned char ret_data[32];
    struct i2c_client *client = to_i2c_client(dev);
    struct sensor_device_attribute *sda = to_sensor_dev_attr(attr);

    switch(sda->index) {
        case SYS_STATUS_LED:
          command = SYS_LED_REG;
          break;
		case PWR_LED:  
		  command = SYS_PSU_LED_REG;
          break; 
        case FAN_LED:
		  command = SYS_FAN_LED_REG;
          break; 
        case BMC_LED:
		  command = SYS_BMC_LED_REG;
          break;
		case LOC_LED:
		  command = SYS_LOC_LED_REG;
          break; 	
        case PORT_CONTROL:
        case OS_CONTORL:
          command = SYS_OS_LED_REG;
          break;
    }

/*current cpld not support random read, so use sequential read*/	
#if 0
    val = i2c_smbus_read_byte_data(client, command);
    if (val < 0) {
        dev_dbg(&client->dev, "cpld(0x%x) reg(0x1) err %d\n", client->addr, val);
    }

    switch(sda->index) {
		case SYS_STATUS_LED:
        case PWR_LED:
        case FAN_LED:
        case BMC_LED:
		case LOC_LED:
        case OS_CONTORL:
          res = val;
          break;
    }
#else	
	switch(sda->index) {
		case SYS_STATUS_LED:
			data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 16, ret_data);
			if (data_num != 16)
				dev_dbg(&client->dev, "should be read 16 regs, but now only read %d\n", data_num);
			val=ret_data[15];
			res = val;
			break;
        case PWR_LED:
			data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 18, ret_data);
			if (data_num != 18)
				dev_dbg(&client->dev, "should be read 18 regs, but now only read %d\n", data_num);
			val=ret_data[17];
			res = val;
			break;
        case FAN_LED:
			data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 17, ret_data);
			if (data_num != 17)
				dev_dbg(&client->dev, "should be read 17 regs, but now only read %d\n", data_num);
			val=ret_data[16];
			res = val;
			break;
        case BMC_LED:
			data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 19, ret_data);
			if (data_num != 19)
				dev_dbg(&client->dev, "should be read 19 regs, but now only read %d\n", data_num);
			val=ret_data[18];
			res = val;
			break;
		case LOC_LED:
			data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 20, ret_data);
			if (data_num != 20)
				dev_dbg(&client->dev, "should be read 20 regs, but now only read %d\n", data_num);
			val=ret_data[19];
			res = val;
			break;
        case PORT_CONTROL:
        case OS_CONTORL:
			data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 31, ret_data);
			if (data_num != 31)
				dev_dbg(&client->dev, "should be read 31 regs, but now only read %d\n", data_num);
			val=ret_data[30];
			res = val;
			break;
    }

#endif

    return sprintf(buf, "%d\n", res);
}

static ssize_t sys_led_write(struct device *dev, struct device_attribute *attr, const char *buf, size_t count)
{
    struct i2c_client *client = to_i2c_client(dev);
    struct sensor_device_attribute *sda = to_sensor_dev_attr(attr);
    int error, write, command;
    unsigned char ret_data[32];
    int data_num =0; 
    int read = 0; 

    error = kstrtoint(buf, 10, &write);
    if (error)
      return error;


    switch(sda->index) {
        case SYS_STATUS_LED:
		  if(write < 0 || write > 3) 
            return -EINVAL;
			command = SYS_LED_REG;
			break;
        case PWR_LED:
		  if(write < 0 || write > 3) 
            return -EINVAL;
			command = SYS_PSU_LED_REG;
			break;
        case FAN_LED:
          if (write < 0 || write > 3) 
            return -EINVAL;
			command = SYS_FAN_LED_REG;
			break;
        case BMC_LED:
			if (write < 0 || write > 3) 
            return -EINVAL;
			command = SYS_BMC_LED_REG;
			break;
		case LOC_LED:
			if (write < 0 || write > 2) 
            return -EINVAL;
			command = SYS_LOC_LED_REG;
			break;	
        case OS_CONTORL:
            if (write < 0 || write > 3) 
                return -EINVAL;
            data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 31, ret_data);
            if (data_num != 31)
                dev_dbg(&client->dev, "should be read 31 regs, but now only read %d\n", data_num);
            read =ret_data[30];
            read &= ~SYS_OS_LED_BITS;
            write |= read << 0;
	  		command = SYS_OS_LED_REG;
	  		break;
        case PORT_CONTROL:
            if (write < 0 || write > 1) 
                return -EINVAL;
            data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 31, ret_data);
            if (data_num != 31)
                dev_dbg(&client->dev, "should be read 31 regs, but now only read %d\n", data_num);
            read =ret_data[30];
            read &= ~SYS_PORT_LED_BITS;
            write *= SYS_PORT_LED_BITS;
            write |= read << 0;
	  		command = SYS_OS_LED_REG;
	  		break;
    }

	
    i2c_smbus_write_byte_data(client, command, write);
    return count;
}

static ssize_t port_reset_read(struct device *dev, struct device_attribute *attr, char *buf)
{
    int val = 0, res = 0;
    //u8 command;
	u8 data_num = 0;
    struct i2c_client *client = to_i2c_client(dev);
    struct sensor_device_attribute *sda = to_sensor_dev_attr(attr);
	u8 ret_data[15];

	switch(sda->index) {
        case P0_RESET:
		case P1_RESET:
		case P2_RESET:
		case P3_RESET:
		case P4_RESET:
		case P5_RESET:
		case P6_RESET:
		case P7_RESET:
			data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 15, ret_data);
			if (data_num != 15)
			dev_dbg(&client->dev, "should be read 15 regs, but now only read %d\n", data_num);
			val=ret_data[14];
          break; 
    }	


    switch(sda->index) {
        case P0_RESET:
          res = (val & P0_RESET_BITS) >> 0;
          break;
        case P1_RESET:
          res = (val & P1_RESET_BITS) >> 1;
          break;
        case P2_RESET:
          res = (val & P2_RESET_BITS) >> 2;
          break;
        case P3_RESET:
          res = (val & P3_RESET_BITS) >> 3;
          break;
        case P4_RESET:
          res = (val & P4_RESET_BITS) >> 4;
          break;
        case P5_RESET:
          res = (val & P5_RESET_BITS) >> 5;
          break;
		case P6_RESET:
          res = (val & P6_RESET_BITS) >> 6;
          break;  
		case P7_RESET:
          res = (val & P7_RESET_BITS) >> 7;
          break;  
    }

    return sprintf(buf, "%d\n", res);
}

static ssize_t port_reset_write(struct device *dev, struct device_attribute *attr, const char *buf, size_t count)
{
    struct i2c_client *client = to_i2c_client(dev);
    struct sensor_device_attribute *sda = to_sensor_dev_attr(attr);
    int error, write, command, read;
	u8 data_num = 0;
	u8 ret_data[15];
    error = kstrtoint(buf, 10, &write);
    if (error)
      return error;
	
	if (write < 0 || write > 1) 
            return -EINVAL;

	switch(sda->index) {
        case P0_RESET:
		case P1_RESET:
		case P2_RESET:
		case P3_RESET:
		case P4_RESET:
		case P5_RESET:
		case P6_RESET:
		case P7_RESET:
			command = PORT_RESET_REG;
			data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 15, ret_data);
			if (data_num != 15)
			dev_dbg(&client->dev, "should be read 15 regs, but now only read %d\n", data_num);
			read=ret_data[14];
          break;
	}
    switch(sda->index) {
        case P0_RESET:
          read &= ~P0_RESET_BITS;
          read |= write << 0;
          break;
        case P1_RESET:
          read &= ~P1_RESET_BITS;
          read |= write << 1;
          break;
        case P2_RESET:
          read &= ~P2_RESET_BITS;
          read |= write << 2;
          break;
        case P3_RESET:
          read &= ~P3_RESET_BITS;
          read |= write << 3;
          break;
        case P4_RESET:
          read &= ~P4_RESET_BITS;
          read |= write << 4;
          break;
        case P5_RESET:
          read &= ~P5_RESET_BITS;
          read |= write << 5;
          break;
		case P6_RESET:
          read &= ~P6_RESET_BITS;
          read |= write << 6;
          break;  
		case P7_RESET:
          read &= ~P7_RESET_BITS;
          read |= write << 7;
          break; 
    }

    i2c_smbus_write_byte_data(client, command, read);
    return count;
}





static ssize_t bmc_reset_read(struct device *dev, struct device_attribute *attr, char *buf)
{
    int val = 0, res = 0;
	u8 data_num = 0;
    u8 command;
    struct i2c_client *client = to_i2c_client(dev);
    struct sensor_device_attribute *sda = to_sensor_dev_attr(attr);
    command = ALL_RESET_REG;
	unsigned char ret_data[31];
/*current cpld not support random read, so use sequential read*/	
#if 0
    val = i2c_smbus_read_byte_data(client, command);
    if (val < 0) {
        dev_dbg(&client->dev, "cpld(0x%x) reg(0x1) err %d\n", client->addr, val);
    }
	res = val;
#else
	switch(sda->index) {
        case BMC_RESET:
		case CPU_RESET:
		case SWITCH_RESET:
		case I210_RESET:
		case R54210_1_RESET:
		case R54210_2_RESET:
		case R5387_RESET:
		case DEBUG_RESET:
			data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 30, ret_data);
			if (data_num != 30)
			dev_dbg(&client->dev, "should be read 29 regs, but now only read %d\n", data_num);
			val=ret_data[29];
			break; 
    }	


    switch(sda->index) {
        case BMC_RESET:
          res = (val & ALL_RESET1_BIT) >> 0;
          break;
        case CPU_RESET:
          res = (val & ALL_RESET2_BIT) >> 1;
          break;
        case SWITCH_RESET:
          res = (val & ALL_RESET3_BIT) >> 2;
          break;
        case I210_RESET:
          res = (val & ALL_RESET4_BIT) >> 3;
          break;
        case R54210_1_RESET:
          res = (val & ALL_RESET5_BIT) >> 4;
          break;
        case R54210_2_RESET:
          res = (val & ALL_RESET6_BIT) >> 5;
          break;
		case R5387_RESET:
          res = (val & ALL_RESET7_BIT) >> 6;
          break;  
		case DEBUG_RESET:
          res = (val & ALL_RESET8_BIT) >> 7;
          break;  
    }

#endif
    return sprintf(buf, "%d\n", res);
}

static ssize_t bmc_reset_write(struct device *dev, struct device_attribute *attr, const char *buf, size_t count)
{
    struct i2c_client *client = to_i2c_client(dev);
    struct sensor_device_attribute *sda = to_sensor_dev_attr(attr);
    int error, write, command, read;
	u8 data_num = 0;
	unsigned char ret_data[31];
    error = kstrtoint(buf, 10, &write);
    if (error)
      return error;
  
	if (write < 0 || write > 1) 
            return -EINVAL;
	
	command = ALL_RESET_REG;

	
	switch(sda->index) {
        case BMC_RESET:
		case CPU_RESET:
		case SWITCH_RESET:
		case I210_RESET:
		case R54210_1_RESET:
		case R54210_2_RESET:
		case R5387_RESET:
		case DEBUG_RESET:
			data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 30, ret_data);
			if (data_num != 30)
			dev_dbg(&client->dev, "should be read 29 regs, but now only read %d\n", data_num);
			read=ret_data[29];
          break;
	}
	
	switch(sda->index) {
        case BMC_RESET:
          read &= ~ALL_RESET1_BIT;
          read |= write << 0;
          break;
        case CPU_RESET:
          read &= ~ALL_RESET2_BIT;
          read |= write << 1;
          break;
        case SWITCH_RESET:
          read &= ~ALL_RESET3_BIT;
          read |= write << 2;
          break;
        case I210_RESET:
          read &= ~ALL_RESET4_BIT;
          read |= write << 3;
          break;
        case R54210_1_RESET:
          read &= ~ALL_RESET5_BIT;
          read |= write << 4;
          break;
        case R54210_2_RESET:
          read &= ~ALL_RESET6_BIT;
          read |= write << 5;
          break;
		case R5387_RESET:
          read &= ~ALL_RESET7_BIT;
          read |= write << 6;
          break;  
		case DEBUG_RESET:
          read &= ~ALL_RESET8_BIT;
          read |= write << 7;
          break; 
    }
	
    i2c_smbus_write_byte_data(client, command, write);
    return count;
}


static ssize_t cpld_show_version(struct device *dev, struct device_attribute *attr, char *buf)
{
    int val = 0, res = 0;
    u8 command;
	//u8 data_num = 0;
    struct i2c_client *client = to_i2c_client(dev);
    struct sensor_device_attribute *sda = to_sensor_dev_attr(attr);
    
	command = CPLD_VERSION_REG;


    val = i2c_smbus_read_byte_data(client, command);
    if (val < 0) {
        dev_dbg(&client->dev, "cpld(0x%x) reg(0x1) err %d\n", client->addr, val);
    }


    switch(sda->index) {
        case FIRST_CPLD_VERSION:
          res = (val & FIRST_VERSiON_BITS) >> 6;
          break;
        case SECOND_CPLD_VERSION:
          res = (val & SECOND_VERSiON_BITS) >> 4;
          break;
        case THIRD_CPLD_VERSION:
          res = (val & THIRD_VERSiON_BITS) >> 0;
          break;
    }

    return sprintf(buf, "%d\n", res);
}

static ssize_t port_fault_read(struct device *dev, struct device_attribute *attr, char *buf)
{
    int val = 0, res = 0;
    //u8 command;
	u8 data_num = 0;
    struct i2c_client *client = to_i2c_client(dev);
    struct sensor_device_attribute *sda = to_sensor_dev_attr(attr);
	u8 ret_data[31];
/*current cpld not support random read, so use sequential read*/	
#if 0
    switch(sda->index) {
        case P0_FAULT:
		case P1_FAULT:
		case P2_FAULT:
		case P3_FAULT:
		case P4_FAULT:
		case P5_FAULT:
		case P6_FAULT:
		case P7_FAULT:
          command = PORT_FAULT0_REG;
          break;
		case P8_FAULT:
		case P9_FAULT:
		case P10_FAULT:
		case P11_FAULT:
		case P12_FAULT:
		case P13_FAULT:
		case P14_FAULT:
		case P15_FAULT:
          command = PORT_FAULT1_REG;
          break;
        case P16_FAULT:
		case P17_FAULT:
		case P18_FAULT:
		case P19_FAULT:
		case P20_FAULT:
		case P21_FAULT:
		case P22_FAULT:
		case P23_FAULT:
          command = PORT_FAULT2_REG;
          break; 
        case P24_FAULT:
		case P25_FAULT:
		case P26_FAULT:
		case P27_FAULT:
		case P28_FAULT:
		case P29_FAULT:
		case P30_FAULT:
		case P31_FAULT:
          command = PORT_FAULT3_REG;
          break;
		case P32_FAULT:
		case P33_FAULT:
		case P34_FAULT:
		case P35_FAULT:
		case P36_FAULT:
		case P37_FAULT:
		case P38_FAULT:
		case P39_FAULT:
          command = PORT_FAULT4_REG;
          break;
		case P40_FAULT:
		case P41_FAULT:
		case P42_FAULT:
		case P43_FAULT:
		case P44_FAULT:
		case P45_FAULT:
		case P46_FAULT:
		case P47_FAULT:
          command = PORT_FAULT5_REG;
          break;  
		case P48_FAULT:
		case P49_FAULT:
		case P50_FAULT:
		case P51_FAULT:
		case P52_FAULT:
		case P53_FAULT:
		case P54_FAULT:
		case P55_FAULT:
          command = PORT_FAULT6_REG;
          break;   
    }


    val = i2c_smbus_read_byte_data(client, command);
    if (val < 0) {
        dev_dbg(&client->dev, "cpld(0x%x) reg(0x1) err %d\n", client->addr, val);
    }
	res = val;
#else
	switch(sda->index) {
        case P0_FAULT:
		case P1_FAULT:
		case P2_FAULT:
		case P3_FAULT:
		case P4_FAULT:
		case P5_FAULT:
		case P6_FAULT:
		case P7_FAULT:
			data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 21, ret_data);
			if (data_num != 21)
			dev_dbg(&client->dev, "should be read 21 regs, but now only read %d\n", data_num);
			val=ret_data[20];
          break;
		case P8_FAULT:
		case P9_FAULT:
		case P10_FAULT:
		case P11_FAULT:
		case P12_FAULT:
		case P13_FAULT:
		case P14_FAULT:
		case P15_FAULT:
			data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 22, ret_data);
			if (data_num != 22)
			dev_dbg(&client->dev, "should be read 22 regs, but now only read %d\n", data_num);
			val=ret_data[21];
          break;
        case P16_FAULT:
		case P17_FAULT:
		case P18_FAULT:
		case P19_FAULT:
		case P20_FAULT:
		case P21_FAULT:
		case P22_FAULT:
		case P23_FAULT:
			data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 23, ret_data);
			if (data_num != 23)
			dev_dbg(&client->dev, "should be read 23 regs, but now only read %d\n", data_num);
			val=ret_data[22];
          break; 
        case P24_FAULT:
		case P25_FAULT:
		case P26_FAULT:
		case P27_FAULT:
		case P28_FAULT:
		case P29_FAULT:
		case P30_FAULT:
		case P31_FAULT:
			data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 24, ret_data);
			if (data_num != 24)
			dev_dbg(&client->dev, "should be read 24 regs, but now only read %d\n", data_num);
			val=ret_data[23];
          break;
		case P32_FAULT:
		case P33_FAULT:
		case P34_FAULT:
		case P35_FAULT:
		case P36_FAULT:
		case P37_FAULT:
		case P38_FAULT:
		case P39_FAULT:
			data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 25, ret_data);
			if (data_num != 25)
			dev_dbg(&client->dev, "should be read 25 regs, but now only read %d\n", data_num);
			val=ret_data[24];
          break;
		case P40_FAULT:
		case P41_FAULT:
		case P42_FAULT:
		case P43_FAULT:
		case P44_FAULT:
		case P45_FAULT:
		case P46_FAULT:
		case P47_FAULT:
			data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 26, ret_data);
			if (data_num != 26)
			dev_dbg(&client->dev, "should be read 26 regs, but now only read %d\n", data_num);
			val=ret_data[25];
          break;  
		case P48_FAULT:
		case P49_FAULT:
		case P50_FAULT:
		case P51_FAULT:
		case P52_FAULT:
		case P53_FAULT:
		case P54_FAULT:
		case P55_FAULT:
			data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 27, ret_data);
			if (data_num != 27)
			dev_dbg(&client->dev, "should be read 27 regs, but now only read %d\n", data_num);
			val=ret_data[26];
          break;   
    }	
#endif

    switch(sda->index) {
        case P0_FAULT:
		case P8_FAULT:
		case P16_FAULT:
		case P24_FAULT:
		case P32_FAULT:
		case P40_FAULT:
		case P48_FAULT:
          res = (val & P0_FAULT_BITS) >> 0;
          break;
        case P1_FAULT:
		case P9_FAULT:
		case P17_FAULT:
		case P25_FAULT:
		case P33_FAULT:
		case P41_FAULT:
		case P49_FAULT:
          res = (val & P1_FAULT_BITS) >> 1;
          break;
        case P2_FAULT:
		case P10_FAULT:
		case P18_FAULT:
		case P26_FAULT:
		case P34_FAULT:
		case P42_FAULT:
		case P50_FAULT:
          res = (val & P2_FAULT_BITS) >> 2;
          break;
        case P3_FAULT:
		case P11_FAULT:
		case P19_FAULT:
		case P27_FAULT:
		case P35_FAULT:
		case P43_FAULT:
		case P51_FAULT:
          res = (val & P3_FAULT_BITS) >> 3;
          break;
        case P4_FAULT:
		case P12_FAULT:
		case P20_FAULT:
		case P28_FAULT:
		case P36_FAULT:
		case P44_FAULT:
		case P52_FAULT:
          res = (val & P4_FAULT_BITS) >> 4;
          break;
        case P5_FAULT:
		case P13_FAULT:
		case P21_FAULT:
		case P29_FAULT:
		case P37_FAULT:
		case P45_FAULT:
		case P53_FAULT:
          res = (val & P5_FAULT_BITS) >> 5;
          break;
		case P6_FAULT:
		case P14_FAULT:
		case P22_FAULT:
		case P30_FAULT:
		case P38_FAULT:
		case P46_FAULT:
		case P54_FAULT:
          res = (val & P6_FAULT_BITS) >> 6;
          break;  
		case P7_FAULT:
		case P15_FAULT:
		case P23_FAULT:
		case P31_FAULT:
		case P39_FAULT:
		case P47_FAULT:
		case P55_FAULT:
          res = (val & P7_FAULT_BITS) >> 7;
          break;  
    }

    return sprintf(buf, "%d\n", res);
}

static ssize_t port_fault_write(struct device *dev, struct device_attribute *attr, const char *buf, size_t count)
{
    struct i2c_client *client = to_i2c_client(dev);
    struct sensor_device_attribute *sda = to_sensor_dev_attr(attr);
    int error, write, command, read;
	u8 data_num = 0;
	u8 ret_data[31];
    error = kstrtoint(buf, 10, &write);
    if (error)
      return error;
	
	if (write < 0 || write > 1) 
            return -EINVAL;
/*current cpld not support random read, so use sequential read*/		
#if 0
    switch(sda->index) {
        case P0_FAULT:
		case P1_FAULT:
		case P2_FAULT:
		case P3_FAULT:
		case P4_FAULT:
		case P5_FAULT:
		case P6_FAULT:
		case P7_FAULT:
          command = PORT_FAULT0_REG;
          break;
		case P8_FAULT:
		case P9_FAULT:
		case P10_FAULT:
		case P11_FAULT:
		case P12_FAULT:
		case P13_FAULT:
		case P14_FAULT:
		case P15_FAULT:
          command = PORT_FAULT1_REG;
          break;
        case P16_FAULT:
		case P17_FAULT:
		case P18_FAULT:
		case P19_FAULT:
		case P20_FAULT:
		case P21_FAULT:
		case P22_FAULT:
		case P23_FAULT:
          command = PORT_FAULT2_REG;
          break; 
        case P24_FAULT:
		case P25_FAULT:
		case P26_FAULT:
		case P27_FAULT:
		case P28_FAULT:
		case P29_FAULT:
		case P30_FAULT:
		case P31_FAULT:
          command = PORT_FAULT3_REG;
          break;
		case P32_FAULT:
		case P33_FAULT:
		case P34_FAULT:
		case P35_FAULT:
		case P36_FAULT:
		case P37_FAULT:
		case P38_FAULT:
		case P39_FAULT:
          command = PORT_FAULT4_REG;
          break;
		case P40_FAULT:
		case P41_FAULT:
		case P42_FAULT:
		case P43_FAULT:
		case P44_FAULT:
		case P45_FAULT:
		case P46_FAULT:
		case P47_FAULT:
          command = PORT_FAULT5_REG;
          break;  
		case P48_FAULT:
		case P49_FAULT:
		case P50_FAULT:
		case P51_FAULT:
		case P52_FAULT:
		case P53_FAULT:
		case P54_FAULT:
		case P55_FAULT:
          command = PORT_FAULT6_REG;
          break;   
    }

    read = i2c_smbus_read_byte_data(client, command);
    if (read < 0) {
        dev_dbg(&client->dev, "cpld(0x%x) reg(0x1) err %d\n", client->addr, read);
    }
#else	
	switch(sda->index) {
        case P0_FAULT:
		case P1_FAULT:
		case P2_FAULT:
		case P3_FAULT:
		case P4_FAULT:
		case P5_FAULT:
		case P6_FAULT:
		case P7_FAULT:
			command = PORT_FAULT0_REG;
			data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 21, ret_data);
			if (data_num != 21)
			dev_dbg(&client->dev, "should be read 21 regs, but now only read %d\n", data_num);
			read=ret_data[20];
          break;
		case P8_FAULT:
		case P9_FAULT:
		case P10_FAULT:
		case P11_FAULT:
		case P12_FAULT:
		case P13_FAULT:
		case P14_FAULT:
		case P15_FAULT:
			command = PORT_FAULT1_REG;
			data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 22, ret_data);
			if (data_num != 22)
			dev_dbg(&client->dev, "should be read 22 regs, but now only read %d\n", data_num);
			read=ret_data[21];
          break;
        case P16_FAULT:
		case P17_FAULT:
		case P18_FAULT:
		case P19_FAULT:
		case P20_FAULT:
		case P21_FAULT:
		case P22_FAULT:
		case P23_FAULT:
			command = PORT_FAULT2_REG;
			data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 23, ret_data);
			if (data_num != 23)
			dev_dbg(&client->dev, "should be read 23 regs, but now only read %d\n", data_num);
			read=ret_data[22];
          break; 
        case P24_FAULT:
		case P25_FAULT:
		case P26_FAULT:
		case P27_FAULT:
		case P28_FAULT:
		case P29_FAULT:
		case P30_FAULT:
		case P31_FAULT:
			command = PORT_FAULT3_REG;
			data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 24, ret_data);
			if (data_num != 24)
			dev_dbg(&client->dev, "should be read 24 regs, but now only read %d\n", data_num);
			read=ret_data[23];
          break;
		case P32_FAULT:
		case P33_FAULT:
		case P34_FAULT:
		case P35_FAULT:
		case P36_FAULT:
		case P37_FAULT:
		case P38_FAULT:
		case P39_FAULT:
			command = PORT_FAULT4_REG;
			data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 25, ret_data);
			if (data_num != 25)
			dev_dbg(&client->dev, "should be read 25 regs, but now only read %d\n", data_num);
			read=ret_data[24];
          break;
		case P40_FAULT:
		case P41_FAULT:
		case P42_FAULT:
		case P43_FAULT:
		case P44_FAULT:
		case P45_FAULT:
		case P46_FAULT:
		case P47_FAULT:
			command = PORT_FAULT5_REG;
			data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 26, ret_data);
			if (data_num != 26)
			dev_dbg(&client->dev, "should be read 26 regs, but now only read %d\n", data_num);
			read=ret_data[25];
          break;  
		case P48_FAULT:
		case P49_FAULT:
		case P50_FAULT:
		case P51_FAULT:
		case P52_FAULT:
		case P53_FAULT:
		case P54_FAULT:
		case P55_FAULT:
			command = PORT_FAULT6_REG;
			data_num = i2c_smbus_read_i2c_block_data(client, CPLD_MB_BASE_REG, 27, ret_data);
			if (data_num != 27)
			dev_dbg(&client->dev, "should be read 27 regs, but now only read %d\n", data_num);
			read=ret_data[26];
          break;   
    }
#endif
    switch(sda->index) {
        case P0_FAULT:
		case P8_FAULT:
		case P16_FAULT:
		case P24_FAULT:
		case P32_FAULT:
		case P40_FAULT:
		case P48_FAULT:
          read &= ~P0_FAULT_BITS;
          read |= write << 0;
          break;
        case P1_FAULT:
		case P9_FAULT:
		case P17_FAULT:
		case P25_FAULT:
		case P33_FAULT:
		case P41_FAULT:
		case P49_FAULT:
          read &= ~P1_FAULT_BITS;
          read |= write << 1;
          break;
        case P2_FAULT:
		case P10_FAULT:
		case P18_FAULT:
		case P26_FAULT:
		case P34_FAULT:
		case P42_FAULT:
		case P50_FAULT:
          read &= ~P2_FAULT_BITS;
          read |= write << 2;
          break;
        case P3_FAULT:
		case P11_FAULT:
		case P19_FAULT:
		case P27_FAULT:
		case P35_FAULT:
		case P43_FAULT:
		case P51_FAULT:
          read &= ~P3_FAULT_BITS;
          read |= write << 3;
          break;
        case P4_FAULT:
		case P12_FAULT:
		case P20_FAULT:
		case P28_FAULT:
		case P36_FAULT:
		case P44_FAULT:
		case P52_FAULT:
          read &= ~P4_FAULT_BITS;
          read |= write << 4;
          break;
        case P5_FAULT:
		case P13_FAULT:
		case P21_FAULT:
		case P29_FAULT:
		case P37_FAULT:
		case P45_FAULT:
		case P53_FAULT:
          read &= ~P5_FAULT_BITS;
          read |= write << 5;
          break;
		case P6_FAULT:
		case P14_FAULT:
		case P22_FAULT:
		case P30_FAULT:
		case P38_FAULT:
		case P46_FAULT:
		case P54_FAULT:
          read &= ~P6_FAULT_BITS;
          read |= write << 6;
          break;  
		case P7_FAULT:
		case P15_FAULT:
		case P23_FAULT:
		case P31_FAULT:
		case P39_FAULT:
		case P47_FAULT:
		case P55_FAULT:
          read &= ~P7_FAULT_BITS;
          read |= write << 7;
          break; 
    }

    i2c_smbus_write_byte_data(client, command, read);
    return count;
}


static void inspur_i2c_cpld_add_client(struct i2c_client *client)
{
    struct cpld_client_node *node = kzalloc(sizeof(struct cpld_client_node), GFP_KERNEL);

    if (!node) {
        dev_dbg(&client->dev, "Can't allocate cpld_client_node (0x%x)\n", client->addr);
        return;
    }

    node->client = client;

    mutex_lock(&list_lock);
    list_add(&node->list, &cpld_client_list);
    mutex_unlock(&list_lock);
}

static void inspur_i2c_cpld_remove_client(struct i2c_client *client)
{
    struct list_head		*list_node = NULL;
    struct cpld_client_node *cpld_node = NULL;
    int found = 0;

    mutex_lock(&list_lock);

    list_for_each(list_node, &cpld_client_list)
    {
        cpld_node = list_entry(list_node, struct cpld_client_node, list);

        if (cpld_node->client == client) {
            found = 1;
            break;
        }
    }

    if (found) {
        list_del(list_node);
        kfree(cpld_node);
    }

    mutex_unlock(&list_lock);
}

/* ----------------------------------------------------------------------------
 * Module probe/remove functions
 * ----------------------------------------------------------------------------
 */
/* Probe I2C driver */
static int inspur_i2c_cpld_probe(struct i2c_client *client,
                                 const struct i2c_device_id *dev_id)
{
    int status;
    struct inspur_cpld_data* data;

    if (!i2c_check_functionality(client->adapter, I2C_FUNC_SMBUS_BYTE_DATA)) {
        dev_dbg(&client->dev, "i2c_check_functionality failed (0x%x)\n", client->addr);
        status = -EIO;
        goto exit;
    }

    data = kzalloc(sizeof(struct inspur_cpld_data), GFP_KERNEL);
    if (!data) {
      status = -ENOMEM;
      goto exit;
    }

    status = sysfs_create_group(&client->dev.kobj, &inspur_sc5630el_cpld_group);
    if (status) {
      goto exit;
    }

    dev_info(&client->dev, "chip found\n");
    inspur_i2c_cpld_add_client(client);

    data->hwmon_dev = hwmon_device_register(&client->dev);
    if (IS_ERR(data->hwmon_dev)) {
      status = PTR_ERR(data->hwmon_dev);
      goto exit;
    }

    dev_info(&client->dev, "%s: cpld '%s'\n",
             dev_name(data->hwmon_dev), client->name);

    return 0;

exit:
    return status;
}

static int inspur_i2c_cpld_remove(struct i2c_client *client)
{
    struct inspur_cpld_data *data = i2c_get_clientdata(client);
    sysfs_remove_group(&client->dev.kobj, &inspur_sc5630el_cpld_group);
    inspur_i2c_cpld_remove_client(client);
    kfree(data);

    return 0;
}
/* ----------------------------------------------------------------------------
 * Module main functions
 * ----------------------------------------------------------------------------
 */
static const struct i2c_device_id inspur_i2c_cpld_id[] = {
    { DRIVER_NAME, 0 },
    {}
};
MODULE_DEVICE_TABLE(i2c, inspur_i2c_cpld_id);

static struct i2c_driver inspur_i2c_cpld_driver = {
    .class		= I2C_CLASS_HWMON,
    .driver = {
        .name = DRIVER_NAME,
    },
    .probe		= inspur_i2c_cpld_probe,
    .remove	   	= inspur_i2c_cpld_remove,
    .id_table	= inspur_i2c_cpld_id,
    .address_list = normal_i2c,
};

int inspur_i2c_cpld_read(unsigned short cpld_addr, u8 reg)
{
    struct list_head   *list_node = NULL;
    struct cpld_client_node *cpld_node = NULL;
    int ret = -EPERM;

    mutex_lock(&list_lock);

    list_for_each(list_node, &cpld_client_list)
    {
        cpld_node = list_entry(list_node, struct cpld_client_node, list);

        if (cpld_node->client->addr == cpld_addr) {
            ret = i2c_smbus_read_byte_data(cpld_node->client, reg);
            break;
        }
    }

    mutex_unlock(&list_lock);

    return ret;
}
EXPORT_SYMBOL(inspur_i2c_cpld_read);

int inspur_i2c_cpld_write(unsigned short cpld_addr, u8 reg, u8 value)
{
    struct list_head   *list_node = NULL;
    struct cpld_client_node *cpld_node = NULL;
    int ret = -EIO;

    mutex_lock(&list_lock);

    list_for_each(list_node, &cpld_client_list)
    {
        cpld_node = list_entry(list_node, struct cpld_client_node, list);

        if (cpld_node->client->addr == cpld_addr) {
            ret = i2c_smbus_write_byte_data(cpld_node->client, reg, value);
            break;
        }
    }

    mutex_unlock(&list_lock);

    return ret;
}
EXPORT_SYMBOL(inspur_i2c_cpld_write);

static int __init inspur_i2c_cpld_init(void)
{
    mutex_init(&list_lock);
    return i2c_add_driver(&inspur_i2c_cpld_driver);
}

static void __exit inspur_i2c_cpld_exit(void)
{
    i2c_del_driver(&inspur_i2c_cpld_driver);
}

static struct dmi_system_id inspur_sc5630el_dmi_table[] = {
    {
        .ident = "inspur sc5630el",
        .matches = {
            DMI_MATCH(DMI_SYS_VENDOR, "inspur"),
            DMI_MATCH(DMI_PRODUCT_NAME, "sc5630el"),
        },
    }
};

int platform_inspur_sc5630el(void)
{
    return dmi_check_system(inspur_sc5630el_dmi_table);
}
EXPORT_SYMBOL(platform_inspur_sc5630el);

module_init(inspur_i2c_cpld_init);
module_exit(inspur_i2c_cpld_exit);


MODULE_AUTHOR("sdn@inspur.com");
MODULE_VERSION("1.0");
MODULE_DESCRIPTION("Inspur cpld driver");
MODULE_LICENSE("GPL");

