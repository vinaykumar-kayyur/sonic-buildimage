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

#include <syslog.h>
#include <errno.h>
#include <mqueue.h>
#include <string.h>
#include <pthread.h>
#include <stdlib.h>
#include <stdio.h>

#include "bms_sys_serv_common.h"
#include "bms_fan_servd.h"

bms_fan_serv_data_t bms_fan_serv_data[BMS_FAN_MODULE_NUM * BMS_FAN_NUM_PER_MODULE] = {
    {
        .number = 1,
        .hwmon_path = "/sys/bus/i2c/devices/3-0020/hwmon",
        .intr_src = "fan1_fault",
        .intr_msk = "fan1_fault_mask",
        .tray_led = "/sys/bus/i2c/devices/1-0032/fan_tray1_led",
        .type = "/sys/bus/i2c/devices/1-0032/fan_type1",
        .present = "/sys/bus/i2c/devices/1-0032/fan_tray1_6_present",
        .pwm = "pwm1",
        .pwm_enable = "pwm1_enable",
        .input = "fan1_input",
        .smart_fan_path = "/etc/init.d/fan-ctrld",
    },
    {
        .number = 2,
        .hwmon_path = NULL, /* share same path with FAN number 1 */
        .intr_src = "fan2_fault",
        .intr_msk = "fan2_fault_mask",
        .tray_led = NULL,
        .type = NULL,
        .present = NULL, /* share same byte with FAN1 */
        .pwm = "pwm2",
        .pwm_enable = "pwm2_enable",
        .input = "fan2_input",
        .smart_fan_path = NULL, /* share same path with FAN1 */
    },
    {
        .number = 3,
        .hwmon_path = NULL, /* share same path with FAN number 1 */
        .intr_src = "fan3_fault",
        .intr_msk = "fan3_fault_mask",
        .tray_led = "/sys/bus/i2c/devices/1-0032/fan_tray2_led",
        .type = "/sys/bus/i2c/devices/1-0032/fan_type2",
        .present = NULL, /* share same byte with FAN1 */
        .pwm = "pwm3",
        .pwm_enable = "pwm3_enable",
        .input = "fan3_input",
        .smart_fan_path = NULL, /* share same path with FAN1 */
    },
    {
        .number = 4,
        .hwmon_path = NULL, /* share same path with FAN number 1 */
        .intr_src = "fan4_fault",
        .intr_msk = "fan4_fault_mask",
        .tray_led = NULL,
        .type = NULL,
        .present = NULL, /* share same byte with FAN1 */
        .pwm = "pwm4",
        .pwm_enable = "pwm4_enable",
        .input = "fan4_input",
        .smart_fan_path = NULL, /* share same path with FAN1 */
    },
    {
        .number = 5,
        .hwmon_path = NULL, /* share same path with FAN number 1 */
        .intr_src = "fan5_fault",
        .intr_msk = "fan5_fault_mask",
        .tray_led = "/sys/bus/i2c/devices/1-0032/fan_tray3_led",
        .type = "/sys/bus/i2c/devices/1-0032/fan_type3",
        .present = NULL, /* share same byte with FAN1 */
        .pwm = "pwm5",
        .pwm_enable = "pwm5_enable",
        .input = "fan5_input",
        .smart_fan_path = NULL, /* share same path with FAN1 */
    },
    {
        .number = 6,
        .hwmon_path = NULL, /* share same path with FAN number 1 */
        .intr_src = "fan6_fault",
        .intr_msk = "fan6_fault_mask",
        .tray_led = NULL,
        .type = NULL,
        .present = NULL, /* share same byte with FAN1 */
        .pwm = "pwm6",
        .pwm_enable = "pwm6_enable",
        .input = "fan6_input",
        .smart_fan_path = NULL, /* share same path with FAN1 */
    },
    {
        .number = 7,
        .hwmon_path = "/sys/bus/i2c/devices/3-0023/hwmon",
        .intr_src = "fan1_fault",
        .intr_msk = "fan1_fault_mask",
        .tray_led = "/sys/bus/i2c/devices/1-0032/fan_tray4_led",
        .type = "/sys/bus/i2c/devices/1-0032/fan_type4",
        .present = NULL, /* share same byte with FAN1 */
        .pwm = "pwm1",
        .pwm_enable = "pwm1_enable",
        .input = "fan1_input",
        .smart_fan_path = NULL, /* share same path with FAN1 */
    },
    {
        .number = 8,
        .hwmon_path = NULL, /* share same path with FAN number 7 */
        .intr_src = "fan2_fault",
        .intr_msk = "fan2_fault_mask",
        .tray_led = NULL,
        .type = NULL,
        .present = NULL, /* share same byte with FAN1 */
        .pwm = "pwm2",
        .pwm_enable = "pwm2_enable",
        .input = "fan2_input",
        .smart_fan_path = NULL, /* share same path with FAN1 */
    },
    {
        .number = 9,
        .hwmon_path = NULL, /* share same path with FAN number 7 */
        .intr_src = "fan3_fault",
        .intr_msk = "fan3_fault_mask",
        .tray_led = "/sys/bus/i2c/devices/1-0032/fan_tray5_led",
        .type = "/sys/bus/i2c/devices/1-0032/fan_type5",
        .present = NULL, /* share same byte with FAN1 */
        .pwm = "pwm3",
        .pwm_enable = "pwm3_enable",
        .input = "fan3_input",
        .smart_fan_path = NULL, /* share same path with FAN1 */
    },
    {
        .number = 10,
        .hwmon_path = NULL, /* share same path with FAN number 7 */
        .intr_src = "fan4_fault",
        .intr_msk = "fan4_fault_mask",
        .tray_led = NULL,
        .type = NULL,
        .present = NULL, /* share same byte with FAN1 */
        .pwm = "pwm4",
        .pwm_enable = "pwm4_enable",
        .input = "fan4_input",
        .smart_fan_path = NULL, /* share same path with FAN1 */
    },
    {
        .number = 11,
        .hwmon_path = NULL, /* share same path with FAN number 7 */
        .intr_src = "fan5_fault",
        .intr_msk = "fan5_fault_mask",
        .tray_led = "/sys/bus/i2c/devices/1-0032/fan_tray6_led",
        .type = "/sys/bus/i2c/devices/1-0032/fan_type6",
        .present = NULL, /* share same byte with FAN1 */
        .pwm = "pwm5",
        .pwm_enable = "pwm5_enable",
        .input = "fan5_input",
        .smart_fan_path = NULL, /* share same path with FAN1 */
    },
    {
        .number = 12,
        .hwmon_path = NULL, /* share same path with FAN number 7 */
        .intr_src = "fan6_fault",
        .intr_msk = "fan6_fault_mask",
        .tray_led = NULL,
        .type = NULL,
        .present = NULL, /* share same byte with FAN1 */
        .pwm = "pwm6",
        .pwm_enable = "pwm6_enable",
        .input = "fan6_input",
        .smart_fan_path = NULL, /* share same path with FAN1 */
    },
};

