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
#include <linux/hwmon.h>
#include <linux/hwmon-sysfs.h>
#include <linux/platform_data/pca954x.h>
#include <linux/platform_data/i2c-mux-gpio.h>

#define agv848v1_i2c_device1_num(c){                                         \
        .name                   = "delta-agv848v1-i2c-pca9548-1",                \
        .id                     = c,                                        \
        .dev                    = {                                           \
                    .platform_data = &agv848v1_i2c_device_pca9548_1_data[c], \
                    .release       = device_release,                          \
        },                                                                    \
}

#define agv848v1_i2c_device2_num(c){                                         \
        .name                   = "delta-agv848v1-i2c-pca9548-2",                \
        .id                     = c,                                        \
        .dev                    = {                                           \
                    .platform_data = &agv848v1_i2c_device_pca9548_2_data[c], \
                    .release       = device_release,                          \
        },                                                                    \
}

#define agv848v1_i2c_device3_num(c){                                         \
        .name                   = "delta-agv848v1-i2c-pca9548-3",                \
        .id                     = c,                                        \
        .dev                    = {                                           \
                    .platform_data = &agv848v1_i2c_device_pca9548_3_data[c], \
                    .release       = device_release,                          \
        },                                                                    \
}

#define agv848v1_i2c_device4_num(c){                                         \
        .name                   = "delta-agv848v1-i2c-pca9548-4",                \
        .id                     = c,                                        \
        .dev                    = {                                           \
                    .platform_data = &agv848v1_i2c_device_pca9548_4_data[c], \
                    .release       = device_release,                          \
        },                                                                    \
}

#define agv848v1_i2c_device5_num(c){                                         \
        .name                   = "delta-agv848v1-i2c-pca9548-5",                \
        .id                     = c,                                        \
        .dev                    = {                                           \
                    .platform_data = &agv848v1_i2c_device_pca9548_5_data[c], \
                    .release       = device_release,                          \
        },                                                                    \
}

#define agv848v1_i2c_device6_num(c){                                         \
        .name                   = "delta-agv848v1-i2c-pca9548-6",                \
        .id                     = c,                                        \
        .dev                    = {                                           \
                    .platform_data = &agv848v1_i2c_device_pca9548_6_data[c], \
                    .release       = device_release,                          \
        },                                                                    \
}

#define agv848v1_i2c_device7_num(c){                                         \
        .name                   = "delta-agv848v1-i2c-pca9548-7",                \
        .id                     = c,                                        \
        .dev                    = {                                           \
                    .platform_data = &agv848v1_i2c_device_pca9548_7_data[c], \
                    .release       = device_release,                          \
        },                                                                    \
}

#define I2C_BUS_BASE      51
#define PCA9548_MUX_CNT      8
/* Define struct to get client of i2c_new_deivce at 0x72 */
struct i2c_client * i2c_client_9548[7];

struct i2c_device_platform_data {
    int parent;
    struct i2c_board_info           info;
    struct i2c_client              *client;
};

/* pca9548-1 - SFP 1-8, add 8 bus */
static struct pca954x_platform_mode pca954x_mode1[] = {
  { .adap_id = 81,
    .deselect_on_exit = 1,
  },
  { .adap_id = 82,
    .deselect_on_exit = 1,
  },
  { .adap_id = 83,
    .deselect_on_exit = 1,
  },
  { .adap_id = 84,
    .deselect_on_exit = 1,
  },
  { .adap_id = 85,
    .deselect_on_exit = 1,
  },
  { .adap_id = 86,
    .deselect_on_exit = 1,
  },
  { .adap_id = 87,
    .deselect_on_exit = 1,
  },
  { .adap_id = 88,
    .deselect_on_exit = 1,
  },
};

/* pca9548-2 - SFP 9-16, add 8 bus */
static struct pca954x_platform_mode pca954x_mode2[] = {
  { .adap_id = 89,
    .deselect_on_exit = 1,
  },
  { .adap_id = 90,
    .deselect_on_exit = 1,
  },
  { .adap_id = 91,
    .deselect_on_exit = 1,
  },
  { .adap_id = 92,
    .deselect_on_exit = 1,
  },
  { .adap_id = 93,
    .deselect_on_exit = 1,
  },
  { .adap_id = 94,
    .deselect_on_exit = 1,
  },
  { .adap_id = 95,
    .deselect_on_exit = 1,
  },
  { .adap_id = 96,
    .deselect_on_exit = 1,
  },
};

