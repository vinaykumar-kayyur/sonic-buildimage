/*
 *  Inspur Platform Driver of SC5630EL
 *
 *
 *  Copyright (C) 2018 Inspur Electronic Information Industry Co.,Ltd
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program; if not, write to the Free Software
 *  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 */

#define pr_fmt(fmt) KBUILD_MODNAME ": " fmt

#include <linux/version.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/init.h>
#include <linux/types.h>
#include <linux/err.h>
#include <linux/proc_fs.h>
#include <linux/leds.h>
#include <linux/platform_device.h>
#include <linux/slab.h>
#if (LINUX_VERSION_CODE < KERNEL_VERSION(3,16,0))
#include <linux/i2c/pca953x.h>
#include <linux/i2c/pca954x.h>
#else
#include <linux/platform_data/pca953x.h>
#include <linux/platform_data/pca954x.h>
#endif
//#include <linux/i2c/pmbus.h>
#include <linux/pmbus.h>

#define MUX_INFO(bus, deselect) \
	{.adap_id = bus, .deselect_on_exit = deselect}

// 9641 devices
static struct pca954x_platform_mode pca9641_1_modes[] = {
	MUX_INFO(0x60, 1),
};
static struct pca954x_platform_data pca9641_1_data = {
	.modes 		= pca9641_1_modes,
	.num_modes 	= 1,
};

static struct pca954x_platform_mode pca9641_2_modes[] = {
	MUX_INFO(0x61, 1),
};
static struct pca954x_platform_data pca9641_2_data = {
	.modes 		= pca9641_2_modes,
	.num_modes 	= 1,
};

static struct pca954x_platform_mode pca9641_3_modes[] = {
	MUX_INFO(0x62, 1),
};
static struct pca954x_platform_data pca9641_3_data = {
	.modes 		= pca9641_3_modes,
	.num_modes 	= 1,
};

static struct pca954x_platform_mode pca9641_4_modes[] = {
	MUX_INFO(0x63, 1),
};
static struct pca954x_platform_data pca9641_4_data = {
	.modes 		= pca9641_4_modes,
	.num_modes 	= 1,
};

static struct pca954x_platform_mode pca9641_5_modes[] = {
	MUX_INFO(0x64, 1),
};
static struct pca954x_platform_data pca9641_5_data = {
	.modes 		= pca9641_5_modes,
	.num_modes 	= 1,
};

static struct pca954x_platform_mode pca9641_6_modes[] = {
	MUX_INFO(0x65, 1),
};
static struct pca954x_platform_data pca9641_6_data = {
	.modes 		= pca9641_6_modes,
	.num_modes 	= 1,
};

static struct pca954x_platform_mode pca9641_7_modes[] = {
	MUX_INFO(0x66, 1),
};
static struct pca954x_platform_data pca9641_7_data = {
	.modes 		= pca9641_7_modes,
	.num_modes 	= 1,
};

static struct pca954x_platform_mode pca9641_8_modes[] = {
	MUX_INFO(0x67, 1),
};
static struct pca954x_platform_data pca9641_8_data = {
	.modes 		= pca9641_8_modes,
	.num_modes 	= 1,
};

// start port io
// SFP
static struct pca954x_platform_mode pca9548_sfp1_modes[] = {
	MUX_INFO(0x20, 1),
	MUX_INFO(0x21, 1),
	MUX_INFO(0x22, 1),
	MUX_INFO(0x23, 1),
	MUX_INFO(0x24, 1),
	MUX_INFO(0x25, 1),
	MUX_INFO(0x26, 1),
	MUX_INFO(0x27, 1),
};

static struct pca954x_platform_data pca9548_sfp1_data = {
	.modes 		= pca9548_sfp1_modes,
	.num_modes 	= 8,
};

