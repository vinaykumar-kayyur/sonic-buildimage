#include <linux/device.h>
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/sysfs.h>
#include <linux/init.h>
#include <linux/slab.h>
#include <linux/dmi.h>
#include <linux/version.h>
#include <linux/ctype.h>
#include <linux/platform_device.h>
#include <linux/i2c.h>
#include <linux/i2c-mux.h>
#include <linux/i2c/sff-8436.h>
#include <linux/platform_data/pca954x.h>
#include <linux/platform_data/i2c-mux-gpio.h>
#include <linux/hwmon.h>
#include <linux/hwmon-sysfs.h>



#define ag7648v2_i2c_device_num(c){                                         \
        .name                   = "delta-ag7648v2-i2c-device",                \
        .id                     = c,                                        \
        .dev                    = {                                           \
                    .platform_data = &ag7648v2_i2c_device_platform_data[c], \
                    .release       = device_release,                          \
        },                                                                    \
}



/* Define struct to get client of i2c_new_deivce at 0x70 */
struct i2c_client * i2c_client_9548_main;
struct i2c_client * i2c_client_9548_fan;
struct i2c_client * i2c_client_9548_sfp_main_mux;

enum{
    BUS0 = 0,
    BUS1,
    BUS2,
    BUS3,
    BUS4,
    BUS5,
    BUS6,
    BUS7,
    BUS8,
};

struct i2c_device_platform_data {
    int parent;
    struct i2c_board_info           info;
    struct i2c_client              *client;
};

/* Main pca9548 on CPU Board - add 8 bus */
static struct pca954x_platform_mode pca954x_main_mode[] = {
  { .adap_id = 2,
    .deselect_on_exit = 1,
  },
  { .adap_id = 3,
    .deselect_on_exit = 1,
  },
  { .adap_id = 4,
    .deselect_on_exit = 1,
  },
  { .adap_id = 5,
    .deselect_on_exit = 1,
  },
  { .adap_id = 6,
    .deselect_on_exit = 1,
  },
  { .adap_id = 7,
    .deselect_on_exit = 1,
  },
  { .adap_id = 8,
    .deselect_on_exit = 1,
  },
  { .adap_id = 9,
    .deselect_on_exit = 1,
  },
};

/* pca9548 on fan Board - add 8 bus */
static struct pca954x_platform_mode pca954x_fan_mode[] = {
  { .adap_id = 21,
    .deselect_on_exit = 1,
  },
  { .adap_id = 22,
    .deselect_on_exit = 1,
  },
  { .adap_id = 23,
    .deselect_on_exit = 1,
  },
  { .adap_id = 24,
    .deselect_on_exit = 1,
  },
  { .adap_id = 25,
    .deselect_on_exit = 1,
  },
  { .adap_id = 26,
    .deselect_on_exit = 1,
  },
  { .adap_id = 27,
    .deselect_on_exit = 1,
  },
  { .adap_id = 28,
    .deselect_on_exit = 1,
  },
};

/* pca9548 mux of seven pca9848s for SFPs on System Board - add 8 bus */
static struct pca954x_platform_mode pca954x_sfp_main_mux_mode[] = {
  { .adap_id = 51,
    .deselect_on_exit = 1,
  },
  { .adap_id = 52,
    .deselect_on_exit = 1,
  },
  { .adap_id = 53,
    .deselect_on_exit = 1,
  },
  { .adap_id = 54,
    .deselect_on_exit = 1,
  },
  { .adap_id = 55,
    .deselect_on_exit = 1,
  },
  { .adap_id = 56,
    .deselect_on_exit = 1,
  },
  { .adap_id = 57,
    .deselect_on_exit = 1,
  },
  { .adap_id = 58,
    .deselect_on_exit = 1,
  },
};

static struct pca954x_platform_data pca954x_main_data = {
  .modes = pca954x_main_mode,
  .num_modes = ARRAY_SIZE(pca954x_main_mode),
};

static struct pca954x_platform_data pca954x_fan_data = {
  .modes = pca954x_fan_mode,
  .num_modes = ARRAY_SIZE(pca954x_fan_mode),
};

static struct pca954x_platform_data pca954x_sfp_main_mux_data = {
  .modes = pca954x_sfp_main_mux_mode,
  .num_modes = ARRAY_SIZE(pca954x_sfp_main_mux_mode),
};

static struct i2c_board_info __initdata i2c_info_pca9548_main[] =
{
        {
            I2C_BOARD_INFO("pca9548", 0x70),
            .platform_data = &pca954x_main_data,
        },
};

static struct i2c_board_info __initdata i2c_info_pca9548_fan[] =
{
        {
            I2C_BOARD_INFO("pca9548", 0x71),
            .platform_data = &pca954x_fan_data,
        },
};

static struct i2c_board_info __initdata i2c_info_pca9548_sfp_main_mux[] =
{
        {
            I2C_BOARD_INFO("pca9548", 0x71),
            .platform_data = &pca954x_sfp_main_mux_data,
        },
};

