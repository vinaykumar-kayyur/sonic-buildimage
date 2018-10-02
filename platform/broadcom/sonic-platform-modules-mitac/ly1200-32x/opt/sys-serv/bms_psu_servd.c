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
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>
#include <unistd.h>
#include <stdio.h>
#include "bms_irq_sysd.h"
#include "bms_sys_serv_common.h"
#include "bms_psu_servd.h"

bms_psu_serv_data_t bms_psu_serv_data[BMS_PSU_NUM] = {
    {
        .name = "PS1",
        .i2c_path = "/sys/bus/i2c/devices/i2c-5/new_device",
        .driver_name = "fse000",
        .pg_offset = 6,
        .ps_offset = 7,
        .address = 0x58,
        .pg_ps_reg = "/sys/bus/i2c/devices/1-0032/psu_en_status_fld",
        .model_reg = "mfr_model",
        .hwmon_path = "/sys/bus/i2c/devices/5-0058/hwmon",
        .intr_src = {
                     "vout_ov_fault",
                     "vout_uv_fault",
                     "curr2_crit_alarm",
                     "curr2_max_alarm",
                     "ot_fault",
                     "ot_warning",
                     "vin_uv_warning",
                     "vin_uv_fault",
                     "fan1_fault",
                     "fan1_alarm",
                    },
    },
    {
        .name = "PS2",
        .i2c_path = NULL, /* share with ps1 i2c_path */
        .driver_name = NULL, /* share with ps1 driver_name */
        .pg_offset = 2,
        .ps_offset = 3,
        .address = 0x59,
        .pg_ps_reg = NULL, /* share with ps1 pg_ps_reg */
        .model_reg = "mfr_model",
        .hwmon_path = "/sys/bus/i2c/devices/5-0059/hwmon",
        .intr_src = {
                     "vout_ov_fault",
                     "vout_uv_fault",
                     "curr2_crit_alarm",
                     "curr2_max_alarm",
                     "ot_fault",
                     "ot_warning",
                     "vin_uv_warning",
                     "vin_uv_fault",
                     "fan1_fault",
                     "fan1_alarm",
                    },
    },
};

char *bms_psu_mfr_model[] = {
    "FSE047-180G",
    "FSE048-180G",
    "FSE050-180G",
    "FSE049-180G"
};

unsigned int bms_psu_board_type;
unsigned int bms_psu_status[BMS_PSU_NUM];
unsigned int bms_psu_type[BMS_PSU_NUM];
unsigned int bms_psu_driver_init[BMS_PSU_NUM] = {0};
unsigned int bms_psu_init_done = 0;
unsigned int bms_psu_intr_cache[BMS_PSU_NUM * BMS_PSU_INTR_NUM] = {0};
pthread_mutex_t bms_psu_st_cache_lock;
pthread_mutex_t bms_psu_intr_cache_lock;

/*
* FEATURE:
*   bms_psu_serv_power_status_get
* PURPOSE:
*   psu service psu status get from file system
* PARAMETERS:
*   psu_number           (IN) psu number
*   value                (OUT) pointer of get value
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
int
bms_psu_serv_power_status_get(unsigned int *value)
{
    return bms_sys_serv_hex_read(bms_psu_serv_data[0].pg_ps_reg, value);
}

/*
* FEATURE:
*   bms_psu_serv_type_get
* PURPOSE:
*   psu service psu type get from file system
* PARAMETERS:
*   psu_number           (IN) psu number
*   value                (OUT) pointer of get value
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
int
bms_psu_serv_type_get(unsigned int psu_number,
                      unsigned int *value)
{
    int ret_code, i, type_num;
    char buf[32] = {0};

    /* size of type number */
    type_num = sizeof(bms_psu_mfr_model) / sizeof(bms_psu_mfr_model[0]);

    if((ret_code = bms_sys_serv_char_read(bms_psu_serv_data[psu_number].model_reg, buf)) < 0)
        return ret_code;

    for(i = 0; i < type_num; i++) {
        if(strncmp(bms_psu_mfr_model[i], buf, strlen(bms_psu_mfr_model[i])) == 0) {
            break;
        }
    }

    if(i == type_num) {
        syslog(LOG_WARNING|LOG_USER,"[%s] can't find type data", __FUNCTION__);
        return -EINVAL;
    }else{
        *value = i;
    }

    return ret_code;
}

