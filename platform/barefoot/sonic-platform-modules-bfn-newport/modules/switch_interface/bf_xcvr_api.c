/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * device attribute handler implementation for bf xcvr driver
 */

#define pr_fmt(fmt) "%s:%s: " fmt, KBUILD_MODNAME,  __func__

#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/hwmon-sysfs.h>
#include <linux/bitops.h>
#include "bf_module_util.h"
#include "bf_xcvr_driver.h"
#include "bf_fpga_i2c_util.h"

#define EEPROM_ADDR 0x50
#define BUS_NO 32

enum pcal9535_regs_enum {
  PCAL9535_INPUT_PORT_REG_0 = 0,
  PCAL9535_OUTPUT_PORT_REG_0 = 2
};

enum attr_pio_enum {
    PIO_LPMODE = 0,
    PIO_PRESENT,
    PIO_INTR,
    PIO_RESET,
    MAX_PIO_ATTR
};

struct pio_info {
    uint8_t mux_chn[2];
    uint8_t i2c_addr[2];
};

extern struct bf_xcvr_drv_data *g_data;

static const struct pio_info pio_infos[] = {
    {{ 0x1,  0x2}, {0x20, 0x21}},
    {{ 0x4,  0x8}, {0x22, 0x23}},
    {{0x10, 0x20}, {0x24, 0x25}},
    {{0x40, 0x80}, {0x26, 0x27}}
};

static const long id_to_bitidx[] = {
     0,  1,  2,  3,  4,  5,  6,  7,  9,  8, 11, 10, 13, 12, 15, 14,
    17, 16, 19, 18, 21, 20, 23, 22, 24, 25, 26, 27, 29, 28, 31, 30
};

ATTR_SHOW_STR_FUNC(debug, //SEAN TODO
    "+++DUMMY content+++\n"
    "xcvr present:\n"
    "  0-->present\n"
    "  1-->unpresent\n"
    "  bit0-->xcvr1, bit4-->xcvr2\n"
    "  eg:\n"
    "  1.show present info: i2cget -f -y 2 0x1d 0x34\n"
    "\n"
    "xcvr data:\n"
    "                    path\n"
    "  xcvr1             81-0058\n"
    "  xcvr2             82-0058\n"
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
    "xcvr vendor, model, serial, version:\n"
    "  xcvr1-->$bus = 81, $addr = 0x50\n"
    "  xcvr2-->$bus = 82, $addr = 0x50\n"
    "  eg:\n"
    "  1.show all info: i2cdump -f -y $bus $addr\n"
    "---DUMMY content---\n"
)

ATTR_SHOW_NUM_FUNC(devnum, NUM_DEV)

static int read_pio(uint32_t attr, uint32_t *_val)
{
    uint8_t *val = (uint8_t*) _val;
    uint8_t mux_chn, i2c_addr;
    uint8_t reg_addr = PCAL9535_INPUT_PORT_REG_0;
    int i, status;

    if(attr > MAX_PIO_ATTR)
        return -EINVAL;

    for(i = 0 ; i < 2 ; i++)
    {
        mux_chn = pio_infos[attr].mux_chn[i];
        i2c_addr = pio_infos[attr].i2c_addr[i];
        status = bf_fpga_i2c_addr_read(BUS_NO, WITH_MUX, mux_chn, i2c_addr,
                                       &reg_addr, sizeof(reg_addr), val, 2);
        if(status != 0)
        {
            bf_print("read pio fail, mux_chn(0x%x), addr(0x%x), st(%s)\n",
                     mux_chn, i2c_addr, bf_pltfm_err_str(status));
            return -EIO;
        }
        val += 2;
    }
    return 0;
}

static struct bf_xcvr_drv_data *update_all_xcvr_data(void){
    int i, status;
    uint32_t attrs[] = {PIO_LPMODE, PIO_PRESENT, PIO_INTR, PIO_RESET};
    uint32_t *vals[] = {&g_data->lpmode, &g_data->present, &g_data->interrupt,
                        &g_data->reset};

    if (time_before(jiffies, g_data->last_updated + HZ * 5) && g_data->valid)
        return g_data;

    g_data->valid = 0;

    for(i = 0 ; i < ARRAY_SIZE(attrs); i++) {
        status = read_pio(attrs[i], vals[i]);
        if(status != 0) {
            bf_print("read attr(%d) from PIO fail!\n", attrs[i]);
            goto exit;
        }
    }

    g_data->last_updated = jiffies;
    g_data->valid = 1;
exit:
    return g_data;
}