/* pca9548-3 - SFP 17-24, add 8 bus */
static struct pca954x_platform_mode pca954x_mode3[] = {
  { .adap_id = 97,
    .deselect_on_exit = 1,
  },
  { .adap_id = 98,
    .deselect_on_exit = 1,
  },
  { .adap_id = 99,
    .deselect_on_exit = 1,
  },
  { .adap_id = 100,
    .deselect_on_exit = 1,
  },
  { .adap_id = 101,
    .deselect_on_exit = 1,
  },
  { .adap_id = 102,
    .deselect_on_exit = 1,
  },
  { .adap_id = 103,
    .deselect_on_exit = 1,
  },
  { .adap_id = 104,
    .deselect_on_exit = 1,
  },
};

/* pca9548-4 - SFP 25-32, add 8 bus */
static struct pca954x_platform_mode pca954x_mode4[] = {
  { .adap_id = 105,
    .deselect_on_exit = 1,
  },
  { .adap_id = 106,
    .deselect_on_exit = 1,
  },
  { .adap_id = 107,
    .deselect_on_exit = 1,
  },
  { .adap_id = 108,
    .deselect_on_exit = 1,
  },
  { .adap_id = 109,
    .deselect_on_exit = 1,
  },
  { .adap_id = 110,
    .deselect_on_exit = 1,
  },
  { .adap_id = 111,
    .deselect_on_exit = 1,
  },
  { .adap_id = 112,
    .deselect_on_exit = 1,
  },
};

/* pca9548-5 - SFP 33-40, add 8 bus */
static struct pca954x_platform_mode pca954x_mode5[] = {
  { .adap_id = 113,
    .deselect_on_exit = 1,
  },
  { .adap_id = 114,
    .deselect_on_exit = 1,
  },
  { .adap_id = 115,
    .deselect_on_exit = 1,
  },
  { .adap_id = 116,
    .deselect_on_exit = 1,
  },
  { .adap_id = 117,
    .deselect_on_exit = 1,
  },
  { .adap_id = 118,
    .deselect_on_exit = 1,
  },
  { .adap_id = 119,
    .deselect_on_exit = 1,
  },
  { .adap_id = 120,
    .deselect_on_exit = 1,
  },
};

/* pca9548-6 - SFP 41-48, add 8 bus */
static struct pca954x_platform_mode pca954x_mode6[] = {
  { .adap_id = 121,
    .deselect_on_exit = 1,
  },
  { .adap_id = 122,
    .deselect_on_exit = 1,
  },
  { .adap_id = 123,
    .deselect_on_exit = 1,
  },
  { .adap_id = 124,
    .deselect_on_exit = 1,
  },
  { .adap_id = 125,
    .deselect_on_exit = 1,
  },
  { .adap_id = 126,
    .deselect_on_exit = 1,
  },
  { .adap_id = 127,
    .deselect_on_exit = 1,
  },
  { .adap_id = 128,
    .deselect_on_exit = 1,
  },
};

/* pca9548-7 - QSFP 49-56, add 8 bus */
static struct pca954x_platform_mode pca954x_mode7[] = {
  { .adap_id = 129,
    .deselect_on_exit = 1,
  },
  { .adap_id = 130,
    .deselect_on_exit = 1,
  },
  { .adap_id = 131,
    .deselect_on_exit = 1,
  },
  { .adap_id = 132,
    .deselect_on_exit = 1,
  },
  { .adap_id = 133,
    .deselect_on_exit = 1,
  },
  { .adap_id = 134,
    .deselect_on_exit = 1,
  },
  { .adap_id = 135,
    .deselect_on_exit = 1,
  },
  { .adap_id = 136,
    .deselect_on_exit = 1,
  },
};

static struct pca954x_platform_data pca954x_data[] = {
    {
        .modes = pca954x_mode1,
        .num_modes = ARRAY_SIZE(pca954x_mode1),
    },
    {
        .modes = pca954x_mode2,
        .num_modes = ARRAY_SIZE(pca954x_mode2),
    },
    {
        .modes = pca954x_mode3,
        .num_modes = ARRAY_SIZE(pca954x_mode3),
    },
    {
        .modes = pca954x_mode4,
        .num_modes = ARRAY_SIZE(pca954x_mode4),
    },
    {
        .modes = pca954x_mode5,
        .num_modes = ARRAY_SIZE(pca954x_mode5),
    },
    {
        .modes = pca954x_mode6,
        .num_modes = ARRAY_SIZE(pca954x_mode6),
    },
    {
        .modes = pca954x_mode7,
        .num_modes = ARRAY_SIZE(pca954x_mode7),
    },
};