/*
* FEATURE:
*   bms_psu_serv_board_type_get
* PURPOSE:
*   psu service board get from file system
* PARAMETERS:
*   value                (OUT) pointer of get value
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
int
bms_psu_serv_board_type_get(unsigned int *value)
{
    return bms_sys_serv_hex_read(BMS_SYSFS_BOARD_TYPE, value);
}

/*
* FEATURE:
*   bms_psu_serv_cache_update
* PURPOSE:
*   update data to cache
* PARAMETERS:
*   psu_number           (IN) psu number
*   psu_cause            (IN) cause of psu event
*   psu_type             (IN) psu type
* RETURNS:
*/
static void
bms_psu_serv_cache_update(unsigned int psu_number,
                          unsigned int psu_cause,
                          unsigned int psu_type)
{
    pthread_mutex_lock(&bms_psu_st_cache_lock);
    bms_psu_status[psu_number] = psu_cause;

    if((int)psu_type != (-1)) {
        bms_psu_type[psu_number] = psu_type;
    }
    pthread_mutex_unlock(&bms_psu_st_cache_lock);
}

/*
* FEATURE:
*   bms_psu_serv_cache_init
* PURPOSE:
*   initial psu status and psu type
* PARAMETERS:
*
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
static void
bms_psu_serv_cache_init(void)
{
    int i;

    for(i = 0; i < BMS_PSU_NUM; i++) {
        bms_psu_serv_cache_update(i, BMS_PSU_STATUS_ABSENT, bms_psu_board_type);
    }
    memset(bms_psu_intr_cache, 0, sizeof(unsigned int) * BMS_PSU_NUM * BMS_PSU_INTR_NUM);
}


/*
* FEATURE:
*   bms_psu_serv_power_led_set
* PURPOSE:
*   psu service power led set to file system in CPLD
* PARAMETERS:
*   value                (IN) setting value
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
int
bms_psu_serv_power_led_set(unsigned int value)
{
    return bms_sys_serv_write(BMS_SYSFS_POWER_LED, value);
}


/*
* FEATURE:
*   bms_psu_serv_mutex_init
* PURPOSE:
*   initial mutex
* PARAMETERS:
*
* RETURNS:
*   init success, this function shall return zero.
*   otherwise, an error number shall be returned to indicate the error.
*/
static int
bms_psu_serv_mutex_init(void)
{
    int ret_code;

    if((ret_code = pthread_mutex_init(&bms_psu_st_cache_lock, NULL)) != 0) {
        return -ret_code;
    }

    if((ret_code = pthread_mutex_init(&bms_psu_intr_cache_lock, NULL)) != 0) {
        return -ret_code;
    }

    return ret_code;
}

/*
* FEATURE:
*   bms_psu_serv_file_path_rename
* PURPOSE:
*   psu hwmon path rename
* PARAMETERS:
*
* RETURNS:
*   init success, this function shall return zero.
*   otherwise, an error number shall be returned to indicate the error.
*/
int
bms_psu_serv_file_path_rename(unsigned int psu_number)
{
    int ret_code = 0;
    unsigned int i;

    for(i = psu_number * BMS_PSU_INTR_NUM; i < ((BMS_PSU_INTR_NUM * psu_number) + BMS_PSU_INTR_NUM); i++){
        if(bms_psu_driver_init[i / BMS_PSU_INTR_NUM] == BMS_PSU_DRIVER_UNINIT)
            continue;
        if((ret_code = bms_sys_serv_hwmon_path_find(bms_psu_serv_data[i / BMS_PSU_INTR_NUM].hwmon_path,
                                                    bms_psu_serv_data[i / BMS_PSU_INTR_NUM].intr_src[i % BMS_PSU_INTR_NUM])) < 0){
            return -ret_code;
        }
    }

    if(bms_psu_driver_init[psu_number] == BMS_PSU_DRIVER_INIT_DONE){
        if((ret_code = bms_sys_serv_hwmon_path_find(bms_psu_serv_data[psu_number].hwmon_path,
                                                    bms_psu_serv_data[psu_number].model_reg)) < 0){
            return -ret_code;
        }
    }
    return ret_code;
}