static struct i2c_device_platform_data ag7648v2_i2c_device_platform_data[] = {
    {
        /* Fan5 EEPROM (0x50) */
        .parent = 21,
        .info = { I2C_BOARD_INFO("24c02", 0x50) },
        .client = NULL,
    },
    {
        /* Fan4 EEPROM (0x50) */
        .parent = 22,
        .info = { I2C_BOARD_INFO("24c02", 0x50) },
        .client = NULL,
    },
    {
        /* Fan3 EEPROM (0x50) */
        .parent = 23,
        .info = { I2C_BOARD_INFO("24c02", 0x50) },
        .client = NULL,
    },
    {
        /* Fan2 EEPROM (0x50) */
        .parent = 24,
        .info = { I2C_BOARD_INFO("24c02", 0x50) },
        .client = NULL,
    },
    {
        /* Fan1 EEPROM (0x50) */
        .parent = 25,
        .info = { I2C_BOARD_INFO("24c02", 0x50) },
        .client = NULL,
    },
    {
        /* Front FAN Controller (0x2c) */
        .parent = 26,
        .info = { I2C_BOARD_INFO("emc2305", 0x2c) },
        .client = NULL,
    },
    {
        /* Rear FAN Controller (0x2d) */
        .parent = 26,
        .info = { I2C_BOARD_INFO("emc2305", 0x2d) },
        .client = NULL,
    },
	{
        /* tmp75 (0x4f) @ near FAN */
        .parent = 27,
        .info = { I2C_BOARD_INFO("tmp75", 0x4f) },
        .client = NULL,
    },
    {
        /* GPIO expander (0x27) */
        .parent = 28,
        .info = { I2C_BOARD_INFO("pca9555", 0x27) },
        .client = NULL,
    },
    {
        /* at24c08d (0x50) */
        .parent = 3,
        .info = { I2C_BOARD_INFO("24c08", 0x50) },
        .client = NULL,
    },
    {
        /* tmp75 (0x4d) @ upper right of MAC */
        .parent = 4,
        .info = { I2C_BOARD_INFO("tmp75", 0x4d) },
        .client = NULL,
    },
    {
        /* tmp75 (0x4e) @ lower left of MAC */
        .parent = 4,
        .info = { I2C_BOARD_INFO("tmp75", 0x4e) },
        .client = NULL,
    },
    {
        /* tmp75 (0x4f) @ lower left of CPU on CPU Board */
        .parent = 4,
        .info = { I2C_BOARD_INFO("tmp75", 0x4f) },
        .client = NULL,
    },
    {
        /* psu1 (0x50) */
        .parent = 6,
        .info = { I2C_BOARD_INFO("24c08", 0x50) },
        .client = NULL,
    },
    {
        /* psu 1 (0x58) */
        .parent = 6,
        .info = { .type = "dni_ag7648v2_psu", .addr = 0x58, .platform_data = (void *) 0 },
        .client = NULL,
    },
    {
        /* psu2 (0x50) */
        .parent = 7,
        .info = { I2C_BOARD_INFO("24c08", 0x50) },
        .client = NULL,
    },
    {
        /* psu 2 (0x58) */
        .parent = 7,
        .info = { .type = "dni_ag7648v2_psu", .addr = 0x58, .platform_data = (void *) 0 },
        .client = NULL,
    },
};

static void device_release(struct device *dev)
{
    return;
}

static struct platform_device ag7648v2_i2c_device[] = {
    ag7648v2_i2c_device_num(0),
    ag7648v2_i2c_device_num(1),
    ag7648v2_i2c_device_num(2),
    ag7648v2_i2c_device_num(3),
    ag7648v2_i2c_device_num(4),
    ag7648v2_i2c_device_num(5),
    ag7648v2_i2c_device_num(6),
    ag7648v2_i2c_device_num(7),
    ag7648v2_i2c_device_num(8),
    ag7648v2_i2c_device_num(9),
    ag7648v2_i2c_device_num(10),
    ag7648v2_i2c_device_num(11),
    ag7648v2_i2c_device_num(12),
    ag7648v2_i2c_device_num(13),
    ag7648v2_i2c_device_num(14),
    ag7648v2_i2c_device_num(15),
    ag7648v2_i2c_device_num(16),
};

static int __init i2c_device_probe(struct platform_device *pdev)
{
    struct i2c_device_platform_data *pdata;
    struct i2c_adapter *parent;

    pdata = pdev->dev.platform_data;
    if (!pdata) {
        dev_err(&pdev->dev, "Missing platform data\n");
        return -ENODEV;
    }

    parent = i2c_get_adapter(pdata->parent);
    if (!parent) {
        dev_err(&pdev->dev, "Parent adapter (%d) not found\n",
            pdata->parent);
        return -ENODEV;
    }

    pdata->client = i2c_new_device(parent, &pdata->info);
    if (!pdata->client) {
        dev_err(&pdev->dev, "Failed to create i2c client %s at %d\n",
            pdata->info.type, pdata->parent);
        return -ENODEV;
    }

    return 0;
}