unsigned int bms_fan_status[BMS_FAN_MODULE_NUM];
unsigned int bms_fan_type[BMS_FAN_MODULE_NUM];
unsigned int bms_fan_retry[BMS_FAN_MODULE_NUM];
unsigned int bms_board_type;
int bms_fan_init_done = 0;
pthread_mutex_t bms_fan_cache_lock;


/*
* FEATURE:
*   bms_fan_serv_fan_module_led_set
* PURPOSE:
*   fan service fan module led set to file system
* PARAMETERS:
*   module_number        (IN) module number
*   value                (IN) setting value
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
int
bms_fan_serv_fan_module_led_set(unsigned int module_number,
                                unsigned int value)
{
    return bms_sys_serv_write(bms_fan_serv_data[module_number * BMS_FAN_NUM_PER_MODULE].tray_led, value);
}

/*
* FEATURE:
*   bms_fan_serv_fan_pwm_set
* PURPOSE:
*   fan service fan pwm duty cycle set to file system
* PARAMETERS:
*   module_number        (IN) module number
*   value                (IN) setting value
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
int
bms_fan_serv_fan_pwm_set(unsigned int module_number,
                         unsigned int value)
{
    int i, ret_code = 0;

    for(i = 0; i < BMS_FAN_NUM_PER_MODULE; i++){
        if((ret_code = bms_sys_serv_write(bms_fan_serv_data[(module_number * BMS_FAN_NUM_PER_MODULE) + i].pwm, value)) < 0){
            break;
        }
    }
    return ret_code;
}

/*
* FEATURE:
*   bms_fan_serv_fan_pwm_enable_set
* PURPOSE:
*   fan service fan pwm mode set to file system
* PARAMETERS:
*   module_number        (IN) module number
*   value                (IN) setting value
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
int
bms_fan_serv_fan_pwm_enable_set(unsigned int module_number,
                                unsigned int value)
{
    int i, ret_code = 0;

    for(i = 0; i < BMS_FAN_NUM_PER_MODULE; i++){
        if((ret_code = bms_sys_serv_write(bms_fan_serv_data[(module_number * BMS_FAN_NUM_PER_MODULE) + i].pwm_enable, value)) < 0){
            break;
        }
    }
    return ret_code;
}

/*
* FEATURE:
*   bms_fan_serv_fan_mask_set
* PURPOSE:
*   fan service fan mask set to file system in fan controller
* PARAMETERS:
*   fan_number           (IN) fan number
*   value                (IN) setting value
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
int
bms_fan_serv_fan_mask_set(unsigned int fan_number,
                          unsigned int value)
{
/*
*  within kernel 4.9 max31790 driver, there is no "fan_fault_mask" file nodes
*  so just return 0
*/
#if 1
#define UNUSED(x) (void)(x)
    UNUSED(fan_number);
    UNUSED(value);
    return 0;
#else
    return bms_sys_serv_write(bms_fan_serv_data[fan_number].intr_msk, value);
#endif    
}