/*
* FEATURE:
*   bms_psu_serv_driver_plugin
* PURPOSE:
*   plug in driver to create sysfs
* PARAMETERS:
*
* RETURNS:
*   init success, this function shall return zero.
*   otherwise, an error number shall be returned to indicate the error.
*/
int
bms_psu_serv_driver_plugin(int psu_number)
{
    char buf[64];
    int buf_size = sizeof(buf);
    int ret_code = 0;

    if(bms_sys_serv_file_exist(bms_psu_serv_data[psu_number].hwmon_path) == 1){
        /*  hwmon path not exist*/

        /* echo driver to create sysfs */
        snprintf(buf, buf_size, "%s %d",bms_psu_serv_data[0].driver_name, bms_psu_serv_data[psu_number].address);//
        if((ret_code = bms_sys_serv_buf_write(bms_psu_serv_data[0].i2c_path, buf, buf_size)) < 0)
            return ret_code;
    }
    bms_psu_driver_init[psu_number] = BMS_PSU_DRIVER_INIT_DONE;

    if ((ret_code = bms_psu_serv_file_path_rename(psu_number)) < 0) {
        return ret_code;
    }

    return ret_code;
}

/*
* FEATURE:
*   bms_psu_serv_driver_init
* PURPOSE:
*   Initial sysfs and rename path of sysfs
* PARAMETERS:
*
* RETURNS:
*   init success, this function shall return zero.
*   otherwise, an error number shall be returned to indicate the error.
*/
static int
bms_psu_serv_driver_init(void)
{
    int ret_code = 0;
    unsigned int psu_ps_pg = 0, i;

    if((ret_code = bms_sys_serv_hex_read(bms_psu_serv_data[0].pg_ps_reg, &psu_ps_pg)) < 0)
        return ret_code;

    for(i = 0; i < BMS_PSU_NUM ; i++){
        if((psu_ps_pg & (1 << bms_psu_serv_data[i].pg_offset)) == BMS_PSU_PG_GOOD){
            if((ret_code = bms_psu_serv_driver_plugin(i)) < 0)
                return ret_code;
        }
    }
    return ret_code;
}

/*
* FEATURE:
*   bms_psu_serv_init
* PURPOSE:
*   initial psu servd
* PARAMETERS:
*   mq_name            (IN) message queue name
*   mq_desc            (OUT) pointer of message queue description
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
static int
bms_psu_serv_init(char *mq_name,
                  mqd_t *mq_desc)
{
    int ret_code = 0;

    /* 1 init pmbus to create sysfs */
    if((ret_code = bms_psu_serv_driver_init()) < 0) {
        return ret_code;
    }

    /* 2. record board type from CPLD */
    if((ret_code = bms_psu_serv_board_type_get(&bms_psu_board_type)) < 0) {
        return ret_code;
    }

    /* 3. initial cache to maintain psu statue and type. */
    bms_psu_serv_cache_init();

    /* 4. open message queue */
    if ((ret_code = bms_sys_serv_msq_open(mq_name, mq_desc)) < 0) {
        return ret_code;
    }

    /* 5. initial Mutexes */
    if ((ret_code = bms_psu_serv_mutex_init() < 0)) {
        return ret_code;
    }

    /* 6. set initial flag */
    bms_psu_init_done = 1;

    return ret_code;
}

/*
* FEATURE:
*   bms_psu_serv_cache_get
* PURPOSE:
*   psu service cache get
* PARAMETERS:
*   psu_number            (IN)  psu number
*   psu_status            (OUT) pointer of psu status
*   psu_type              (OUT) pointer of psu type
* RETURNS:
*/
void
bms_psu_serv_cache_get(unsigned int psu_number,
                       unsigned int* psu_status,
                       unsigned int* psu_type)
{
    pthread_mutex_lock(&bms_psu_st_cache_lock);
    *psu_status = bms_psu_status[psu_number];
    *psu_type = bms_psu_type[psu_number];
    pthread_mutex_unlock(&bms_psu_st_cache_lock);
}