static int __exit i2c_deivce_remove(struct platform_device *pdev)
{
    struct i2c_adapter *parent;
    struct i2c_device_platform_data *pdata;

    pdata = pdev->dev.platform_data;
    if (!pdata) {
        dev_err(&pdev->dev, "Missing platform data\n");
        return -ENODEV;
    }

    if (pdata->client) {
        parent = (pdata->client)->adapter;
        i2c_unregister_device(pdata->client);
        i2c_put_adapter(parent);
    }

    return 0;
}


static struct platform_driver i2c_device_driver = {
    .probe = i2c_device_probe,
    .remove = __exit_p(i2c_deivce_remove),
    .driver = {
        .owner = THIS_MODULE,
        .name = "delta-ag7648v2-i2c-device",
    }
};

static struct platform_driver i2c_fan_device_driver = {
    .probe = i2c_device_probe,
    .remove = __exit_p(i2c_deivce_remove),
    .driver = {
        .owner = THIS_MODULE,
        .name = "delta-ag7648v2-i2c-fan-device",
    }
};

static struct platform_driver i2c_sfp_main_mux_device_driver = {
    .probe = i2c_device_probe,
    .remove = __exit_p(i2c_deivce_remove),
    .driver = {
        .owner = THIS_MODULE,
        .name = "delta-ag7648v2-i2c-sfp-main-mux-device",
    }
};

static int __init delta_ag7648v2_platform_init(void)
{
    struct i2c_adapter *adapter;
    //struct cpld_platform_data *cpld_pdata;
    int ret = 0;
    int cnt = 0;

    printk("ag7648v2_platform module initialization\n");

    adapter = i2c_get_adapter(BUS1);
    i2c_client_9548_main = i2c_new_device(adapter, &i2c_info_pca9548_main[0]);

    i2c_put_adapter(adapter);

    /* register the i2c device driver */
    ret = platform_driver_register(&i2c_device_driver);
    if (ret) {
        printk(KERN_WARNING "Fail to register i2c device driver\n");
        goto error_i2c_device_driver;
    }

    adapter = i2c_get_adapter(BUS2);
    i2c_client_9548_fan = i2c_new_device(adapter, &i2c_info_pca9548_fan[0]);

    i2c_put_adapter(adapter);

    /* register the i2c fan device driver */
    ret = platform_driver_register(&i2c_fan_device_driver);
    if (ret) {
        printk(KERN_WARNING "Fail to register i2c fan device driver\n");
        goto error_i2c_fan_device_driver;
    }

    adapter = i2c_get_adapter(BUS5);
    i2c_client_9548_sfp_main_mux = i2c_new_device(adapter, &i2c_info_pca9548_sfp_main_mux[0]);

    i2c_put_adapter(adapter);

    /* register the i2c sfp main mux device driver */
    ret = platform_driver_register(&i2c_sfp_main_mux_device_driver);
    if (ret) {
        printk(KERN_WARNING "Fail to register i2c sfp main mux device driver\n");
        goto error_i2c_sfp_main_mux_device_driver;
    }
    /* register the i2c devices */
    for (cnt = 0; cnt < ARRAY_SIZE(ag7648v2_i2c_device); cnt++)
    {
        ret = platform_device_register(&ag7648v2_i2c_device[cnt]);
        if (ret) {
            printk(KERN_WARNING "Fail to create i2c device %d\n", cnt);
            goto error_ag7648v2_i2c_device;
        }
    }

    return 0;

error_ag7648v2_i2c_device:
    for (; cnt >= 0; cnt--) {
        platform_device_unregister(&ag7648v2_i2c_device[cnt]);
    }
    platform_driver_unregister(&i2c_sfp_main_mux_device_driver);
error_i2c_sfp_main_mux_device_driver:
    platform_driver_unregister(&i2c_fan_device_driver);
error_i2c_fan_device_driver:
    platform_driver_unregister(&i2c_device_driver);
error_i2c_device_driver:
    return ret;
}

static void __exit delta_ag7648v2_platform_exit(void)
{
    int i = 0;

    for ( i = 0; i < ARRAY_SIZE(ag7648v2_i2c_device); i++ ) {
        platform_device_unregister(&ag7648v2_i2c_device[i]);
    }

    platform_driver_unregister(&i2c_device_driver);
    i2c_unregister_device(i2c_client_9548_fan);
    i2c_unregister_device(i2c_client_9548_main);
    i2c_unregister_device(i2c_client_9548_sfp_main_mux);
}


module_init(delta_ag7648v2_platform_init);
module_exit(delta_ag7648v2_platform_exit);

MODULE_DESCRIPTION("DNI AG7648V2 Platform Support");
MODULE_AUTHOR("Mike Chen <mike.hc.chen@deltaww.com>");
MODULE_LICENSE("GPL");