static struct pca954x_platform_mode pca9548_sfp2_modes[] = {
	MUX_INFO(0x28, 1),
	MUX_INFO(0x29, 1),
	MUX_INFO(0x2a, 1),
	MUX_INFO(0x2b, 1),
	MUX_INFO(0x2c, 1),
	MUX_INFO(0x2d, 1),
	MUX_INFO(0x2e, 1),
	MUX_INFO(0x2f, 1),
};

static struct pca954x_platform_data pca9548_sfp2_data = {
	.modes 		= pca9548_sfp2_modes,
	.num_modes 	= 8,
};
static struct pca954x_platform_mode pca9548_sfp3_modes[] = {
	MUX_INFO(0x30, 1),
	MUX_INFO(0x31, 1),
	MUX_INFO(0x32, 1),
	MUX_INFO(0x33, 1),
	MUX_INFO(0x34, 1),
	MUX_INFO(0x35, 1),
	MUX_INFO(0x36, 1),
	MUX_INFO(0x37, 1),
};

static struct pca954x_platform_data pca9548_sfp3_data = {
	.modes 		= pca9548_sfp3_modes,
	.num_modes 	= 8,
};

static struct pca954x_platform_mode pca9548_sfp4_modes[] = {
	MUX_INFO(0x38, 1),
	MUX_INFO(0x39, 1),
	MUX_INFO(0x3a, 1),
	MUX_INFO(0x3b, 1),
	MUX_INFO(0x3c, 1),
	MUX_INFO(0x3d, 1),
	MUX_INFO(0x3e, 1),
	MUX_INFO(0x3f, 1),
};

static struct pca954x_platform_data pca9548_sfp4_data = {
	.modes 		= pca9548_sfp4_modes,
	.num_modes 	= 8,
};

static struct pca954x_platform_mode pca9548_sfp5_modes[] = {
	MUX_INFO(0x40, 1),
	MUX_INFO(0x41, 1),
	MUX_INFO(0x42, 1),
	MUX_INFO(0x43, 1),
	MUX_INFO(0x44, 1),
	MUX_INFO(0x45, 1),
	MUX_INFO(0x46, 1),
	MUX_INFO(0x47, 1),
};

static struct pca954x_platform_data pca9548_sfp5_data = {
	.modes 		= pca9548_sfp5_modes,
	.num_modes 	= 8,
};

static struct pca954x_platform_mode pca9548_sfp6_modes[] = {
	MUX_INFO(0x48, 1),
	MUX_INFO(0x49, 1),
	MUX_INFO(0x4a, 1),
	MUX_INFO(0x4b, 1),
	MUX_INFO(0x4c, 1),
	MUX_INFO(0x4d, 1),
	MUX_INFO(0x4e, 1),
	MUX_INFO(0x4f, 1),
};

static struct pca954x_platform_data pca9548_sfp6_data = {
	.modes 		= pca9548_sfp6_modes,
	.num_modes 	= 8,
};

// QSFP28
static struct pca954x_platform_mode pca9548_qsfp_modes[] = {
	MUX_INFO(0x50, 1),
	MUX_INFO(0x51, 1),
	MUX_INFO(0x52, 1),
	MUX_INFO(0x53, 1),
	MUX_INFO(0x54, 1),
	MUX_INFO(0x55, 1),
	MUX_INFO(0x56, 1),
	MUX_INFO(0x57, 1),
};

static struct pca954x_platform_data pca9548_qsfp_data = {
	.modes 		= pca9548_qsfp_modes,
	.num_modes 	= 8,
};

// end port io

// root
static struct pca954x_platform_mode pca9548_root_modes[] = {
	MUX_INFO(0x10, 1),
	MUX_INFO(0x11, 1),
	MUX_INFO(0x12, 1),
	MUX_INFO(0x13, 1),
	MUX_INFO(0x14, 1),
	MUX_INFO(0x15, 1),
	MUX_INFO(0x16, 1),
	MUX_INFO(0x17, 1),
};

static struct pca954x_platform_data pca9548_root_data = {
	.modes 		= pca9548_root_modes,
	.num_modes 	= 8,
};