/*
* FEATURE:
*   bms_psu_serv_intr_cache_get
* PURPOSE:
*   psu service interrupt cache get
* PARAMETERS:
*   intr_status         (OUT) pointer of psu type
* RETURNS:
*/
void
bms_psu_serv_intr_cache_get(unsigned int* intr_status)
{
    pthread_mutex_lock(&bms_psu_intr_cache_lock);
    memcpy(intr_status, bms_psu_intr_cache, sizeof(unsigned int) * BMS_PSU_NUM * BMS_PSU_INTR_NUM);
    pthread_mutex_unlock(&bms_psu_intr_cache_lock);
}


/*
* FEATURE:
*   bms_psu_serv_intr_cache_update
* PURPOSE:
*   psu service interrupt cache update
* PARAMETERS:
*   psu_number    (IN) psu number
*   psu_cause     (IN) psu update index
*   value         (IN) update value
* RETURNS:
*/
void
bms_psu_serv_intr_cache_update(unsigned int psu_number,
                               unsigned int psu_cause,
                               unsigned int value)
{
    pthread_mutex_lock(&bms_psu_intr_cache_lock);
    bms_psu_intr_cache[(psu_number * BMS_PSU_INTR_NUM) + psu_cause] = value;
    pthread_mutex_unlock(&bms_psu_intr_cache_lock);
}

/*
* FEATURE:
*   bms_psu_serv_intr_cache_clear
* PURPOSE:
*   psu specific interrupt cache clear
* PARAMETERS:
*   psu_number    (IN) psu number
* RETURNS:
*/
void
bms_psu_serv_intr_cache_clear(unsigned int psu_number)
{
    int i = 0;

    pthread_mutex_lock(&bms_psu_intr_cache_lock);

    for(i = 0; i < BMS_PSU_INTR_NUM; i++) {
        bms_psu_intr_cache[(psu_number * BMS_PSU_INTR_NUM) + i] = 0;
    }

    pthread_mutex_unlock(&bms_psu_intr_cache_lock);
}


/*
* FEATURE:
*   bms_psu_serv_power_led_by_cache_get
* PURPOSE:
*   get power led status from cache
* PARAMETERS:
*
* RETURNS:
*   BMS_PSU_POWER_LED_OFF or BMS_PSU_POWER_LED_AMBER or BMS_PSU_POWER_LED_GREEN,
*/
static int
bms_psu_serv_power_led_by_cache_get(void)
{
    int i = 0;
    unsigned int cache_status[BMS_PSU_NUM], cache_type[BMS_PSU_NUM];

    /* read value from cache */
    for(i = 0; i < BMS_PSU_NUM; i++) {
        bms_psu_serv_cache_get(i, &cache_status[i], &cache_type[i]);
    }

    for(i = 0; i < BMS_PSU_NUM; i++) {
        if((cache_status[i] == BMS_PSU_STATUS_NORMAL) ||
           (cache_status[i] == BMS_PSU_STATUS_FAULT)) {
            break;
        }
    }

    if(i == BMS_PSU_NUM) {
        return BMS_PSU_POWER_LED_OFF;
    }

    for(i = 0; i < BMS_PSU_NUM; i++) {
        if((cache_status[i] == BMS_PSU_STATUS_FAULT) ||
           (cache_type[i] != bms_psu_board_type)) {
            return BMS_PSU_POWER_LED_AMBER;
        }
    }

    return BMS_PSU_POWER_LED_GREEN;
}


/*
* FEATURE:
*   bms_psu_serv_cache_power_led_update
* PURPOSE:
*   update psu cache and power led
* PARAMETERS:
*   psu_number        (IN) psu number
*   psu_cause         (IN) cause of psu event
*   psu_type          (IN) psu type
* RETURNS:
*   success, compare the same return zero.
*   for other cases, negative errno is returned.
*/
static int
bms_psu_serv_cache_power_led_update(unsigned int psu_number,
                               unsigned int psu_cause,
                               unsigned int psu_type)
{
    int ret_code = 0;
    unsigned int pre_status, cur_status;

    pre_status = bms_psu_serv_power_led_by_cache_get();

    bms_psu_serv_cache_update(psu_number, psu_cause, psu_type);

    cur_status = bms_psu_serv_power_led_by_cache_get();

    if(cur_status == pre_status)
        return ret_code;

    if(cur_status == BMS_PSU_POWER_LED_GREEN) {
        if((ret_code = bms_psu_serv_power_led_set(BMS_PSU_POWER_LED_GREEN)) < 0) {
            return ret_code;
        }
    }else
    if(cur_status == BMS_PSU_POWER_LED_AMBER) {
        if((ret_code = bms_psu_serv_power_led_set(BMS_PSU_POWER_LED_AMBER)) < 0) {
            return ret_code;
        }
    }else{
        syslog(LOG_WARNING|LOG_USER,"[%s] Invaild vailed in cache\n", __FUNCTION__);
        return -EINVAL;
    }

    return ret_code;
}