/*
* FEATURE:
*   bms_fan_serv_fan_global_mask_set
* PURPOSE:
*   fan service fan global mask set to file system
* PARAMETERS:
*   index                (IN) fan index in bms_sys_serv_data
*   value                (IN) setting value
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
int
bms_fan_serv_fan_global_mask_set(unsigned int index,
                                 unsigned int value)
{
    return bms_sys_serv_write(bms_sys_serv_data[index].intr_msk, value);
}

/*
* FEATURE:
*   bms_fan_serv_fan_panel_led_set
* PURPOSE:
*   fan service fan panel led set to file system in CPLD
* PARAMETERS:
*   value                (IN) setting value
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
int
bms_fan_serv_fan_panel_led_set(unsigned int value)
{
    return bms_sys_serv_write(BMS_SYSFS_FAN_PANEL_LED, value);
}

/*
* FEATURE:
*   bms_fan_serv_fan_intr_get
* PURPOSE:
*   fan service fan interrupt get from file system
* PARAMETERS:
*   fan_number           (IN) fan number
*   value                (out) pointer of get value
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
int
bms_fan_serv_fan_intr_get(unsigned int fan_number,
                          unsigned int *value)
{
    return bms_sys_serv_dec_read(bms_fan_serv_data[fan_number].intr_src, value);
}

/*
* FEATURE:
*   bms_fan_serv_fan_input_get
* PURPOSE:
*   fan service fan input value get from file system
* PARAMETERS:
*   fan_number           (IN) fan number
*   value                (out) pointer of get value
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
int
bms_fan_serv_fan_input_get(unsigned int fan_number,
                           unsigned int *value)
{
    return bms_sys_serv_dec_read(bms_fan_serv_data[fan_number].input, value);
}

/*
* FEATURE:
*   bms_fan_serv_fan_mask_get
* PURPOSE:
*   fan service fan fault mask value get from file system
* PARAMETERS:
*   fan_number           (IN) fan number
*   value                (out) pointer of get value
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
int
bms_fan_serv_fan_mask_get(unsigned int fan_number,
                          unsigned int *value)
{
    return bms_sys_serv_dec_read(bms_fan_serv_data[fan_number].intr_msk, value);
}

/*
* FEATURE:
*   bms_fan_serv_module_type_get
* PURPOSE:
*   fan service fan type get from file system
* PARAMETERS:
*   module_number        (IN) module number
*   value                (OUT) pointer of get value
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
int
bms_fan_serv_module_type_get(unsigned int module_number,
                             unsigned int *value)
{
    return bms_sys_serv_hex_read(bms_fan_serv_data[module_number * BMS_FAN_NUM_PER_MODULE].type, value);
}

/*
* FEATURE:
*   bms_fan_serv_fan_present_get
* PURPOSE:
*   fan service fan present get from file system
* PARAMETERS:
*   value                (OUT) pointer of present bitmap
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
int
bms_fan_serv_fan_present_get(unsigned int *value)
{
    return bms_sys_serv_hex_read(bms_fan_serv_data[0].present, value);
}

/*
* FEATURE:
*   bms_fan_serv_fan_board_type_get
* PURPOSE:
*   fan service fan board get from file system
* PARAMETERS:
*   value                (OUT) pointer of get value
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
int
bms_fan_serv_fan_board_type_get(unsigned int *value)
{
    return bms_sys_serv_hex_read(BMS_SYSFS_BOARD_TYPE, value);
}

/*
* FEATURE:
*   bms_fan_serv_mask_init
* PURPOSE:
*   enable all fan interrupt mask in fan controller
* PARAMETERS:
*
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
static int
bms_fan_serv_mask_init(void)
{
    int i, ret_code = 0;

    for(i = 0; i < BMS_FAN_NUM_PER_MODULE * BMS_FAN_MODULE_NUM; i++){
        if((ret_code = bms_fan_serv_fan_mask_set(i, BMS_FAN_INTR_MASKED)) < 0){
            break;
        }
    }
    return ret_code;
}

/*
* FEATURE:
*   bms_fan_serv_cache_init
* PURPOSE:
*   initial fan status and fan type
* PARAMETERS:
*
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
static int
bms_fan_serv_cache_init(void)
{
    int ret_code = 0, i;
    for(i = 0; i < BMS_FAN_MODULE_NUM; i++){
        bms_fan_status[i] = BMS_FAN_MODULE_STATUS_NONINIT;
        bms_fan_retry[i] = BMS_FAN_NONREADY_RETRY_INIT;
        if((bms_board_type == BMS_AC_PSU_NORMAL_FAN) || (bms_board_type == BMS_DC_PSU_NORMAL_FAN)){
            bms_fan_type[i] = BMS_FAN_MODULE_TYPE_NORMAL;
        }else if((bms_board_type == BMS_AC_PSU_REVERSE_FAN) || (bms_board_type == BMS_DC_PSU_REVERSE_FAN)){
            bms_fan_type[i] = BMS_FAN_MODULE_TYPE_REVERSE;
        }else{
            syslog(LOG_WARNING|LOG_USER,"Can't identify board_type.\n");
            return -EINVAL;
        }
    }
    return ret_code;
}

/*
* FEATURE:
*   bms_fan_serv_pwm_init
* PURPOSE:
*   initial all fan pwm mode and duty cycle
* PARAMETERS:
*
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
static int
bms_fan_serv_pwm_init(void)
{
    int ret_code, i;

    for(i = 0; i < BMS_FAN_MODULE_NUM; i++){
        if((ret_code = bms_fan_serv_fan_pwm_enable_set(i, BMS_FAN_PWM_ENABLE_PWM)) < 0){
            break;
        }
        if((ret_code = bms_fan_serv_fan_pwm_set(i, BMS_FAN_PWM_DUTY_CYCLE_MAX)) < 0){
            break;
        }
    }
    return ret_code;
}

/*
* FEATURE:
*   bms_fan_serv_mutex_init
* PURPOSE:
*   initial mutex
* PARAMETERS:
*
* RETURNS:
*   init success, this function shall return zero.
*   otherwise, an error number shall be returned to indicate the error.
*/
static int
bms_fan_serv_mutex_init(void)
{
    int ret_code;

    if((ret_code = pthread_mutex_init(&bms_fan_cache_lock, NULL)) != 0){
        return -ret_code;
    }

    return ret_code;
}

/*
* FEATURE:
*   bms_fan_serv_cache_module_cache_get
* PURPOSE:
*   fan service cache get
* PARAMETERS:
*   module_number            (IN)  module number
*   module_status            (OUT) pointer of module status
*   module_type              (OUT) pointer of module type
* RETURNS:
*/
void
bms_fan_serv_cache_module_cache_get(unsigned int module_number,
                                    unsigned int* module_status,
                                    unsigned int* module_type)
{
    pthread_mutex_lock(&bms_fan_cache_lock);
    *module_status = bms_fan_status[module_number];
    *module_type = bms_fan_type[module_number];
    pthread_mutex_unlock(&bms_fan_cache_lock);
}

/*
* FEATURE:
*   bms_fan_serv_cache_module_cache_retry_get
* PURPOSE:
*   fan service cache retry get
* PARAMETERS:
*   module_number            (IN)  module number
*   module_retry             (OUT) pointer of module retry
* RETURNS:
*/
void
bms_fan_serv_cache_module_cache_retry_get(unsigned int module_number,
                                          unsigned int* module_retry)
{
    pthread_mutex_lock(&bms_fan_cache_lock);
    *module_retry = bms_fan_retry[module_number];
    pthread_mutex_unlock(&bms_fan_cache_lock);
}