static struct i2c_board_info __initdata i2c_info_pca9548[] = {
    {
        I2C_BOARD_INFO("pca9548", 0x72),
        .platform_data = &pca954x_data[0],
    },
    {
        I2C_BOARD_INFO("pca9548", 0x72),
        .platform_data = &pca954x_data[1],
    },
    {
        I2C_BOARD_INFO("pca9548", 0x72),
        .platform_data = &pca954x_data[2],
    },
    {
        I2C_BOARD_INFO("pca9548", 0x72),
        .platform_data = &pca954x_data[3],
    },
    {
        I2C_BOARD_INFO("pca9548", 0x72),
        .platform_data = &pca954x_data[4],
    },
    {
        I2C_BOARD_INFO("pca9548", 0x72),
        .platform_data = &pca954x_data[5],
    },
    {
        I2C_BOARD_INFO("pca9548", 0x72),
        .platform_data = &pca954x_data[6],
    },
};

static struct i2c_device_platform_data agv848v1_i2c_device_pca9548_1_data[] = {
    {
        // sfp 1 (0x50)
        .parent = 81,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 2 (0x50)
        .parent = 82,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 3 (0x50)
        .parent = 83,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 4 (0x50)
        .parent = 84,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 5 (0x50)
        .parent = 85,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 6 (0x50)
        .parent = 86,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 7 (0x50)
        .parent = 87,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 8 (0x50)
        .parent = 88,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
};

static struct i2c_device_platform_data agv848v1_i2c_device_pca9548_2_data[] = {
    {
        // sfp 9 (0x50)
        .parent = 89,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 10 (0x50)
        .parent = 90,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 11 (0x50)
        .parent = 91,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 12 (0x50)
        .parent = 92,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 13 (0x50)
        .parent = 93,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 14 (0x50)
        .parent = 94,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 15 (0x50)
        .parent = 95,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 16 (0x50)
        .parent = 96,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
};

static struct i2c_device_platform_data agv848v1_i2c_device_pca9548_3_data[] = {
    {
        // sfp 17 (0x50)
        .parent = 97,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 18 (0x50)
        .parent = 98,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 19 (0x50)
        .parent = 99,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 20 (0x50)
        .parent = 100,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 21 (0x50)
        .parent = 101,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 22 (0x50)
        .parent = 102,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 23 (0x50)
        .parent = 103,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 24 (0x50)
        .parent = 104,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
};

static struct i2c_device_platform_data agv848v1_i2c_device_pca9548_4_data[] = {
    {
        // sfp 25 (0x50)
        .parent = 105,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 26 (0x50)
        .parent = 106,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 27 (0x50)
        .parent = 107,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 28 (0x50)
        .parent = 108,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 29 (0x50)
        .parent = 109,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 30 (0x50)
        .parent = 110,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 31 (0x50)
        .parent = 111,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 32 (0x50)
        .parent = 112,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
};

static struct i2c_device_platform_data agv848v1_i2c_device_pca9548_5_data[] = {
    {
        // sfp 33 (0x50)
        .parent = 113,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 34 (0x50)
        .parent = 114,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 35 (0x50)
        .parent = 115,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 36 (0x50)
        .parent = 116,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 37 (0x50)
        .parent = 117,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 38 (0x50)
        .parent = 118,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 39 (0x50)
        .parent = 119,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 40 (0x50)
        .parent = 120,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
};

static struct i2c_device_platform_data agv848v1_i2c_device_pca9548_6_data[] = {
    {
        // sfp 41 (0x50)
        .parent = 121,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 42 (0x50)
        .parent = 122,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 43 (0x50)
        .parent = 123,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 44 (0x50)
        .parent = 124,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 45 (0x50)
        .parent = 125,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 46 (0x50)
        .parent = 126,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 47 (0x50)
        .parent = 127,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
    {
        // sfp 48 (0x50)
        .parent = 128,
        .info = { .type = "optoe2", .addr = 0x50 },
        .client = NULL,
    },
};

static struct i2c_device_platform_data agv848v1_i2c_device_pca9548_7_data[] = {
    {
        // qsfp 49 (0x50)
        .parent = 129,
        .info = { .type = "optoe1", .addr = 0x50 },
        .client = NULL,
    },
    {
        // qsfp 50 (0x50)
        .parent = 130,
        .info = { .type = "optoe1", .addr = 0x50 },
        .client = NULL,
    },
    {
        // qsfp 51 (0x50)
        .parent = 131,
        .info = { .type = "optoe1", .addr = 0x50 },
        .client = NULL,
    },
    {
        // qsfp 52 (0x50)
        .parent = 132,
        .info = { .type = "optoe1", .addr = 0x50 },
        .client = NULL,
    },
    {
        // qsfp 53 (0x50)
        .parent = 133,
        .info = { .type = "optoe1", .addr = 0x50 },
        .client = NULL,
    },
    {
        // qsfp 54 (0x50)
        .parent = 134,
        .info = { .type = "optoe1", .addr = 0x50 },
        .client = NULL,
    },
    {
        // qsfp 55 (0x50)
        .parent = 135,
        .info = { .type = "optoe1", .addr = 0x50 },
        .client = NULL,
    },
    {
        // qsfp 56 (0x50)
        .parent = 136,
        .info = { .type = "optoe1", .addr = 0x50 },
        .client = NULL,
    },
};

static void device_release(struct device *dev)
{
    return;
}

static struct platform_device agv848v1_i2c_device[] = {
    agv848v1_i2c_device1_num(0),//SFP 1-8
    agv848v1_i2c_device1_num(1),
    agv848v1_i2c_device1_num(2),
    agv848v1_i2c_device1_num(3),
    agv848v1_i2c_device1_num(4),
    agv848v1_i2c_device1_num(5),
    agv848v1_i2c_device1_num(6),
    agv848v1_i2c_device1_num(7),
    agv848v1_i2c_device2_num(0),//SFP 9-23
    agv848v1_i2c_device2_num(1),
    agv848v1_i2c_device2_num(2),
    agv848v1_i2c_device2_num(3),
    agv848v1_i2c_device2_num(4),
    agv848v1_i2c_device2_num(5),
    agv848v1_i2c_device2_num(6),
    agv848v1_i2c_device2_num(7),
    agv848v1_i2c_device3_num(0),//SFP 17-24
    agv848v1_i2c_device3_num(1),
    agv848v1_i2c_device3_num(2),
    agv848v1_i2c_device3_num(3),
    agv848v1_i2c_device3_num(4),
    agv848v1_i2c_device3_num(5),
    agv848v1_i2c_device3_num(6),
    agv848v1_i2c_device3_num(7),
    agv848v1_i2c_device4_num(0),//SFP 25-32
    agv848v1_i2c_device4_num(1),
    agv848v1_i2c_device4_num(2),
    agv848v1_i2c_device4_num(3),
    agv848v1_i2c_device4_num(4),
    agv848v1_i2c_device4_num(5),
    agv848v1_i2c_device4_num(6),
    agv848v1_i2c_device4_num(7),
    agv848v1_i2c_device5_num(0),//SFP 33-47
    agv848v1_i2c_device5_num(1),
    agv848v1_i2c_device5_num(2),
    agv848v1_i2c_device5_num(3),
    agv848v1_i2c_device5_num(4),
    agv848v1_i2c_device5_num(5),
    agv848v1_i2c_device5_num(6),
    agv848v1_i2c_device5_num(7),
    agv848v1_i2c_device6_num(0),//SFP 41-48
    agv848v1_i2c_device6_num(1),
    agv848v1_i2c_device6_num(2),
    agv848v1_i2c_device6_num(3),
    agv848v1_i2c_device6_num(4),
    agv848v1_i2c_device6_num(5),
    agv848v1_i2c_device6_num(6),
    agv848v1_i2c_device6_num(7),
    agv848v1_i2c_device7_num(0),//QSFP 49-56
    agv848v1_i2c_device7_num(1),
    agv848v1_i2c_device7_num(2),
    agv848v1_i2c_device7_num(3),
    agv848v1_i2c_device7_num(4),
    agv848v1_i2c_device7_num(5),
    agv848v1_i2c_device7_num(6),
    agv848v1_i2c_device7_num(7),
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

static struct platform_driver i2c_device_pca9548_driver[] = {
    {
        .probe = i2c_device_probe,
        .remove = __exit_p(i2c_deivce_remove),
        .driver = {
            .owner = THIS_MODULE,
            .name = "delta-agv848v1-i2c-pca9548-1",
        }
    },
    {
        .probe = i2c_device_probe,
        .remove = __exit_p(i2c_deivce_remove),
        .driver = {
            .owner = THIS_MODULE,
            .name = "delta-agv848v1-i2c-pca9548-2",
        }
    },
    {
        .probe = i2c_device_probe,
        .remove = __exit_p(i2c_deivce_remove),
        .driver = {
            .owner = THIS_MODULE,
            .name = "delta-agv848v1-i2c-pca9548-3",
        }
    },
    {
        .probe = i2c_device_probe,
        .remove = __exit_p(i2c_deivce_remove),
        .driver = {
            .owner = THIS_MODULE,
            .name = "delta-agv848v1-i2c-pca9548-4",
        }
    },
    {
        .probe = i2c_device_probe,
        .remove = __exit_p(i2c_deivce_remove),
        .driver = {
            .owner = THIS_MODULE,
            .name = "delta-agv848v1-i2c-pca9548-5",
        }
    },
    {
        .probe = i2c_device_probe,
        .remove = __exit_p(i2c_deivce_remove),
        .driver = {
            .owner = THIS_MODULE,
            .name = "delta-agv848v1-i2c-pca9548-6",
        }
    },
    {
        .probe = i2c_device_probe,
        .remove = __exit_p(i2c_deivce_remove),
        .driver = {
            .owner = THIS_MODULE,
            .name = "delta-agv848v1-i2c-pca9548-7",
        }
    },
};

static int __init delta_agv848v1_platform_init(void)
{
    struct i2c_adapter *adapter;
    int ret = 0;
    int device_cnt = 0, driver_cnt = 0, i2c_max_cnt = 0, bus = 0, i = 0;

    printk("delta_agv848v1_sfp module initialization\n");

    for (driver_cnt = 0; driver_cnt < ARRAY_SIZE(i2c_client_9548); driver_cnt++) {

        /* register the i2c driver */
        bus = I2C_BUS_BASE + driver_cnt;
        adapter = i2c_get_adapter(bus);
        i2c_client_9548[driver_cnt] = i2c_new_device(adapter, &i2c_info_pca9548[driver_cnt]);
        i2c_put_adapter(adapter); 
        ret = platform_driver_register(&i2c_device_pca9548_driver[driver_cnt]);
        if (ret) {
            printk(KERN_WARNING "Fail to register i2c device driver\n");
            goto error_agv848v1_i2c;
        }

        /* register the i2c devices */
        if (driver_cnt == (ARRAY_SIZE(i2c_client_9548)-1) ) {
            i2c_max_cnt = ARRAY_SIZE(agv848v1_i2c_device); //Get last pca8548 device number.
        } else {
            i2c_max_cnt = i2c_max_cnt + PCA9548_MUX_CNT; //pca954x 1-6 : 8 devices.
        }

        for (; device_cnt < i2c_max_cnt; device_cnt++) {
            ret = platform_device_register(&agv848v1_i2c_device[device_cnt]);
            if (ret) {
                printk(KERN_WARNING "Fail to create i2c device %d\n", device_cnt);
                goto error_agv848v1_i2c;
            }
        }
    }
    return 0;

error_agv848v1_i2c:
    i = device_cnt;
    for ( i = 0; i >= 0; i--) {
        platform_device_unregister(&agv848v1_i2c_device[device_cnt]);
    }
    i = driver_cnt;
    for (i = 0; i >= 0; i--) {
        platform_driver_unregister(&i2c_device_pca9548_driver[driver_cnt]);
    }
    return ret;
}

static void __exit delta_agv848v1_platform_exit(void)
{
    int i = 0;

    for ( i = 0; i < ARRAY_SIZE(agv848v1_i2c_device); i++ ) {
        platform_device_unregister(&agv848v1_i2c_device[i]);
    }

    for ( i = 0; i < ARRAY_SIZE(i2c_device_pca9548_driver); i++ ) {
        platform_driver_unregister(&i2c_device_pca9548_driver[i]);
    }

    for ( i = 0; i < ARRAY_SIZE(i2c_client_9548); i++ ) {
        i2c_unregister_device(i2c_client_9548[i]);
    }
}


module_init(delta_agv848v1_platform_init);
module_exit(delta_agv848v1_platform_exit);

MODULE_DESCRIPTION("Delta AGV848V1 SFP-DD eeprom Support");
MODULE_AUTHOR("Jean Yi Chen <jean.yi.chen@deltaww.com>");
MODULE_LICENSE("GPL");