// mutiplex 8 and 6 9555s for port pin control
static struct pca954x_platform_mode pca9546_portmux_modes[] = {
	MUX_INFO(0x18, 1),
	MUX_INFO(0x19, 1),
	MUX_INFO(0x1a, 1),	//not used
	MUX_INFO(0x1b, 1),	//not used
};

static struct pca954x_platform_data pca9546_portmux_data = {
	.modes 		= pca9546_portmux_modes,
	.num_modes 	= 4,
};


#if 0
/* CPU Board i2c device */
static struct pca954x_platform_mode pca9546_cpu_modes[] = {
	MUX_INFO(0x02, 1),
	MUX_INFO(0x03, 1),
	MUX_INFO(0x04, 1),
	MUX_INFO(0x05, 1),
};

static struct pca954x_platform_data pca9546_cpu_data = {
	.modes 		= pca9546_cpu_modes,
	.num_modes 	= 4,
};
#endif

// FAN led
static struct pca953x_platform_data pca9555_fanled_data = {
	.gpio_base = 0x10,
};
// HW alert
static struct pca953x_platform_data pca9555_hwalert_data = {
	.gpio_base = 0x20,
};

// SFP 1-16 tx_fault
static struct pca953x_platform_data pca9555_txfault1_data = {
	.gpio_base = 0x30,
};
// SFP 17-32 tx_fault
static struct pca953x_platform_data pca9555_txfault2_data = {
	.gpio_base = 0x40,
};
// SFP 33-48 tx_fault
static struct pca953x_platform_data pca9555_txfault3_data = {
	.gpio_base = 0x50,
};
// SFP 1-16 rx_los
static struct pca953x_platform_data pca9555_rxlos1_data = {
	.gpio_base = 0x60,
};
// SFP 17-32 rx_los
static struct pca953x_platform_data pca9555_rxlos2_data = {
	.gpio_base = 0x70,
};
// SFP 33-48 rx_los
static struct pca953x_platform_data pca9555_rxlos3_data = {
	.gpio_base = 0x80,
};
// SFP 1-16 tx_disable
static struct pca953x_platform_data pca9555_txdisable1_data = {
	.gpio_base = 0x90,
};
// SFP 17-32 tx_disable
static struct pca953x_platform_data pca9555_txdisable2_data = {
	.gpio_base = 0xA0,
};
// SFP 33-48 tx_disable
static struct pca953x_platform_data pca9555_txdisable3_data = {
	.gpio_base = 0xB0,
};
// SFP 1-16 mod_absent
static struct pca953x_platform_data pca9555_modabsent1_data = {
	.gpio_base = 0xC0,
};
// SFP 17-32 mod_absent
static struct pca953x_platform_data pca9555_modabsent2_data = {
	.gpio_base = 0xD0,
};
// SFP 33-48 mod_absent
static struct pca953x_platform_data pca9555_modabsent3_data = {
	.gpio_base = 0xE0,
};
// QSFP 1-8 lpmode
static struct pca953x_platform_data pca9555_lpmode_data = {
	.gpio_base = 0xF0,
};
// QSFP 1-8 interrupt, present
static struct pca953x_platform_data pca9555_intrpresent_data = {
	.gpio_base = 0x100,
};

static struct pmbus_platform_data liteon_pdata = { 
 	.flags = PMBUS_SKIP_STATUS_CHECK, 
}; 