/*
* FEATURE:
*   bms_psu_serv_find_serv_data_index
* PURPOSE:
*   find index of psu of serv_data
* PARAMETERS:
*   psu_number                (IN) psu number
* RETURNS:
*   success, this function returns value.
*   for other cases, negative errno is returned.
*/
static int
bms_psu_serv_find_serv_data_index(unsigned int psu_number)
{
    int i;

    for(i = 0; i < bms_sys_serv_data_num; i++) {
        if(strcmp(bms_sys_serv_data[i].name, bms_psu_serv_data[psu_number].name) == 0)
            return i;
    }

    syslog(LOG_WARNING|LOG_USER,"Can't find %s item index in bms_sys_serv_data\n", bms_psu_serv_data[psu_number].name);
    return -EINVAL;
}


/*
* FEATURE:
*   bms_psu_serv_intr_mask_set
* PURPOSE:
*   set psu intr mask
* PARAMETERS:
*   psu_number                (IN) psu number
*   value                     (IN) mask of setting value
* RETURNS:
*   success, this function returns zero.
*   for other cases, negative errno is returned.
*/
int
bms_psu_serv_intr_mask_set(unsigned int psu_number,
                           unsigned int value)
{
    int ret_code = 0, index;

    if((ret_code = bms_psu_serv_find_serv_data_index(psu_number)) < 0)
        return ret_code;

    index = ret_code;
    if((ret_code = bms_sys_serv_write(bms_sys_serv_data[index].intr_msk, value)) < 0) {
        return ret_code;
    }

    return ret_code;
}


/*
* FEATURE:
*   bms_psu_serv_intr_get
* PURPOSE:
*   set psu intr mask
* PARAMETERS:
*   psu_number                (IN) psu number
*   value                     (OUT) mask of setting value
* RETURNS:
*   success, this function returns zero.
*   for other cases, negative errno is returned.
*/
int
bms_psu_serv_intr_get(unsigned int psu_number,
                      unsigned int *value)
{
    int ret_code = 0, index;

    if((ret_code = bms_psu_serv_find_serv_data_index(psu_number)) < 0)
        return ret_code;

    index = ret_code;

    if((ret_code = bms_sys_serv_hex_read(bms_sys_serv_data[index].intr_src, value)) < 0) {
        return ret_code;
    }

    return ret_code;
}


/*
* FEATURE:
*   bms_psu_serv_psu_fault_datect
* PURPOSE:
*   detect psu fault cause
* PARAMETERS:
*   psu_number        (IN) psu number
*   psu_status        (OUT) pointer of psu status
*/
void
bms_psu_serv_psu_fault_datect(unsigned int psu_number,
                              unsigned int *psu_status)
{
    unsigned int intr_table[BMS_PSU_NUM * BMS_PSU_INTR_NUM], i;

    memset(intr_table, 0, sizeof(unsigned int) * BMS_PSU_NUM * BMS_PSU_INTR_NUM);

    bms_psu_serv_intr_cache_get(intr_table);

    for(i = 0; i < BMS_PSU_INTR_NUM; i++) {
        if(intr_table[i + (psu_number * BMS_PSU_INTR_NUM)] == BMS_PSU_SOURCE_INTR_ASSERTED){
            *psu_status = BMS_PSU_STATUS_FAULT;
            return;
        }
    }

    *psu_status = BMS_PSU_STATUS_NORMAL;
}