static int write_pio_bit(uint32_t attr, long bit_idx, bool is_set)
{
    uint32_t *vals[] = {&g_data->lpmode, &g_data->present, &g_data->interrupt,
                        &g_data->reset};
    uint8_t *val;
    uint8_t mux_chn, i2c_addr;
    uint8_t reg_addr = PCAL9535_OUTPUT_PORT_REG_0;
    int i, status = 0;

    if(attr > MAX_PIO_ATTR)
        return -EINVAL;

    g_data = update_all_xcvr_data();
    if (!g_data->valid) {
        return -EIO;
    }

    /* Update the bit only if it is differ from intended is_set. */
    val = (uint8_t*) vals[attr];
    if(is_set == test_bit(bit_idx, (unsigned long*)val))
        return 0;

    assign_bit(bit_idx, (unsigned long*)val, is_set);
    for(i = 0 ; i < 2 ; i++)
    {
        mux_chn = pio_infos[attr].mux_chn[i];
        i2c_addr = pio_infos[attr].i2c_addr[i];
        status = bf_fpga_i2c_addr_write(BUS_NO, WITH_MUX, mux_chn, i2c_addr,
                                       &reg_addr, sizeof(reg_addr), val, 2);
        if(status != 0)
        {
            bf_print("write pio fail, mux_chn(0x%x), addr(0x%x), st(%s)\n",
                     mux_chn, i2c_addr, bf_pltfm_err_str(status));
            return -EIO;
        }
        val += 2;
    }
    return 0;
}

ssize_t root_show(struct device *dev, struct device_attribute *da,
                            char *buf)
{
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
    int i, error = 0;
    uint32_t value = 0;
    bool bit_val;
    bf_print("attr_name(%s) attr_idx=%d\n", da->attr.name, attr->index);

    mutex_lock(&g_data->update_lock);
    g_data = update_all_xcvr_data();
    if (!g_data->valid) {
        error = -EIO;
        goto exit;
    }

    switch (attr->index) {
    case POWERON_ATTR_ID:
        value = g_data->power_on;
        break;
    case PRESENT_ATTR_ID:
        value = 0;
        for(i = 0 ; i < ARRAY_SIZE(id_to_bitidx) ; i++){
            bit_val = test_bit(id_to_bitidx[i],
                               (unsigned long*)&g_data->present);
            assign_bit(i, (unsigned long*)&value, !bit_val);
        }
        break;
    default:
        error = -EINVAL;
        goto exit;
    }
    mutex_unlock(&g_data->update_lock);
    return sprintf(buf, "0x%08X\n", value);
exit:
    mutex_unlock(&g_data->update_lock);
    return error;
}

ssize_t xcvr_show(struct device *dev, struct device_attribute *da,
                            char *buf)
{
    struct platform_device *pdev = to_platform_device(dev);
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
    int error = 0;
    bool val;
    long bit_idx = id_to_bitidx[pdev->id];

    mutex_lock(&g_data->update_lock);
    g_data = update_all_xcvr_data();
    if (!g_data->valid) {
        error = -EIO;
        goto exit;
    }

    switch (attr->index) {
    case ETH_POWERON_ATTR_ID:
        val = test_bit(pdev->id, (unsigned long*)&g_data->power_on);
        break;
    case ETH_RESET_ATTR_ID:
        val = !test_bit(bit_idx, (unsigned long*)&g_data->reset);
        break;
    case ETH_LPMODE_ATTR_ID:
        val = test_bit(bit_idx, (unsigned long*)&g_data->lpmode);
        break;
    case ETH_PRESENT_ATTR_ID:
        val = !test_bit(bit_idx, (unsigned long*)&g_data->present);
        break;
    case ETH_INTR_ATTR_ID:
        val = !test_bit(bit_idx, (unsigned long*)&g_data->interrupt);
        break;
    default:
        error = -EINVAL;
        goto exit;
    }
    mutex_unlock(&g_data->update_lock);
    return sprintf(buf, "%d\n", ((val)? 1 : 0));

exit:
    mutex_unlock(&g_data->update_lock);
    return error;
}
ssize_t xcvr_store(struct device *dev, struct device_attribute *da,
                            const char *buf, size_t count)
{
    struct platform_device *pdev = to_platform_device(dev);
    struct sensor_device_attribute *attr = to_sensor_dev_attr(da);
    long val_int = 0;
    bool val;
    int error;
    long bit_idx = id_to_bitidx[pdev->id];

    error = kstrtol(buf, 10, &val_int);
    if(error)
        return error;
    val = (val_int == 0)? false : true;

    mutex_lock(&g_data->update_lock);

    switch (attr->index) {
    case ETH_POWERON_ATTR_ID:
        assign_bit(pdev->id, (unsigned long*)&g_data->power_on, val);
        break;
    case ETH_RESET_ATTR_ID:
        error = write_pio_bit(PIO_RESET, bit_idx, !val);
        if(error != 0)
            goto exit;
        break;
    case ETH_LPMODE_ATTR_ID:
        error = write_pio_bit(PIO_LPMODE, bit_idx, val);
        if(error != 0)
            goto exit;
        break;
    default:
        error = -EINVAL;
        goto exit;
    }

    mutex_unlock(&g_data->update_lock);
    return count;
exit:
    mutex_unlock(&g_data->update_lock);
    return error;
}