static struct i2c_board_info sc5630el_i2c_devices[] = {
	{
		I2C_BOARD_INFO("pca9548", 0x77),		// 0
		.platform_data = &pca9548_root_data,
	},
	{
		I2C_BOARD_INFO("inspur-sfpio", 0x20),	// 9548 ch0, port control
	},
	{
		I2C_BOARD_INFO("24c16", 0x50),	// 9548 ch1, eeprom
	},
	{
		I2C_BOARD_INFO("inspur-pca9641", 0x73),	// 9548 ch2, sensor
		.platform_data = &pca9641_3_data,
	},
	{
		I2C_BOARD_INFO("inspur-pca9641", 0x76),	// 9548 ch5, psu
		.platform_data = &pca9641_4_data,
	},
	{
		I2C_BOARD_INFO("inspur-pca9641", 0x71),	// 9548 ch6, alert
		.platform_data = &pca9641_5_data,
	},
	{
		I2C_BOARD_INFO("inspur-pca9641", 0x0a),	// 9548 ch6, cpld
		.platform_data = &pca9641_6_data,
	},
	{
		I2C_BOARD_INFO("inspur-pca9641", 0x0b),	// 9548 ch6, fan present
		.platform_data = &pca9641_7_data,
	},
	{
		I2C_BOARD_INFO("inspur-optoe", 0x50),	// 9548 ch7, port eeprom
	},
	{
		I2C_BOARD_INFO("pca9546", 0x71),		// 9 0x77 ch0
		.platform_data = &pca9546_portmux_data,
	},
	{
		I2C_BOARD_INFO("dummy", 0xCC),		// 0x77 ch1
	},
	{
		I2C_BOARD_INFO("dummy", 0xDD),		// 0x77 ch1
	},
	{
		I2C_BOARD_INFO("emc1413", 0x5c),		// 0x77 ch2 switch 1-3
	},
	{
		I2C_BOARD_INFO("emc1413", 0x4c),		// 0x77 ch2 switch 4-6
	},
	{
		I2C_BOARD_INFO("emc1413", 0x1c),		// 0x77 ch2 switch 7-9
	},
	{
		I2C_BOARD_INFO("emc1413", 0x6c),		// 0x77 ch2 cpu 1-3
	},
	{
		I2C_BOARD_INFO("ps2551", 0x58),		// 0x77 ch5
		.platform_data = &liteon_pdata,
	},
	{
		I2C_BOARD_INFO("ps2551", 0x59),		// 0x77 ch5
		.platform_data = &liteon_pdata,
	},
	{
		I2C_BOARD_INFO("pca9555", 0x25),		// 18 0x77 ch6
		.platform_data = &pca9555_fanled_data,
	},
	{
		I2C_BOARD_INFO("pca9555", 0x20),		// 0x77 ch6
		.platform_data = &pca9555_hwalert_data,
	},
	{
		I2C_BOARD_INFO("pca9548", 0x70),		// 20 0x77 ch7
		.platform_data = &pca9548_sfp1_data,
	},
	{
		I2C_BOARD_INFO("pca9548", 0x71),		// 0x77 ch7
		.platform_data = &pca9548_sfp2_data,
	},
	{
		I2C_BOARD_INFO("pca9548", 0x72),		// 0x77 ch7
		.platform_data = &pca9548_sfp3_data,
	},
	{
		I2C_BOARD_INFO("pca9548", 0x73),		// 0x77 ch7
		.platform_data = &pca9548_sfp4_data,
	},
	{
		I2C_BOARD_INFO("pca9548", 0x74),		// 0x77 ch7
		.platform_data = &pca9548_sfp5_data,
	},
	{
		I2C_BOARD_INFO("pca9548", 0x75),		// 0x77 ch7
		.platform_data = &pca9548_sfp6_data,
	},
	{
		I2C_BOARD_INFO("pca9548", 0x76),		// 26 0x77 ch7
		.platform_data = &pca9548_qsfp_data,
	},
	{
		I2C_BOARD_INFO("pca9555", 0x21),		// 0x71 ch0
		.platform_data = &pca9555_txfault1_data,
	},
	{
		I2C_BOARD_INFO("pca9555", 0x22),		// 0x71 ch0
		.platform_data = &pca9555_txfault2_data,
	},
	{
		I2C_BOARD_INFO("pca9555", 0x23),		// 0x71 ch0
		.platform_data = &pca9555_txfault3_data,
	},
	{
		I2C_BOARD_INFO("pca9555", 0x24),		// 0x71 ch0
		.platform_data = &pca9555_rxlos1_data,
	},
	{
		I2C_BOARD_INFO("pca9555", 0x25),		// 0x71 ch0
		.platform_data = &pca9555_rxlos2_data,
	},
	{
		I2C_BOARD_INFO("pca9555", 0x26),		// 0x71 ch0
		.platform_data = &pca9555_rxlos3_data,
	},
	{
		I2C_BOARD_INFO("pca9555", 0x20),		// 0x71 ch0
		.platform_data = &pca9555_lpmode_data,
	},
	{
		I2C_BOARD_INFO("pca9555", 0x27),		// 34 0x71 ch0
		.platform_data = &pca9555_intrpresent_data,
	},
	{
		I2C_BOARD_INFO("pca9555", 0x20),		// 0x71 ch1
		.platform_data = &pca9555_txdisable1_data,
	},
	{
		I2C_BOARD_INFO("pca9555", 0x21),		// 0x71 ch1
		.platform_data = &pca9555_txdisable2_data,
	},
	{
		I2C_BOARD_INFO("pca9555", 0x22),		// 0x71 ch1
		.platform_data = &pca9555_txdisable3_data,
	},
	{
		I2C_BOARD_INFO("pca9555", 0x23),		// 0x71 ch1
		.platform_data = &pca9555_modabsent1_data,
	},
	{
		I2C_BOARD_INFO("pca9555", 0x24),		// 0x71 ch1
		.platform_data = &pca9555_modabsent2_data,
	},
	{
		I2C_BOARD_INFO("pca9555", 0x25),		// 40 0x71 ch1
		.platform_data = &pca9555_modabsent3_data,
	},
	{
		I2C_BOARD_INFO("optoe2", 0x50),		// sfp eeprom 
	},
	{
		I2C_BOARD_INFO("optoe1", 0x50),		// qsfp eeprom 
	},
	{
		I2C_BOARD_INFO("inspur_cpld", 0x68),		// cpld
	},

};