/*
* FEATURE:
*   bms_fan_serv_cache_module_cache_retry_set
* PURPOSE:
*   fan service cache retry set
* PARAMETERS:
*   module_number            (IN)  module number
*   value                    (OUT) retry value
* RETURNS:
*/
void
bms_fan_serv_cache_module_cache_retry_set(unsigned int module_number,
                                          unsigned int value)
{
    pthread_mutex_lock(&bms_fan_cache_lock);
    bms_fan_retry[module_number] = value;
    pthread_mutex_unlock(&bms_fan_cache_lock);
}

/*
* FEATURE:
*   bms_fan_serv_file_path_rename
* PURPOSE:
*   rename sysfs path
* PARAMETERS:
* RETURNS:
*   success, this function returns 0.
*   for other cases, negative errno is returned.
*/
int
bms_fan_serv_file_path_rename(void)
{
    int i, ret_code = 0;

    for(i = 0; i < BMS_FAN_MODULE_NUM * BMS_FAN_CONTROL_NUM ; i++){
        if((ret_code = bms_sys_serv_hwmon_path_find(bms_fan_serv_data[(i/BMS_FAN_MODULE_NUM) * BMS_FAN_MODULE_NUM].hwmon_path,
                                                    bms_fan_serv_data[i].intr_src)) < 0){
            return -ret_code;
        }
        if((ret_code = bms_sys_serv_hwmon_path_find(bms_fan_serv_data[(i/BMS_FAN_MODULE_NUM) * BMS_FAN_MODULE_NUM].hwmon_path,
                                                    bms_fan_serv_data[i].intr_msk)) < 0){
            return -ret_code;
        }
        if((ret_code = bms_sys_serv_hwmon_path_find(bms_fan_serv_data[(i/BMS_FAN_MODULE_NUM) * BMS_FAN_MODULE_NUM].hwmon_path,
                                                    bms_fan_serv_data[i].pwm)) < 0){
            return -ret_code;
        }
        if((ret_code = bms_sys_serv_hwmon_path_find(bms_fan_serv_data[(i/BMS_FAN_MODULE_NUM) * BMS_FAN_MODULE_NUM].hwmon_path,
                                                    bms_fan_serv_data[i].pwm_enable)) < 0){
            return -ret_code;
        }
        if((ret_code = bms_sys_serv_hwmon_path_find(bms_fan_serv_data[(i/BMS_FAN_MODULE_NUM) * BMS_FAN_MODULE_NUM].hwmon_path,
                                                    bms_fan_serv_data[i].input)) < 0){
            return -ret_code;
        }
    }

    return ret_code;
}


/*
* FEATURE:
*   bms_fan_serv_init
* PURPOSE:
*   initial fan servd
* PARAMETERS:
*   mq_name            (IN) message queue name
*   mq_desc            (OUT) pointer of message queue description
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
static int
bms_fan_serv_init(char *mq_name,
                  mqd_t *mq_desc)
{
    int ret_code = 0;

    /* 1. record board type from CPLD */
    if((ret_code = bms_fan_serv_fan_board_type_get(&bms_board_type)) < 0){
        return ret_code;
    }

    /* 2. initial cache to maintain fan statue and type. */
    if((ret_code = bms_fan_serv_cache_init()) < 0){
        return ret_code;
    }

    /* 3. rename file path */
    if((ret_code = bms_fan_serv_file_path_rename()) < 0){
        return ret_code;
    }

    /* 4. enable all fan mask */
    if((ret_code = bms_fan_serv_mask_init()) < 0)
        return ret_code;

    /* 5. open message queue */
    if ((ret_code = bms_sys_serv_msq_open(mq_name, mq_desc)) < 0) {
        return ret_code;
    }

    /* 6. default set PWM mode */
    if ((ret_code = bms_fan_serv_pwm_init() < 0)) {
        return ret_code;
    }

    /* 7. initial Mutexes */
    if ((ret_code = bms_fan_serv_mutex_init() < 0)) {
        return ret_code;
    }

    /* 8. set initial flag */
    bms_fan_init_done = 1;

    return ret_code;
}


/*
 * FEATURE:
 *   bms_fan_serv_source_identify
 * PURPOSE:
 *   identify interrupt source from absent or interrupt
 * PARAMETERS:
 *   module_bmap             (OUT) module bi map
 *   module_cause            (OUT) module status
 * RETURNS:
 *   open success, this function returns .
 *   for other cases, negative errno is returned.
 */
