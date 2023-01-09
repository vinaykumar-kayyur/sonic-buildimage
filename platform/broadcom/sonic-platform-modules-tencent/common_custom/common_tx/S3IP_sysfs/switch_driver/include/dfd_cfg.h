#ifndef __DFD_CFG_H__
#define __DFD_CFG_H__

#include <linux/list.h>

#define DFD_KO_FILE_NAME_DIR       "/etc/dfd_cfg/ko/file_name/"
#define DFD_KO_CFG_FILE_DIR        "/etc/dfd_cfg/ko/cfg_file/"
#define DFD_PUB_CARDTYPE_FILE      "/sys/module/ruijie_common/parameters/dfd_my_type"

#define DFD_CFG_CMDLINE_MAX_LEN (256)
#define DFD_CFG_NAME_MAX_LEN    (256)
#define DFD_CFG_VALUE_MAX_LEN   (256)
#define DFD_CFG_STR_MAX_LEN     (64)
#define DFD_CFG_CPLD_NUM_MAX    (16)
#define DFD_PRODUCT_ID_LENGTH   (8)
#define DFD_PID_BUF_LEN         (32)
#define DFD_TEMP_NAME_BUF_LEN   (32)

#define DFD_CFG_EMPTY_VALUE     (-1)
#define DFD_CFG_INVALID_VALUE   (0)

#define DFD_CFG_KEY(item, index1, index2) \
    ((((item) & 0xff) << 24) | (((index1) & 0xffff) << 8) | ((index2) & 0xff))
#define DFD_CFG_ITEM_ID(key)    (((key) >> 24) & 0xff)
#define DFD_CFG_INDEX1(key)     (((key) >> 8) & 0xffff)
#define DFD_CFG_INDEX2(key)     ((key)& 0xff)

#define INDEX_NOT_EXIST     (-1)
#define INDEX1_MAX           (0xffff)
#define INDEX2_MAX           (0xff)