static struct platform_driver sc5630el_platform_driver = {
	.driver = {
		.name = "inspur-sc5630el",
		.owner = THIS_MODULE,
	},
};

static struct platform_device *sc5630el_device;

static int __init sc5630el_platform_init(void)
{
	struct i2c_client *client;
	struct i2c_adapter *adapter;
	int ret, i;

	ret = platform_driver_register(&sc5630el_platform_driver);
	if (ret < 0)
		return ret;

	/* Register platform stuff */
	sc5630el_device = platform_device_alloc("inspur-sc5630el", -1);
	if (!sc5630el_device) {
		ret = -ENOMEM;
		goto fail_platform_driver;
	}

	ret = platform_device_add(sc5630el_device);
	if (ret)
		goto fail_platform_device;

// root
	adapter = i2c_get_adapter(0);
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[0]);		// root 9548
	i2c_put_adapter(adapter);
	dev_err(&client->dev, "[CC] i2c_get_adapter(0) end\n");
	
// 9641 muxes
	adapter = i2c_get_adapter(0x10);
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[1]);		// port control
	i2c_put_adapter(adapter);
	dev_err(&client->dev, "[CC] i2c_get_adapter(10) end\n");

	adapter = i2c_get_adapter(0x11);
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[2]);		// eeprom
	i2c_put_adapter(adapter);

	adapter = i2c_get_adapter(0x12);
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[3]);		// sensor
	i2c_put_adapter(adapter);

	adapter = i2c_get_adapter(0x15);
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[4]);		// psu
	i2c_put_adapter(adapter);

	adapter = i2c_get_adapter(0x16);
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[5]);		// alert
	i2c_put_adapter(adapter);

	adapter = i2c_get_adapter(0x16);
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[6]);		// cpld
	i2c_put_adapter(adapter);

	adapter = i2c_get_adapter(0x16);
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[7]);		// fan present
	i2c_put_adapter(adapter);

	adapter = i2c_get_adapter(0x17);
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[8]);		// port eeprom
	i2c_put_adapter(adapter);
	dev_err(&client->dev, "[CC] i2c_get_adapter(17) end\n");