int
bms_fan_serv_source_identify(unsigned int *module_bmap,
                             unsigned int *module_cause)
{
    unsigned int module_present_bmap, fan_intr;
    unsigned int mask = 1;
    unsigned int cache_status[BMS_FAN_MODULE_NUM], cache_type[BMS_FAN_MODULE_NUM];
    int ret_code = 0, i;

    for(i = 0 ; i < BMS_FAN_MODULE_NUM; i++){
        bms_fan_serv_cache_module_cache_get(i, &cache_status[i], &cache_type[i]);
    }
    /* Is fan interrupt, return bmap */
    /* this i is fan number */
    for(i = 0 ; i < BMS_FAN_MODULE_NUM * BMS_FAN_NUM_PER_MODULE; i++){
        /* read from max31790, 0 for normal and 1 for failed */
        if((ret_code = bms_fan_serv_fan_intr_get(i, &fan_intr)) < 0){
            return ret_code;
        }

        if(((cache_status[i / BMS_FAN_NUM_PER_MODULE] == BMS_FAN_MODULE_STATUS_NORMAL) ||
            (cache_status[i / BMS_FAN_NUM_PER_MODULE] == BMS_FAN_MODULE_STATUS_NONREADY))
           && (fan_intr == BMS_FAN_INTR_FAULT)){
            *module_bmap |= (mask << ((i / BMS_FAN_NUM_PER_MODULE)));
            *module_cause = BMS_FAN_MODULE_STATUS_FAILED;
        }
    }

    if(*module_bmap != 0){
        return ret_code;
    }

    /* read fan module present from sysfs, 0 for present and 1 for non-present */
    if((ret_code = bms_fan_serv_fan_present_get(&module_present_bmap)) < 0){
        return ret_code;
    }

    /* Is module non-present, return module number, because we don't care non-present here. */
    /* this i is fan module */
    for(i = 0 ; i < BMS_FAN_MODULE_NUM; i++){
        if((cache_status[i] == BMS_FAN_MODULE_STATUS_NORMAL) ||
           (cache_status[i] == BMS_FAN_MODULE_STATUS_NONREADY) ||
           (cache_status[i] == BMS_FAN_MODULE_STATUS_FAILED)){
            if((module_present_bmap & mask)){
                *module_bmap = i;
                *module_cause = BMS_FAN_MODULE_STATUS_NONPRESENT;
                return ret_code;
            }
        }
        mask = mask << 1;
    }

    syslog(LOG_WARNING|LOG_USER,"Can't found fan interrupt source .\n");
    return -EINVAL;
}

/*
* FEATURE:
*   bms_fan_serv_cause_log
* PURPOSE:
*   log of fan cause
* PARAMETERS:
*   module_number           (IN) module number
*   module_cause            (IN) cause of fan module status
* RETURNS:
*/
static void
bms_fan_serv_cause_log(unsigned int module_number,
                       unsigned int module_cause)
{
    if(module_cause == BMS_FAN_MODULE_STATUS_NONPRESENT)
        syslog(LOG_DEBUG|LOG_USER,"The fan module %u was non present\n", module_number + 1);
    else if(module_cause == BMS_FAN_MODULE_STATUS_FAILED)
        syslog(LOG_WARNING|LOG_USER,"The fan module %u was fault\n", module_number + 1);
    else if(module_cause == BMS_FAN_MODULE_STATUS_NORMAL)
        syslog(LOG_DEBUG|LOG_USER,"The fan module %u was present\n", module_number + 1);
    else
        syslog(LOG_WARNING|LOG_USER,"LOG error, unknown fan_cause in fan module %u\n", module_number + 1);
}

/*
* FEATURE:
*   bms_fan_serv_intr_mask_set
* PURPOSE:
*   set specific fan mask
* PARAMETERS:
*   module_number           (IN) module number
*   module_mask             (IN) module mask
* RETURNS:
*   success, this function returns zero.
*   for other cases, negative errno is returned.
*/
int
bms_fan_serv_intr_mask_set(unsigned int module_number,
                           unsigned int module_mask)
{
    int ret_code = 0, i;

    /* write to max31790, 0 for unmask and 1 for masked */
    for(i = 0; i < BMS_FAN_NUM_PER_MODULE; i++){
        if((ret_code = bms_fan_serv_fan_mask_set((module_number * BMS_FAN_NUM_PER_MODULE) + i, module_mask)) < 0){
            return ret_code;
        }
    }

    return ret_code;
}


/*
* FEATURE:
*   bms_fan_serv_find_serv_data_index
* PURPOSE:
*   find index of fan of serv_data
* PARAMETERS:

* RETURNS:
*   success, this function returns value.
*   for other cases, negative errno is returned.
*/
static int
bms_fan_serv_find_serv_data_index(void)
{
    int i;
    for(i = 0; i < bms_sys_serv_data_num; i++){
        if(strcmp(bms_sys_serv_data[i].name, BMS_FAN_SERV_DATA_NAME) == 0)
            return i;
    }

    syslog(LOG_WARNING|LOG_USER,"Can't find %s item index in bms_sys_serv_data\n", BMS_FAN_SERV_DATA_NAME);
    return -EINVAL;
}


/*
* FEATURE:
*   bms_fan_serv_global_mask_enable
* PURPOSE:
*   enable fan global mask
* PARAMETERS:

* RETURNS:
*   success, this function returns zero.
*   for other cases, negative errno is returned.
*/
int
bms_fan_serv_global_mask_enable(void)
{
    int ret_code = 0, index;

    if((ret_code = bms_fan_serv_find_serv_data_index()) < 0)
        return ret_code;

    index = ret_code;
    if((ret_code = bms_fan_serv_fan_global_mask_set(index, BMS_FAN_GLOBAL_INTR_UNMASKED)) < 0){
        return ret_code;
    }

    return ret_code;
}

/*
* FEATURE:
*   bms_fan_serv_board_type_comp
* PURPOSE:
*   compare board tpye with fan type
* PARAMETERS:
*   module_type             (IN) module type
* RETURNS:
*   success, compare the same return zero.
*   for other cases, negative errno is returned.
*/
static int
bms_fan_serv_board_type_comp(unsigned int module_type)
{

    if(((bms_board_type == BMS_AC_PSU_NORMAL_FAN) || (bms_board_type == BMS_DC_PSU_NORMAL_FAN)) &&
        (module_type == BMS_FAN_MODULE_TYPE_NORMAL)){
        return 0;
    }

    if(((bms_board_type == BMS_AC_PSU_REVERSE_FAN) || (bms_board_type == BMS_DC_PSU_REVERSE_FAN)) &&
        (module_type == BMS_FAN_MODULE_TYPE_REVERSE)){
        return 0;
    }

    return -EINVAL;
}

