#ifndef _DEF_H
#define _DEF_H

/* Reserve some bus numbers for CPU or FPGA */
#define I2C_BUS_OFS				15
#define I2C_Port_B_OFS  		I2C_BUS_OFS + 21 /*i2c ocores bus + PCA9548 bus*/

#undef BMC_ON_BOARD

#define FPGA_DEVICE_ID      	0x7021
#define FPGA_MMIO_BAR			0
#define SWITCH_CPLD_ADAP_1    	1
#define SWITCH_CPLD_ADAP_2    	2
#define SWITCH_CPLD_ADAP_7    	7
#define SFP_PORT_PCA9548_ADD	0x71

#define MODPRS_IRQ_CPLD1_1_8    0x34
#define MODPRS_IRQ_CPLD1_9_16   0x37
#define MODPRS_IRQ_CPLD2_17_24  0x37
#define MODPRS_IRQ_CPLD2_25_32  0x34

#define LPMOD_CPLD1_1_8         0x11
#define LPMOD_CPLD1_9_16        0x12
#define LPMOD_CPLD2_17_24       0x12
#define LPMOD_CPLD2_25_32       0x11

#define RESET_CPLD1_1_8         0x20
#define RESET_CPLD1_9_16        0x21
#define RESET_CPLD2_17_24       0x21
#define RESET_CPLD2_25_32       0x20

#define MODPRS_CPLD1_1_8        0x40
#define MODPRS_CPLD1_9_16       0x41
#define MODPRS_CPLD2_17_24      0x41
#define MODPRS_CPLD2_25_32      0x40
#endif