/*
* FEATURE:
*   bms_psu_serv_cause_log
* PURPOSE:
*   log of psu cause
* PARAMETERS:
*   psu_number           (IN) psu number
*   psu_cause            (IN) cause of psu status
* RETURNS:
*/
static void
bms_psu_serv_cause_log(unsigned int psu_number,
                       unsigned int psu_cause)
{
    unsigned int cache_type, cache_status;

    bms_psu_serv_cache_get(psu_number, &cache_status, &cache_type);

    if(psu_cause == BMS_PSU_STATUS_PRESENT) {
        if((cache_status == BMS_PSU_STATUS_NORMAL) ||
           (cache_status == BMS_PSU_STATUS_FAULT)) {
            syslog(LOG_DEBUG|LOG_USER,"The psu %u was no power.", psu_number + 1);
        }else
        if(cache_status == BMS_PSU_STATUS_ABSENT) {
            syslog(LOG_DEBUG|LOG_USER,"The psu %u was present, but no power.", psu_number + 1);
        }else{
            syslog(LOG_WARNING|LOG_USER,"LOG error, unknown psu_cause in psu %u\n", psu_number + 1);
        }
    }else
    if(psu_cause == BMS_PSU_STATUS_NORMAL) {
        if(cache_status == BMS_PSU_STATUS_ABSENT) {
            syslog(LOG_DEBUG|LOG_USER,"The psu %u was present, and work normal.", psu_number + 1);
        }else
        if(cache_status == BMS_PSU_STATUS_PRESENT) {
            syslog(LOG_DEBUG|LOG_USER,"The psu %u has power.", psu_number + 1);
        }else
        if(cache_status == BMS_PSU_STATUS_FAULT) {
            /* Don't show any log */
        }else{
            syslog(LOG_WARNING|LOG_USER,"LOG error, unknown psu_cause in psu %u\n", psu_number + 1);
        }
    }else
    if(psu_cause == BMS_PSU_STATUS_FAULT) {
        syslog(LOG_WARNING|LOG_USER,"The psu %u was fault\n", psu_number + 1);
    }else
    if(psu_cause == BMS_PSU_STATUS_ABSENT) {
        syslog(LOG_DEBUG|LOG_USER,"The psu %u was non present\n", psu_number + 1);
    }else{
        syslog(LOG_WARNING|LOG_USER,"LOG error, unknown psu_cause in psu %u\n", psu_number + 1);
    }
}


/*
* FEATURE:
*   bms_psu_serv_intr_log
* PURPOSE:
*   log of psu intrrupt
* PARAMETERS:
*   psu_number           (IN) psu number
*   psu_cause            (IN) psu interrupt cause
* RETURNS:
*/
void
bms_psu_serv_intr_log(unsigned int psu_number,
                       unsigned int psu_cause)
{
    switch (psu_cause) {
        case BMS_PSU_VOUT_OV_FAULT:
            syslog(LOG_WARNING|LOG_USER,"The psu %u is fault by over output voltage.\n", psu_number + 1);
            break;

        case BMS_PSU_VOUT_UV_FAULT:
            syslog(LOG_WARNING|LOG_USER,"The psu %u is fault by under output voltage.\n", psu_number + 1);
            break;

        case BMS_PSU_IOUT_OC_FAULT:
            syslog(LOG_WARNING|LOG_USER,"The psu %u is fault by over currents.\n", psu_number + 1);
            break;

        case BMS_PSU_IOUT_OC_WARNING:
            syslog(LOG_WARNING|LOG_USER,"The psu %u is warning by over currents.\n", psu_number + 1);
            break;

        case BMS_PSU_OT_FAULT:
            syslog(LOG_WARNING|LOG_USER,"The psu %u is fault by over temperature.\n", psu_number + 1);
            break;

        case BMS_PSU_OT_WARNING:
            syslog(LOG_WARNING|LOG_USER,"The psu %u is warning by over temperature.\n", psu_number + 1);
            break;

        case BMS_PSU_VIN_UV_WARNING:
            syslog(LOG_WARNING|LOG_USER,"The psu %u is warning by under input voltage.\n", psu_number + 1);
            break;

        case BMS_PSU_VIN_UV_FAULT:
            syslog(LOG_WARNING|LOG_USER,"The psu %u is fault by under input voltage.\n", psu_number + 1);
            break;

        case BMS_PSU_FAN1_FAULT:
            syslog(LOG_WARNING|LOG_USER,"The psu %u is fault.\n", psu_number + 1);
            break;

        case BMS_PSU_FAN1_WARNING:
            syslog(LOG_WARNING|LOG_USER,"The psu %u is warning.\n", psu_number + 1);
            break;

        default:
            syslog(LOG_WARNING|LOG_USER,"The psu %u receive unknown item %d.\n", psu_number + 1, psu_cause);
            break;
    }
}