/*
* FEATURE:
*   bms_fan_serv_module_led_update
* PURPOSE:
*   update fan module led
* PARAMETERS:
*   module_number        (IN) module number
*   module_cause         (IN) cause of fan module event
*   module_type          (IN) fan module type
* RETURNS:
*   success, compare the same return zero.
*   for other cases, negative errno is returned.
*/
static int
bms_fan_serv_module_led_update(unsigned int module_number,
                               unsigned int module_cause,
                               unsigned int module_type)
{
    int ret_code = 0;
    unsigned int cache_status, cache_type;

    bms_fan_serv_cache_module_cache_get(module_number, &cache_status, &cache_type);

    /* current fan module led status */
    if(cache_status == BMS_FAN_MODULE_STATUS_NORMAL){
        if(bms_fan_serv_board_type_comp(cache_type) == 0){
            /* current fan module led is green */
            if(module_cause == BMS_FAN_MODULE_STATUS_FAILED){
                /* change fan module led to amber */
                if((ret_code = bms_fan_serv_fan_module_led_set(module_number, BMS_FAN_MODULE_LED_AMBER)) < 0){
                    return ret_code;
                }
                return ret_code;
            }else if(module_cause == BMS_FAN_MODULE_STATUS_NONPRESENT){
                /* shutdown fan module led */
                if((ret_code = bms_fan_serv_fan_module_led_set(module_number, BMS_FAN_MODULE_LED_OFF)) < 0){
                    return ret_code;
                }
                return ret_code;
            }else if(module_cause == BMS_FAN_MODULE_STATUS_NORMAL){
                /* Do nothing */
                return ret_code;
            }
        }else{
            /* current fan module is amber */
            if(module_cause == BMS_FAN_MODULE_STATUS_NONPRESENT){
                /* shutdown fan module led */
                if((ret_code = bms_fan_serv_fan_module_led_set(module_number, BMS_FAN_MODULE_LED_OFF)) < 0){
                    return ret_code;
                }
                return ret_code;
            }else if(module_cause == BMS_FAN_MODULE_STATUS_FAILED){
                /* Do nothing */
                return ret_code;
            }else if(module_cause == BMS_FAN_MODULE_STATUS_NORMAL){
                if(bms_fan_serv_board_type_comp(module_type) == 0){
                    if((ret_code = bms_fan_serv_fan_module_led_set(module_number, BMS_FAN_MODULE_LED_GREEN)) < 0){
                        return ret_code;
                    }
                }else{
                    /* Do nothing */
                    return ret_code;
                }
            }
        }
    }else
    if((cache_status == BMS_FAN_MODULE_STATUS_NONPRESENT) ||
       (cache_status == BMS_FAN_MODULE_STATUS_NONINIT) ||
       (cache_status == BMS_FAN_MODULE_STATUS_NONREADY)){
        /* current fan module is off */
        if(module_cause == BMS_FAN_MODULE_STATUS_NORMAL){
            if(bms_fan_serv_board_type_comp(module_type) == 0){
                /* change fan module led to green */
                if((ret_code = bms_fan_serv_fan_module_led_set(module_number, BMS_FAN_MODULE_LED_GREEN)) < 0){
                    return ret_code;
                }
                return ret_code;
            }else{
                /* change fan module to amber */
                if((ret_code = bms_fan_serv_fan_module_led_set(module_number, BMS_FAN_MODULE_LED_AMBER)) < 0){
                    return ret_code;
                }
                return ret_code;
            }
        }else if(module_cause == BMS_FAN_MODULE_STATUS_FAILED){
            /* change fan module led to amber */
            if((ret_code = bms_fan_serv_fan_module_led_set(module_number, BMS_FAN_MODULE_LED_AMBER)) < 0){
                return ret_code;
            }
            return ret_code;
        }else if(module_cause == BMS_FAN_MODULE_STATUS_NONPRESENT){
            /* Do nothing */
            return ret_code;
        }
    }else
    if(cache_status == BMS_FAN_MODULE_STATUS_FAILED){
        /* current fan module led is amber */
        /* mast be present the fan cause will be BMS_FAN_MODULE_STATUS_NORMAL */
        if(module_cause == BMS_FAN_MODULE_STATUS_NORMAL){
            if (bms_fan_serv_board_type_comp(module_type) == 0){
                /* change fan module led to green */
                if((ret_code = bms_fan_serv_fan_module_led_set(module_number, BMS_FAN_MODULE_LED_GREEN)) < 0){
                    return ret_code;
                }
                return ret_code;
            }else{
                /* fan type was different from board type, current fan module led was amber, so do nothing */
                return ret_code;
            }
        }else if((module_cause == BMS_FAN_MODULE_STATUS_NONPRESENT)){
            /* shutdown fan module led */
            if((ret_code = bms_fan_serv_fan_module_led_set(module_number, BMS_FAN_MODULE_LED_OFF)) < 0){
                return ret_code;
            }
            return ret_code;
        }else if((module_cause == BMS_FAN_MODULE_STATUS_FAILED)){
            /* Do nothing */
            return ret_code;
        }
    }

    syslog(LOG_WARNING|LOG_USER,"Error input different from cache.\n");
    return -EINVAL;
}

/*
* FEATURE:
*   bms_fan_serv_cache_update
* PURPOSE:
*   update data to cache
* PARAMETERS:
*   module_number           (IN) module number
*   module_cause            (IN) cause of fan module event
*   module_type             (IN) fan module type
* RETURNS:
*/
static void
bms_fan_serv_cache_update(unsigned int module_number,
                          unsigned int module_cause,
                          unsigned int module_type)
{
    pthread_mutex_lock(&bms_fan_cache_lock);
    bms_fan_status[module_number] = module_cause;

    if((int)module_type != -1){
        bms_fan_type[module_number] = module_type;
    }
    pthread_mutex_unlock(&bms_fan_cache_lock);
}