#define DFD_CFG_ITEM_ALL \
    DFD_CFG_ITEM(DFD_CFG_ITEM_NONE, "none", INDEX_NOT_EXIST, INDEX_NOT_EXIST)                       \
    DFD_CFG_ITEM(DFD_CFG_ITEM_DEV_NUM, "dev_num", INDEX1_MAX, INDEX2_MAX)                 \
    DFD_CFG_ITEM(DFD_CFG_ITEM_FAN_SPEED_TOLERANCE, "fan_speed_tolerance", INDEX1_MAX, INDEX2_MAX)   \
    DFD_CFG_ITEM(DFD_CFG_ITEM_FAN_SPEED_TARGET, "fan_speed_target", INDEX1_MAX, INDEX2_MAX)   \
    DFD_CFG_ITEM(DFD_CFG_ITEM_FAN_SPEED_MAX, "fan_speed_max", INDEX1_MAX, INDEX2_MAX)   \
    DFD_CFG_ITEM(DFD_CFG_ITEM_FAN_SPEED_MIN, "fan_speed_min", INDEX1_MAX, INDEX2_MAX)   \
    DFD_CFG_ITEM(DFD_CFG_ITEM_LED_STATUS_DECODE, "led_status_decode", INDEX1_MAX, INDEX2_MAX)   \
    DFD_CFG_ITEM(DFD_CFG_ITEM_CPLD_LPC_DEV, "cpld_lpc_dev", INDEX1_MAX, DFD_CFG_CPLD_NUM_MAX)       \
    DFD_CFG_ITEM(DFD_CFG_ITEM_FAN_TYPE_NUM, "fan_type_num", INDEX1_MAX, INDEX_NOT_EXIST)       \
    DFD_CFG_ITEM(DFD_CFG_ITEM_EEPROM_SIZE, "eeprom_size", INDEX1_MAX, INDEX2_MAX)       \
    DFD_CFG_ITEM(DFD_CFG_ITEM_DECODE_POWER_FAN_DIR, "decode_power_fan_dir", INDEX1_MAX, INDEX_NOT_EXIST)       \
    DFD_CFG_ITEM(DFD_CFG_ITEM_WATCHDOG_ID, "watchdog_id", INDEX1_MAX, INDEX_NOT_EXIST)       \
    DFD_CFG_ITEM(DFD_CFG_ITEM_POWER_RSUPPLY, "power_rate_supply", INDEX1_MAX, INDEX_NOT_EXIST)           \
    DFD_CFG_ITEM(DFD_CFG_ITEM_PSU_PMBUS_ID, "psu_pmbus_id", INDEX1_MAX, INDEX2_MAX)       \
    DFD_CFG_ITEM(DFD_CFG_ITEM_INT_END, "end_int", INDEX_NOT_EXIST, INDEX_NOT_EXIST)                 \
                                                                                                    \
    DFD_CFG_ITEM(DFD_CFG_ITEM_CPLD_MODE, "mode_cpld", INDEX1_MAX, DFD_CFG_CPLD_NUM_MAX)                 \
    DFD_CFG_ITEM(DFD_CFG_ITEM_CPLD_NAME, "cpld_name", INDEX1_MAX, INDEX2_MAX)              \
    DFD_CFG_ITEM(DFD_CFG_ITEM_CPLD_TYPE, "cpld_type", INDEX1_MAX, INDEX2_MAX)              \
    DFD_CFG_ITEM(DFD_CFG_ITEM_FPGA_NAME, "fpga_name", INDEX1_MAX, INDEX2_MAX)              \
    DFD_CFG_ITEM(DFD_CFG_ITEM_FPGA_TYPE, "fpga_type", INDEX1_MAX, INDEX2_MAX)              \
    DFD_CFG_ITEM(DFD_CFG_ITEM_FPGA_MODEL_DECODE, "fpga_model_decode", INDEX1_MAX, INDEX_NOT_EXIST)   \
    DFD_CFG_ITEM(DFD_CFG_ITEM_FAN_E2_MODE, "fan_e2_mode", INDEX_NOT_EXIST, INDEX_NOT_EXIST)       \
    DFD_CFG_ITEM(DFD_CFG_ITEM_FAN_SYSFS_NAME, "fan_sysfs_name", INDEX_NOT_EXIST, INDEX_NOT_EXIST)       \
    DFD_CFG_ITEM(DFD_CFG_ITEM_POWER_NAME, "power_name", INDEX1_MAX, INDEX2_MAX)       \
    DFD_CFG_ITEM(DFD_CFG_ITEM_FAN_NAME, "fan_name", INDEX1_MAX, INDEX2_MAX)       \
    DFD_CFG_ITEM(DFD_CFG_ITEM_DECODE_POWER_NAME, "decode_power_name", INDEX1_MAX, INDEX_NOT_EXIST)       \
    DFD_CFG_ITEM(DFD_CFG_ITEM_DECODE_FAN_NAME, "decode_fan_name", INDEX1_MAX, INDEX_NOT_EXIST)       \
    DFD_CFG_ITEM(DFD_CFG_ITEM_EEPROM_PATH, "eeprom_path", INDEX1_MAX, INDEX2_MAX)       \
    DFD_CFG_ITEM(DFD_CFG_ITEM_FAN_DIRECTION, "fan_direction", INDEX1_MAX, INDEX2_MAX)   \
    DFD_CFG_ITEM(DFD_CFG_ITEM_WATCHDOG_NAME, "watchdog_name", INDEX1_MAX, INDEX2_MAX)              \
    DFD_CFG_ITEM(DFD_CFG_ITEM_PSU_SYSFS_NAME, "psu_sysfs_name", INDEX_NOT_EXIST, INDEX_NOT_EXIST)       \
    DFD_CFG_ITEM(DFD_CFG_ITEM_SLOT_SYSFS_NAME, "slot_sysfs_name", INDEX_NOT_EXIST, INDEX_NOT_EXIST)       \
    DFD_CFG_ITEM(DFD_CFG_ITEM_STRING_END, "end_string", INDEX_NOT_EXIST, INDEX_NOT_EXIST)           \
                                                                                                    \
    DFD_CFG_ITEM(DFD_CFG_ITEM_CPLD_I2C_DEV, "cpld_i2c_dev", INDEX1_MAX, INDEX2_MAX)           \
    DFD_CFG_ITEM(DFD_CFG_ITEM_OTHER_I2C_DEV, "other_i2c_dev", INDEX1_MAX, INDEX2_MAX)         \
    DFD_CFG_ITEM(DFD_CFG_ITEM_I2C_DEV_END, "end_i2c_dev", INDEX_NOT_EXIST, INDEX_NOT_EXIST)         \
                                                                                                    \
    DFD_CFG_ITEM(DFD_CFG_ITEM_FAN_ROLL_STATUS, "fan_roll_status", INDEX1_MAX, INDEX2_MAX)  \
    DFD_CFG_ITEM(DFD_CFG_ITEM_FAN_SPEED, "fan_speed", INDEX1_MAX, INDEX2_MAX)  \
    DFD_CFG_ITEM(DFD_CFG_ITEM_FAN_RATIO, "fan_ratio", INDEX1_MAX, INDEX_NOT_EXIST)  \
    DFD_CFG_ITEM(DFD_CFG_ITEM_LED_STATUS, "led_status", INDEX1_MAX, INDEX2_MAX)  \
    DFD_CFG_ITEM(DFD_CFG_ITEM_CPLD_VERSION, "cpld_version", INDEX1_MAX, INDEX2_MAX)  \
    DFD_CFG_ITEM(DFD_CFG_ITEM_CPLD_TEST_REG, "cpld_test_reg", INDEX1_MAX, INDEX2_MAX)  \
    DFD_CFG_ITEM(DFD_CFG_ITEM_DEV_PRESENT_STATUS, "dev_present_status", INDEX1_MAX, INDEX2_MAX)  \
    DFD_CFG_ITEM(DFD_CFG_ITEM_PSU_STATUS, "psu_status", INDEX1_MAX, INDEX2_MAX)  \
    DFD_CFG_ITEM(DFD_CFG_ITEM_HWMON_TEMP, "hwmon_temp", INDEX1_MAX, INDEX2_MAX)  \
    DFD_CFG_ITEM(DFD_CFG_ITEM_HWMON_IN, "hwmon_in", INDEX1_MAX, INDEX2_MAX)  \
    DFD_CFG_ITEM(DFD_CFG_ITEM_HWMON_CURR, "hwmon_curr", INDEX1_MAX, INDEX2_MAX)  \
    DFD_CFG_ITEM(DFD_CFG_ITEM_HWMON_PSU, "hwmon_psu", INDEX1_MAX, INDEX2_MAX)  \
    DFD_CFG_ITEM(DFD_CFG_ITEM_SFF_CPLD_REG, "sff_cpld_reg", INDEX1_MAX, INDEX2_MAX)  \
    DFD_CFG_ITEM(DFD_CFG_ITEM_FPGA_VERSION, "fpga_version", INDEX1_MAX, INDEX2_MAX)  \
    DFD_CFG_ITEM(DFD_CFG_ITEM_FPGA_TEST_REG, "fpga_test_reg", INDEX1_MAX, INDEX2_MAX)  \
    DFD_CFG_ITEM(DFD_CFG_ITEM_FPGA_MODEL_REG, "fpga_model_reg", INDEX1_MAX, INDEX2_MAX)  \
    DFD_CFG_ITEM(DFD_CFG_ITEM_INFO_CTRL_END, "end_info_ctrl", INDEX_NOT_EXIST, INDEX_NOT_EXIST)     \

