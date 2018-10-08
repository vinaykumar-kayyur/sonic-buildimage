/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements. See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership. The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License. You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied. See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

#ifndef __BMS_FAN_SERVD_H__
#define __BMS_FAN_SERVD_H__

#include "bms_irq_sysd.h"

#define FAN_FILE_PATH_LEN 64

typedef struct {
    int number;
    char *hwmon_path;
    char intr_src[FAN_FILE_PATH_LEN];
    char intr_msk[FAN_FILE_PATH_LEN];
    char *tray_led;
    char *type;
    char *present;
    char pwm[FAN_FILE_PATH_LEN];
    char pwm_enable[FAN_FILE_PATH_LEN];
    char input[FAN_FILE_PATH_LEN];
    char *smart_fan_path;
}bms_fan_serv_data_t;

enum {
    BMS_AC_PSU_NORMAL_FAN = 0,
    BMS_AC_PSU_REVERSE_FAN,
    BMS_DC_PSU_NORMAL_FAN,
    BMS_DC_PSU_REVERSE_FAN,
};

enum {
    BMS_FAN_MODULE_STATUS_NONINIT = 0,
    BMS_FAN_MODULE_STATUS_NONREADY,
    BMS_FAN_MODULE_STATUS_NORMAL,
    BMS_FAN_MODULE_STATUS_NONPRESENT,
    BMS_FAN_MODULE_STATUS_FAILED,
};

enum {
    BMS_FAN_MODULE_TYPE_REVERSE = 0,
    BMS_FAN_MODULE_TYPE_NORMAL,
};

enum {
    BMS_FAN_INTR_UNMASKED = 0,
    BMS_FAN_INTR_MASKED,
};

enum {
    BMS_FAN_INTR_NORMAL = 0,
    BMS_FAN_INTR_FAULT,
};

enum {
    BMS_FAN_GLOBAL_INTR_MASKED = 0,
    BMS_FAN_GLOBAL_INTR_UNMASKED,
};

enum {
    BMS_FAN_MODULE_LED_OFF = 0,
    BMS_FAN_MODULE_LED_GREEN,
    BMS_FAN_MODULE_LED_AMBER,
};

enum {
    BMS_FAN_PANEL_LED_OFF = 0,
    BMS_FAN_PANEL_LED_AMBER,
    BMS_FAN_PANEL_LED_GREEN,
};

enum {
    BMS_FAN_PWM_ENABLE_OFF = 0,
    BMS_FAN_PWM_ENABLE_PWM,
    BMS_FAN_PWM_ENABLE_RPM
};

enum {
    BMS_FAN_PWM_DUTY_CYCLE_NORMAL = 254,
    BMS_FAN_PWM_DUTY_CYCLE_MAX = 255,
};


extern bms_sys_serv_data_t bms_sys_serv_data[];
extern int bms_sys_serv_data_num;

extern int bms_fan_init_done;
extern void bms_fan_serv_fan_debug_cache_print(char * test);
extern bms_fan_serv_data_t bms_fan_serv_data[];
extern unsigned int bms_fan_status[];
extern unsigned int bms_fan_type[];
extern unsigned int bms_board_type;

extern void bms_fan_serv_cache_module_cache_get(unsigned int module_number, unsigned int* module_status, unsigned int* module_type);
extern int bms_fan_serv_fan_present_get(unsigned int *value);
extern int bms_fan_serv_module_type_get(unsigned int module_number, unsigned int *value);
extern void bms_fan_serv_cache_module_cache_retry_get(unsigned int module_number, unsigned int* module_retry);
extern void bms_fan_serv_cache_module_cache_retry_set(unsigned int module_number, unsigned int value);
extern int bms_fan_serv_fan_pwm_set(unsigned int module_number, unsigned int value);
extern int bms_fan_serv_fan_input_get(unsigned int fan_number, unsigned int *value);
extern int bms_fan_serv_fan_intr_get(unsigned int fan_number, unsigned int *value);


#define BMS_SYSFS_FAN_PANEL_LED "/sys/bus/i2c/devices/1-0032/fan_led"
#define BMS_FAN_NUM_PER_MODULE 2
#define BMS_FAN_MODULE_NUM 6
#define BMS_FAN_MIN_FAN_SPEED 480
#define BMS_FAN_NONREADY_RETRY_INIT 0
#define BMS_FAN_NONREADY_RETRY 3
#define BMS_FAN_SERV_DATA_NAME "FAN"
#define BMS_FAN_CONTROL_NUM 2

/* fan message queue range define 100~199 */
#define SERV_TYPE_FAN_MODULE_PRESENT 100
#define SERV_TYPE_FAN_MODULE_NONPRESENT 101

#endif /* __BMS_FAN_SERVD_H__ */