/*
* FEATURE:
*   bms_fan_serv_panel_led_by_cache_get
* PURPOSE:
*   get panel led status from scan cache
* PARAMETERS:
*
* RETURNS:
*   BMS_FAN_PANEL_LED_AMBER or BMS_FAN_PANEL_LED_GREEN
*/
static int
bms_fan_serv_panel_led_by_cache_get(void)
{
    int i = 0;
    unsigned int cache_status[BMS_FAN_MODULE_NUM], cache_type[BMS_FAN_MODULE_NUM];

    /* read value from cache */
    for(i = 0; i < BMS_FAN_MODULE_NUM; i++){
        bms_fan_serv_cache_module_cache_get(i, &cache_status[i], &cache_type[i]);
    }

    /* is cache have any non init status */
	for(i = 0; i < BMS_FAN_MODULE_NUM; i++){
        if(cache_status[i] == BMS_FAN_MODULE_STATUS_NONINIT){
            return BMS_FAN_PANEL_LED_OFF;
        }
    }

    /* is cache all normal and fan type the same with board type */
    for(i = 0; i < BMS_FAN_MODULE_NUM; i++){
        if((cache_status[i] != BMS_FAN_MODULE_STATUS_NORMAL) ||
           (bms_fan_serv_board_type_comp(cache_type[i]) != 0)){
            return BMS_FAN_PANEL_LED_AMBER;
        }
    }
    return BMS_FAN_PANEL_LED_GREEN;
}

/*
* FEATURE:
*   bms_fan_serv_panel_led_speed_normal_change
* PURPOSE:
*   change panel fan led to green and fan speed to normal
* PARAMETERS:
*
* RETURNS:
*   success, compare the same return zero.
*   for other cases, negative errno is returned.
*/
static int
bms_fan_serv_panel_led_speed_normal_change(void)
{
    int ret_code = 0, i;
    unsigned int cache_status[BMS_FAN_MODULE_NUM], cache_type[BMS_FAN_MODULE_NUM];
    char buf[64];

    /* read value from cache */
    for(i = 0; i < BMS_FAN_MODULE_NUM; i++){
        bms_fan_serv_cache_module_cache_get(i, &cache_status[i], &cache_type[i]);
    }

    if((ret_code = bms_fan_serv_fan_panel_led_set(BMS_FAN_PANEL_LED_GREEN)) < 0){
        return ret_code;
    }

    for(i = 0; i < BMS_FAN_MODULE_NUM; i++){
        if(cache_status[i] == BMS_FAN_MODULE_STATUS_NONPRESENT)
            continue;
        if((ret_code = bms_fan_serv_fan_pwm_set(i, BMS_FAN_PWM_DUTY_CYCLE_NORMAL)) < 0){
            return ret_code;
        }
    }

    snprintf(buf, sizeof(buf),"%s start", bms_fan_serv_data[0].smart_fan_path);
    system(buf);

    return ret_code;
}

/*
* FEATURE:
*   bms_fan_serv_panel_led_speed_failed_change
* PURPOSE:
*   change panel fan led to amber and fan speed to max
* PARAMETERS:
*
* RETURNS:
*   success, compare the same return zero.
*   for other cases, negative errno is returned.
*/
static int
bms_fan_serv_panel_led_speed_failed_change(void)
{
    int ret_code = 0, i;
    unsigned int cache_status[BMS_FAN_MODULE_NUM], cache_type[BMS_FAN_MODULE_NUM];
    char buf[64];

    /* read value from cache */
    for(i = 0; i < BMS_FAN_MODULE_NUM; i++){
        bms_fan_serv_cache_module_cache_get(i, &cache_status[i], &cache_type[i]);
    }

    if((ret_code = bms_fan_serv_fan_panel_led_set(BMS_FAN_PANEL_LED_AMBER)) < 0){
        return ret_code;
    }

    snprintf(buf, sizeof(buf),"%s stop", bms_fan_serv_data[0].smart_fan_path);
    system(buf);

    for(i = 0; i < BMS_FAN_MODULE_NUM; i++){
        if(cache_status[i] == BMS_FAN_MODULE_STATUS_NONPRESENT)
            continue;
        if((ret_code = bms_fan_serv_fan_pwm_set(i, BMS_FAN_PWM_DUTY_CYCLE_MAX)) < 0){
            return ret_code;
        }
    }

    return ret_code;
}

/*
* FEATURE:
*   bms_fan_cache_airflow_module_panel_led_update
* PURPOSE:
*   update all fan cache, air flow, fan module and panel led
* PARAMETERS:
*   module_number        (IN) module number
*   module_cause         (IN) cause of fan module event
*   module_type          (IN) fan module type
* RETURNS:
*   success, compare the same return zero.
*   for other cases, negative errno is returned.
*/
static int
bms_fan_serv_cache_airflow_module_panel_led_update(unsigned int module_number,
                                                   unsigned int module_cause,
                                                   unsigned int module_type)
{
    int ret_code = 0;
    unsigned int pre_status, cur_status;
    if((ret_code = bms_fan_serv_module_led_update(module_number, module_cause, module_type)) < 0)
        return ret_code;

    pre_status = bms_fan_serv_panel_led_by_cache_get();

    bms_fan_serv_cache_update(module_number, module_cause, module_type);

    cur_status = bms_fan_serv_panel_led_by_cache_get();


    if(cur_status == pre_status)
        return ret_code;
    if(cur_status == BMS_FAN_PANEL_LED_GREEN){
        if((ret_code = bms_fan_serv_panel_led_speed_normal_change()) < 0){
            return ret_code;
        }
    }else{
        if((ret_code = bms_fan_serv_panel_led_speed_failed_change()) < 0){
            return ret_code;
        }
    }
    return ret_code;
}