/*
* FEATURE:
*   bms_psu_serv_intr_recovery_log
* PURPOSE:
*   log of psu recovery intrrupt
* PARAMETERS:
*   psu_number           (IN) psu number
*   psu_cause            (IN) psu interrupt cause
* RETURNS:
*/
void
bms_psu_serv_intr_recovery_log(unsigned int psu_number,
                               unsigned int psu_cause)
{
    switch (psu_cause) {
        case BMS_PSU_VOUT_OV_FAULT:
            syslog(LOG_WARNING|LOG_USER,"The psu %u over output voltage is recovery.\n", psu_number + 1);
            break;

        case BMS_PSU_VOUT_UV_FAULT:
            syslog(LOG_WARNING|LOG_USER,"The psu %u under output voltage is recovery.\n", psu_number + 1);
            break;

        case BMS_PSU_IOUT_OC_FAULT:
            syslog(LOG_WARNING|LOG_USER,"The psu %u over currents fault is recovery.\n", psu_number + 1);
            break;

        case BMS_PSU_IOUT_OC_WARNING:
            syslog(LOG_WARNING|LOG_USER,"The psu %u over currents warning is recovery.\n", psu_number + 1);
            break;

        case BMS_PSU_OT_FAULT:
            syslog(LOG_WARNING|LOG_USER,"The psu %u over temperature fault is recovery.\n", psu_number + 1);
            break;

        case BMS_PSU_OT_WARNING:
            syslog(LOG_WARNING|LOG_USER,"The psu %u over temperature warning is recovery.\n", psu_number + 1);
            break;

        case BMS_PSU_VIN_UV_WARNING:
            syslog(LOG_WARNING|LOG_USER,"The psu %u under input voltage warning is recovery.\n", psu_number + 1);
            break;

        case BMS_PSU_VIN_UV_FAULT:
            syslog(LOG_WARNING|LOG_USER,"The psu %u under input voltage fault is recovery .\n", psu_number + 1);
            break;

        case BMS_PSU_FAN1_FAULT:
            syslog(LOG_WARNING|LOG_USER,"The psu %u fan fault is recovery.\n", psu_number + 1);
            break;

        case BMS_PSU_FAN1_WARNING:
            syslog(LOG_WARNING|LOG_USER,"The psu %u fan warning is recovery.\n", psu_number + 1);
            break;

        default:
            syslog(LOG_WARNING|LOG_USER,"The psu %u receive unknown item %d recovery.\n", psu_number + 1, psu_cause);
            break;
    }

}

/*
* FEATURE:
*   bms_psu_serv_board_type_comp
* PURPOSE:
*   compare psu type is the same with board type
* PARAMETERS:
*   psu_type           (IN) psu type
* RETURNS:
*/
static int
bms_psu_serv_board_type_comp(unsigned int psu_type)
{

    if(bms_psu_board_type == psu_type) {
        return 0;
    }

    return -EINVAL;
}

/*
* FEATURE:
*   bms_psu_serv_type_log
* PURPOSE:
*   log of psu the is the same with board type
* PARAMETERS:
*   psu_number         (IN) psu number
*   psu_type           (IN) psu type
* RETURNS:
*/
static void
bms_psu_serv_type_log(unsigned int psu_number,
                      unsigned int psu_type)
{
    if((bms_psu_serv_board_type_comp(psu_type) < 0))
        syslog(LOG_WARNING|LOG_USER,"The psu %u type was wrong\n", psu_number + 1);
}


