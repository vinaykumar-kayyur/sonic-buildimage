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

#ifndef __BMS_PSU_SERVD_H__
#define __BMS_PSU_SERVD_H__
#include "bms_irq_sysd.h"

#define PSU_FILE_PATH_LEN 64

enum {
    BMS_PSU_AC_NORMAL_FAN = 0,
    BMS_PSU_AC_REVERSE_FAN,
    BMS_PSU_DC_NORMAL_FAN,
    BMS_PSU_DC_REVERSE_FAN,
};

enum {
    BMS_PSU_STATUS_NORMAL = 0,
    BMS_PSU_STATUS_PRESENT,
    BMS_PSU_STATUS_ABSENT,
    BMS_PSU_STATUS_FAULT,
};

enum {
    BMS_PSU_POWER_LED_OFF = 0,
    BMS_PSU_POWER_LED_AMBER,
    BMS_PSU_POWER_LED_GREEN,
};

enum {
    BMS_PSU_INTR_MASKED = 0,
    BMS_PSU_INTR_UNMASKED,
};

enum {
    BMS_PSU_INTR_ASSERTED = 0,
    BMS_PSU_INTR_DEASSERTED,
};

enum {
    BMS_PSU_SOURCE_INTR_DEASSERTED = 0,
    BMS_PSU_SOURCE_INTR_ASSERTED,
};

enum {
    BMS_PSU_PG_GOOD = 0,
    BMS_PSU_PG_FAILED,
};

enum {
    BMS_PSU_PS_PRESENT = 0,
    BMS_PSU_PS_NONPRESENT,
};

enum {
    BMS_PSU_DRIVER_UNINIT = 0,
    BMS_PSU_DRIVER_INIT_DONE,
};

enum {
    BMS_PSU_VOUT_OV_FAULT = 0,
    BMS_PSU_VOUT_UV_FAULT,
    BMS_PSU_IOUT_OC_FAULT,
    BMS_PSU_IOUT_OC_WARNING,
    BMS_PSU_OT_FAULT,
    BMS_PSU_OT_WARNING,
    BMS_PSU_VIN_UV_WARNING,
    BMS_PSU_VIN_UV_FAULT,
    BMS_PSU_FAN1_FAULT,
    BMS_PSU_FAN1_WARNING,
/*----------------------------------*/
    BMS_PSU_INTR_NUM,
};

typedef struct {
    char* name;
    int pg_offset;
    int ps_offset;
    int address;
    char* pg_ps_reg;
    char model_reg[PSU_FILE_PATH_LEN];
    char* hwmon_path;
    char intr_src[BMS_PSU_INTR_NUM][PSU_FILE_PATH_LEN];
    char* i2c_path;
    char* driver_name;
}bms_psu_serv_data_t;


#define BMS_PSU_NUM 2
#define BMS_SYSFS_POWER_LED "/sys/bus/i2c/devices/1-0032/power_led"

/* PSU message queue range define 200~299 */
#define SERV_TYPE_PSU_PRESENT 200
#define SERV_TYPE_PSU_ABSENT 201
#define SERV_TYPE_PSU_NORMAL 202
#define SERV_TYPE_PSU_INTR_RECOVERY 203

extern bms_sys_serv_data_t bms_sys_serv_data[];
extern int bms_sys_serv_data_num;
extern unsigned int bms_psu_init_done;
extern int bms_psu_serv_power_status_get(unsigned int *value);
extern void bms_psu_serv_cache_get(unsigned int psu_number, unsigned int* psu_status, unsigned int* psu_type);
extern bms_psu_serv_data_t bms_psu_serv_data[];
extern void bms_psu_serv_intr_cache_get(unsigned int* intr_status);

#endif /* __BMS_PSU_SERVD_H__ */