/*
* FEATURE:
*   bms_fan_serv_fan_failed_datect
* PURPOSE:
*   detect fan failed cause
* PARAMETERS:
*   module_number        (IN) module number
*   module_status        (OUT) cause of fan module status
*   success, compare the same return zero.
*   for other cases, negative errno is returned.
*/
int
bms_fan_serv_fan_failed_datect(unsigned int module_number,
                               unsigned int *fan_status)
{
    unsigned int fan_intr, fan_input;
    int ret_code, i;

    /* fan failed datect */
    /* read from max31790, 0 for normal and 1 for failed */
    for(i = 0; i < BMS_FAN_NUM_PER_MODULE; i++){
        if((ret_code = bms_fan_serv_fan_intr_get((module_number * BMS_FAN_NUM_PER_MODULE) + i, &fan_intr)) < 0){
            return ret_code;
        }
        if(fan_intr){
            *fan_status = BMS_FAN_MODULE_STATUS_FAILED;
            return ret_code;
        }
    }

    /* detect fan speed */
    for(i = 0; i < BMS_FAN_NUM_PER_MODULE; i++){
        if((ret_code = bms_fan_serv_fan_input_get((module_number * BMS_FAN_NUM_PER_MODULE) + i, &fan_input)) < 0){
            return ret_code;
        }

        if(fan_input == BMS_FAN_MIN_FAN_SPEED){
            *fan_status = BMS_FAN_MODULE_STATUS_FAILED;
            return ret_code;
        }
    }

    *fan_status = BMS_FAN_MODULE_STATUS_NORMAL;

    return ret_code;
}


/*
* FEATURE:
*   bms_fan_servd
* PURPOSE:
*   service to handle message queue event of fan
* PARAMETERS:
*   args                (IN) message queue name
* RETURNS:
*   open success, this function will wait for message queue.
*   for other cases, will exit this program.
*/
void*
bms_fan_servd(void *args)
{
    char *mq_name = (char*)args;
    mqd_t mq_desc;
    bms_sys_serv_mq_data_t msg;
    int ret_code;
    unsigned int module_number, module_type;
    unsigned int module_status;
    unsigned int cache_status, cache_type;

    /* initial */
    if(bms_fan_serv_init(mq_name, &mq_desc) != 0)
        goto quit;

    while (1) {
        /* Wait for message queue */
        if (mq_receive(mq_desc, (char*)&msg, sizeof(msg), 0) < 0) {
            ret_code = errno;
            syslog(LOG_WARNING|LOG_USER,"Failed to receive message from %s (%s)\n", mq_name, strerror(ret_code));
            goto quit;
        }

        switch (msg.serv_type) {
            case SERV_TYPE_RX_INTR: /* FAN_ALERT_INT interrupt */
                module_number = msg.number;

                bms_fan_serv_cause_log(module_number, BMS_FAN_MODULE_STATUS_FAILED);

                if(bms_fan_serv_cache_airflow_module_panel_led_update(module_number, BMS_FAN_MODULE_STATUS_FAILED, -1) < 0){
                    break;
                }
                break;

            case SERV_TYPE_FAN_MODULE_PRESENT:
                module_number = msg.number;
                module_type = msg.type;

                /* ignore wrong status */
                bms_fan_serv_cache_module_cache_get(module_number, &cache_status, &cache_type);
                if((cache_status != BMS_FAN_MODULE_STATUS_NONREADY) &&
                  (cache_status != BMS_FAN_MODULE_STATUS_NONINIT) &&
                  (cache_status != BMS_FAN_MODULE_STATUS_NONPRESENT)){
                    break;
                }

                if((cache_status == BMS_FAN_MODULE_STATUS_NONPRESENT) ||
                    (cache_status == BMS_FAN_MODULE_STATUS_NONINIT)){
                    /* we assume fan module must failed when fan present */
                    module_status = BMS_FAN_MODULE_STATUS_FAILED;
                }else{
                    if(bms_fan_serv_fan_failed_datect(module_number, &module_status) < 0){
                        break;
                    }
                }

                if(module_status == BMS_FAN_MODULE_STATUS_FAILED){
                    /* if fan present within 1 second, set fan status to non-ready */
                    bms_fan_serv_cache_update(module_number, BMS_FAN_MODULE_STATUS_NONREADY, module_type);
                }else if(module_status == BMS_FAN_MODULE_STATUS_NORMAL){

                    bms_fan_serv_cause_log(module_number, BMS_FAN_MODULE_STATUS_NORMAL);
                    bms_fan_serv_cache_airflow_module_panel_led_update(module_number, BMS_FAN_MODULE_STATUS_NORMAL, module_type);

                }

                if((cache_status == BMS_FAN_MODULE_STATUS_NONINIT) ||
                   (cache_status == BMS_FAN_MODULE_STATUS_NONPRESENT)){
                    if(bms_fan_serv_board_type_comp(module_type) < 0){
                        syslog(LOG_WARNING|LOG_USER,"The fan module %u type was wrong\n", module_number + 1);
                    }
                }

                break;
            case SERV_TYPE_FAN_MODULE_NONPRESENT:
                module_number = msg.number;

                /* ignore wrong status */
                bms_fan_serv_cache_module_cache_get(module_number, &cache_status, &cache_type);
                if(cache_status == BMS_FAN_MODULE_STATUS_NONPRESENT){
                    break;
                }

                /* clear retry cache */
                bms_fan_serv_cache_module_cache_retry_set(module_number, BMS_FAN_NONREADY_RETRY_INIT);

                if(cache_status != BMS_FAN_MODULE_STATUS_NONINIT){
                    bms_fan_serv_cause_log(module_number, BMS_FAN_MODULE_STATUS_NONPRESENT);
                }
                if(bms_fan_serv_cache_airflow_module_panel_led_update(module_number, BMS_FAN_MODULE_STATUS_NONPRESENT, -1) < 0)
                    break;

                break;
            default:
                syslog(LOG_WARNING|LOG_USER,"Receive an unknown message %d from %s\n", msg.serv_type, mq_name);
                break;
        }
    }

quit:
    pthread_mutex_destroy(&bms_fan_cache_lock);
    pthread_exit(NULL);
}