#ifdef DFD_CFG_ITEM
#undef DFD_CFG_ITEM
#endif
#define DFD_CFG_ITEM(_id, _name, _index_min, _index_max)    _id,
typedef enum dfd_cfg_item_id_s {
    DFD_CFG_ITEM_ALL
} dfd_cfg_item_id_t;

#define DFD_CFG_ITEM_IS_INT(item_id) \
    (((item_id) > DFD_CFG_ITEM_NONE) && ((item_id) < DFD_CFG_ITEM_INT_END))

#define DFD_CFG_ITEM_IS_STRING(item_id) \
    (((item_id) > DFD_CFG_ITEM_INT_END) && ((item_id) < DFD_CFG_ITEM_STRING_END))

#define DFD_CFG_ITEM_IS_I2C_DEV(item_id) \
    (((item_id) > DFD_CFG_ITEM_STRING_END) && ((item_id) < DFD_CFG_ITEM_I2C_DEV_END))

#define DFD_CFG_ITEM_IS_INFO_CTRL(item_id) \
    (((item_id) > DFD_CFG_ITEM_I2C_DEV_END) && ((item_id) < DFD_CFG_ITEM_INFO_CTRL_END))

typedef struct index_range_s {
    int index1_max;
    int index2_max;
} index_range_t;

typedef struct val_convert_node_s {
    struct list_head lst;
    int int_val;
    char str_val[DFD_CFG_STR_MAX_LEN];
    int index1;
    int index2;
} val_convert_node_t;

void *dfd_ko_cfg_get_item(int key);

void dfd_ko_cfg_show_item(int key);

int32_t dfd_dev_cfg_init(void);

void dfd_dev_cfg_exit(void);

void dfd_ko_cfg_del_space_lf_cr(char *str);

int dfd_ko_cfg_get_fan_direction_by_name(char *fan_name, int *fan_direction);

int dfd_ko_cfg_get_power_type_by_name(char *power_name, int *power_type);

int dfd_ko_cfg_get_led_status_decode2_by_regval(int regval, int index1, int *value);

#endif /* __DFD_CFG_H__ */