/*
	adapter = i2c_get_adapter(0x60);
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[9]);		// 9546_portmux
	i2c_put_adapter(adapter);
	dev_err(&client->dev, "[CC] i2c_get_adapter(60) end\n");
*/

	//adapter = i2c_get_adapter(0x61);
	//client = i2c_new_device(adapter, &sc5630el_i2c_devices[10]);		// dummy
	//client = i2c_new_device(adapter, &sc5630el_i2c_devices[11]);		// dummy
	//i2c_put_adapter(adapter);
	//dev_err(&client->dev, "[CC] i2c_get_adapter(61) end - remove 9641\n");

	adapter = i2c_get_adapter(0x62);
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[12]);		// emc1413
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[13]);		// emc1413
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[14]);		// emc1413
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[15]);		// emc1413
	i2c_put_adapter(adapter);

	adapter = i2c_get_adapter(0x63);
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[16]);		// psu0
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[17]);		// psu1
	i2c_put_adapter(adapter);

	adapter = i2c_get_adapter(0x64);
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[19]);		// hwalert
	i2c_put_adapter(adapter);

	adapter = i2c_get_adapter(0x65);
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[43]);		// cpld
	i2c_put_adapter(adapter);

	adapter = i2c_get_adapter(0x66);
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[18]);		// fanled
	i2c_put_adapter(adapter);

/*
	adapter = i2c_get_adapter(0x67);
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[20]);		// SFP1
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[21]);		// SFP2
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[22]);		// SFP3
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[23]);		// SFP4
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[24]);		// SFP5
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[25]);		// SFP6
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[26]);		// QSFP
	i2c_put_adapter(adapter);
	dev_err(&client->dev, "[CC] i2c_get_adapter(67) end\n");
*/

/*
	adapter = i2c_get_adapter(0x18);
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[27]);		// txfault1
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[28]);		// txfault2
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[29]);		// txfault3
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[30]);		// rxlos1
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[31]);		// rxlos2
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[32]);		// rxlos3
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[33]);		// lpmode
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[34]);		// intr,present
	i2c_put_adapter(adapter);
	dev_err(&client->dev, "[CC] i2c_get_adapter(18) end\n");

	adapter = i2c_get_adapter(0x19);
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[35]);		// txdisable1
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[36]);		// txdisable2
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[37]);		// txdisable3
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[38]);		// modabsent1
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[39]);		// modabsent2
	client = i2c_new_device(adapter, &sc5630el_i2c_devices[40]);		// modabsent3
	i2c_put_adapter(adapter);
	dev_err(&client->dev, "[CC] i2c_get_adapter(19) end\n");
*/

/*
	for(i = 32; i < 80; i ++){									// SFP28 1~48 EEPROM
		adapter = i2c_get_adapter(i);
		client = i2c_new_device(adapter, &sc5630el_i2c_devices[41]);
		i2c_put_adapter(adapter);
	}
	for(i = 80; i < 88; i ++){									// QSFP 49~56 EEPROM
		adapter = i2c_get_adapter(i);
		client = i2c_new_device(adapter, &sc5630el_i2c_devices[42]);
		i2c_put_adapter(adapter);
	}
*/

	return 0;

fail_platform_device:
	platform_device_put(sc5630el_device);

fail_platform_driver:
	platform_driver_unregister(&sc5630el_platform_driver);
	return ret;
}

static void __exit sc5630el_platform_exit(void)
{
	platform_device_unregister(sc5630el_device);
	platform_driver_unregister(&sc5630el_platform_driver);
}

module_init(sc5630el_platform_init);
module_exit(sc5630el_platform_exit);


//MODULE_AUTHOR("ChihPei Chang <chihpeichang@inspur.com>");
MODULE_AUTHOR("switchsupport@inspur.com");
MODULE_VERSION("1.0");
MODULE_DESCRIPTION("Inspur Platform Driver of SC5630EL");
MODULE_LICENSE("GPL");