/*
* FEATURE:
*   bms_psu_servd
* PURPOSE:
*   service to handle message queue event of cpu temperature
* PARAMETERS:
*   args                (IN) message queue name
* RETURNS:
*   open success, this function will wait for message queue.
*   for other cases, will exit this program.
*/
void*
bms_psu_servd(void *args)
{
    char *mq_name = (char*)args;
    mqd_t mq_desc;
    bms_sys_serv_mq_data_t msg;
    int ret_code;
    unsigned int psu_number, psu_type, psu_status, pg_status;
    unsigned int psu_pg;

    /* Open message queue */
    if (bms_psu_serv_init(mq_name, &mq_desc) < 0) {
        goto quit;
    }

    while (1) {
        /* Wait for message queue */
        if (mq_receive(mq_desc, (char*)&msg, sizeof(msg), 0) < 0) {
            ret_code = errno;
            syslog(LOG_WARNING|LOG_USER,"Failed to receive message from %s (%s)\n", mq_name, strerror(ret_code));
            goto quit;
        }

        switch (msg.serv_type) {
            case SERV_TYPE_RX_INTR:
                psu_number = msg.number;

                bms_psu_serv_intr_cache_update(psu_number, msg.cause, BMS_PSU_SOURCE_INTR_ASSERTED);

                bms_psu_serv_intr_log(psu_number, msg.cause);

                bms_psu_serv_cache_power_led_update(psu_number, BMS_PSU_STATUS_FAULT, -1);
                break;

            case SERV_TYPE_PSU_NORMAL:
                psu_number = msg.number;
PSU_NORMAL:

                if(bms_psu_driver_init[psu_number] == BMS_PSU_DRIVER_UNINIT){
                    if ((ret_code = bms_psu_serv_driver_plugin(psu_number)) < 0) {
                        break;
                    }
                }

                if((ret_code = bms_psu_serv_type_get(psu_number, &psu_type)) < 0) {
                    break;
                }

                bms_psu_serv_psu_fault_datect(psu_number, &psu_status);

                if(psu_status == BMS_PSU_STATUS_FAULT) {
                    bms_psu_serv_cache_update(psu_number, BMS_PSU_STATUS_NORMAL, psu_type);
                    bms_psu_serv_type_log(psu_number, psu_type);
                }else{
                    bms_psu_serv_cause_log(psu_number, BMS_PSU_STATUS_NORMAL);
                    bms_psu_serv_type_log(psu_number, psu_type);
                    bms_psu_serv_cache_power_led_update(psu_number, BMS_PSU_STATUS_NORMAL, psu_type);
                }

                break;

            case SERV_TYPE_PSU_PRESENT:
                psu_number = msg.number;

                if ((ret_code = bms_psu_serv_power_status_get(&pg_status)) < 0) {
                    break;
                }

                psu_pg = ((pg_status & (1 << (bms_psu_serv_data[psu_number].pg_offset))) > 0) ? BMS_PSU_PG_FAILED : BMS_PSU_PG_GOOD;

                if(psu_pg == BMS_PSU_PG_GOOD) {
                    goto PSU_NORMAL;
                }else{
                    bms_psu_serv_cause_log(psu_number, BMS_PSU_STATUS_PRESENT);

                    bms_psu_serv_cache_power_led_update(psu_number, BMS_PSU_STATUS_PRESENT, -1);
                }
                break;

            case SERV_TYPE_PSU_ABSENT:
                psu_number = msg.number;

                bms_psu_serv_intr_cache_clear(psu_number);

                bms_psu_serv_cause_log(psu_number, BMS_PSU_STATUS_ABSENT);
                bms_psu_serv_cache_power_led_update(psu_number, BMS_PSU_STATUS_ABSENT, -1);

                break;

            case SERV_TYPE_PSU_INTR_RECOVERY:
                psu_number = msg.number;
                bms_psu_serv_intr_cache_update(psu_number, msg.cause, BMS_PSU_SOURCE_INTR_DEASSERTED);

                bms_psu_serv_intr_recovery_log(psu_number, msg.cause);

                bms_psu_serv_psu_fault_datect(psu_number, &psu_status);

                if(psu_status == BMS_PSU_STATUS_FAULT) {
                    bms_psu_serv_cache_power_led_update(psu_number, BMS_PSU_STATUS_FAULT, -1);
                }
                else if(psu_status == BMS_PSU_STATUS_NORMAL) {
                    goto PSU_NORMAL;
                }else{
                    syslog(LOG_WARNING|LOG_USER,"Receive psu %d INTR_RECOVERY message, but can't find next status\n", psu_number);
                }

                break;

            default:
                syslog(LOG_WARNING|LOG_USER,"Receive an unknown message %d from %s\n", msg.serv_type, mq_name);
                break;
        }
    }

quit:
    pthread_exit(NULL);
}
