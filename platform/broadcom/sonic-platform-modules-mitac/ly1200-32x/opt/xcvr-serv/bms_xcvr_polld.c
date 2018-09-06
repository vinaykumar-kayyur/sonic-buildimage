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

#include <fcntl.h>
#include <stdio.h>
#include <syslog.h>
#include <stdlib.h>
#include <errno.h>
#include <stdarg.h>
#include <sched.h>
#include <sys/msg.h>
#include <sys/stat.h>
#include <mqueue.h>
#include <string.h>
#include <pthread.h>
#include "bms_xcvr_servd.h"
#include <unistd.h>

pthread_mutex_t bms_xcvr_data_lock;
pthread_t polld_tid;

/* Set default value based on CPLD spec */
unsigned int bms_xcvr_present_cache_bmap = 0xFFFFFFFF;/* ~PRESENT_EN */
unsigned int bms_xcvr_reset_cache_bmap = 0x0;/* RST_EN */
unsigned int bms_xcvr_modsel_cache_bmap = 0xFFFFFFFF;/* ~MODSEL_EN */
unsigned int bms_xcvr_intr_msk_cache_bmap = 0x0;/* INTR_MASK_EN */
unsigned int bms_xcvr_init_done_cache_bmap = 0x0;/* ~INIT_DONE_EN */
unsigned int bms_xcvr_lpmode_cache_bmap = 0x0;/* LPMODE_DIS */

/*
 * FEATURE:
 *   bms_xcvr_pin_read
 * PURPOSE:
 *   read pin status from file of sysfs
 * PARAMETERS:
 *   filename           (IN) file path in the sysfs
 *   value              (OUT) pointer of current value buffer
 * RETURNS:
 *   open success, this function returns .
 *   for other cases, negative errno is returned.
 */
int
bms_xcvr_pin_read(char *filename,
                  unsigned int *value)
{
    char buf[32] = {0};
    int fd, ret_code = 0, buf_size = sizeof(buf);
    ssize_t count;

    /* Open xcvr pin file */
    if ((fd = open(filename, O_RDONLY)) < 0) {
        ret_code = errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to open %s (%s)\n", filename, strerror(ret_code));
        return -ret_code;
    }

    /* Read pin file */
    if ((count = read(fd, buf, buf_size)) != (-1)) {
        *value = strtol(buf, NULL, 16);
    }
    else {
        ret_code = (count >= 0) ? EIO : errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to read %s (%s)\n", filename, strerror(ret_code));
        close(fd);
        return -ret_code;
    }

    close(fd);
    return ret_code;
}

/*
 * FEATURE:
 *   bms_xcvr_pin_write
 * PURPOSE:
 *   write value to file of sysfs
 * PARAMETERS:
 *   filename           (IN) file path in the sysfs
 *   value              (IN) new register value
 * RETURNS:
 *   open success, this function returns .
 *   for other cases, negative errno is returned.
 */
int
bms_xcvr_pin_write(char *filename,
                   unsigned int value)
{
    char buf[3];
    int fd, ret_code = 0, buf_size = sizeof(buf);
    ssize_t count;

    /* Open file */
    if ((fd = open(filename, O_WRONLY)) < 0) {
        ret_code = errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to open %s (%s)\n", filename, strerror(ret_code));
        return -ret_code;
    }

    /* Write file */
    snprintf(buf, buf_size, "%x", value);
    if ((count = write(fd, buf, buf_size)) != (-1)) {;}
    else {
        ret_code = (count >= 0) ? EIO : errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to write %s (%s)\n", filename, strerror(ret_code));
        close(fd);
        return -ret_code;
    }

    close(fd);
    return ret_code;
}

/*
 * FEATURE:
 *   bms_xcvr_data_read
 * PURPOSE:
 *   read pin status from data base
 * PARAMETERS:
 *   pin_num            (IN) the number means different pin name
 *   value              (OUT) pointer of current value buffer
 * RETURNS:
 *   no
 */
void
bms_xcvr_data_read(int pin_num,
                   unsigned int *value)
{
    switch (pin_num) {
        case XCVR_PRESENT:
            *value = bms_xcvr_present_cache_bmap;
            break;
        case XCVR_MODSEL:
            *value = bms_xcvr_modsel_cache_bmap;
            break;
        case XCVR_RESET:
            *value = bms_xcvr_reset_cache_bmap;
            break;
        case XCVR_INTR_MSK:
            *value = bms_xcvr_intr_msk_cache_bmap;
            break;
        case XCVR_INIT_DONE:
            *value = bms_xcvr_init_done_cache_bmap;
            break;
        case XCVR_LPMODE:
            *value = bms_xcvr_lpmode_cache_bmap;
            break;
        default:
            *value = 0;
            break;
    }
}

/*
 * FEATURE:
 *   bms_xcvr_data_write
 * PURPOSE:
 *   write new value to data base
 * PARAMETERS:
 *   pin_num            (IN) the number means different pin name
 *   value              (IN) new register value
 * RETURNS:
 *   no.
 */
void
bms_xcvr_data_write(int pin_num,
                    unsigned int value)
{
    switch (pin_num) {
        case XCVR_PRESENT:
            bms_xcvr_present_cache_bmap = value;
            break;
        case XCVR_MODSEL:
            bms_xcvr_modsel_cache_bmap = value;
            break;
        case XCVR_RESET:
            bms_xcvr_reset_cache_bmap = value;
            break;
        case XCVR_INTR_MSK:
            bms_xcvr_intr_msk_cache_bmap = value;
            break;
        case XCVR_INIT_DONE:
            bms_xcvr_init_done_cache_bmap = value;
            break;
        case XCVR_LPMODE:
            bms_xcvr_lpmode_cache_bmap = value;
            break;
        default:
            break;
    }
}

/*
 * FEATURE:
 *   bms_xcvr_pin_bmap_write
 * PURPOSE:
 *   write bmap to file of sysfs
 * PARAMETERS:
 *   pin_num            (IN) the number means different pin name
 *   value              (IN) new register value
 * RETURNS:
 *   open success, this function returns .
 *   for other cases, negative errno is returned.
 */
int
bms_xcvr_pin_bmap_write(int pin_num,
                        unsigned int value)
{
    int ret_code = 0, i;
    unsigned int val = 0;

    for(i = 0; i < xcvrirq_data_num; i++) {
        if (xcvrirq_data[i].present) {
            val = (value >> i) & 0xff;
            switch (pin_num) {
                case XCVR_PRESENT:
                    ret_code = bms_xcvr_pin_write(xcvrirq_data[i].present, val);
                    break;
                case XCVR_MODSEL:
                    ret_code = bms_xcvr_pin_write(xcvrirq_data[i].modsel, val);
                    break;
                case XCVR_RESET:
                    ret_code = bms_xcvr_pin_write(xcvrirq_data[i].reset, val);
                    break;
                case XCVR_INTR_MSK:
                    ret_code = bms_xcvr_pin_write(xcvrirq_data[i].intr_msk, val);
                    break;
                case XCVR_INTR_SRC:
                    ret_code = bms_xcvr_pin_write(xcvrirq_data[i].intr_src, val);
                    break;
                case XCVR_LPMODE:
                    ret_code = bms_xcvr_pin_write(xcvrirq_data[i].lpmode, val);
                    break;
                default:
                    ret_code = -ENOTSUP;
                    break;
            }
            if (ret_code < 0)
                goto quit;
        }
    }
quit:
    return ret_code;
}

/*
 * FEATURE:
 *   bms_xcvr_pin_bmap_modify
 * PURPOSE:
 *   write bmap to file of sysfs if the value is modified
 * PARAMETERS:
 *   pin_num            (IN) the number means different pin name
 *   value              (IN) new register value
 *   old_value          (IN) last register value
 * RETURNS:
 *   open success, this function returns .
 *   for other cases, negative errno is returned.
 */
int
bms_xcvr_pin_bmap_modify(int pin_num,
                         unsigned int value,
                         unsigned int old_value)
{
    int ret_code = 0, i;
    unsigned int val = 0;

    for(i = 0; i < xcvrirq_data_num; i++) {
        if (xcvrirq_data[i].present && (((old_value ^ value) >> i) & 0xff) ) {
            val = (value >> i) & 0xff;
            switch (pin_num) {
                case XCVR_PRESENT:
                    ret_code = bms_xcvr_pin_write(xcvrirq_data[i].present, val);
                    break;
                case XCVR_MODSEL:
                    ret_code = bms_xcvr_pin_write(xcvrirq_data[i].modsel, val);
                    break;
                case XCVR_RESET:
                    ret_code = bms_xcvr_pin_write(xcvrirq_data[i].reset, val);
                    break;
                case XCVR_INTR_MSK:
                    ret_code = bms_xcvr_pin_write(xcvrirq_data[i].intr_msk, val);
                    break;
                case XCVR_INTR_SRC:
                    ret_code = bms_xcvr_pin_write(xcvrirq_data[i].intr_src, val);
                    break;
                case XCVR_LPMODE:
                    ret_code = bms_xcvr_pin_write(xcvrirq_data[i].lpmode, val);
                    break;
                default:
                    ret_code = -ENOTSUP;
                    break;
            }
            if (ret_code < 0)
                goto quit;
        }
    }
quit:
    return ret_code;
}

/*
 * FEATURE:
 *   bms_xcvr_polld
 * PURPOSE:
 *   poll present pin for each port
 * PARAMETERS:
 *   args               (IN) NULL
 * RETURNS:
 *   No.
 */
void* bms_xcvr_polld(void *args)
{
    int ret_code = 0, i = *(int*)args;
    unsigned int present_bmap, present_cache_bmap, present_switch_bmap;
    unsigned int reset_bmap, reset_cache_bmap;
    unsigned int modsel_bmap, modsel_cache_bmap;
    unsigned int xcvr_insert_bmap, xcvr_remove_bmap, value, init_done_cache_bmap;
#if XCVR_LPMODE_PIN_USE == 1 /* LPMODE is reserved */
    unsigned int lpmode_bmap, lpmode_cache_bmap;
#endif

    while (1) {

        /* Detect xcvr present pin */
        /* 1. read present pin of all xcvr */
        for (i = 0, present_bmap = 0; i < xcvrirq_data_num; i++) {
            if (xcvrirq_data[i].present) {
                if ((ret_code = bms_xcvr_pin_read(xcvrirq_data[i].present, &value)) < 0) {
                    goto quit;
                }
                present_bmap |= (value << i);
            }
        }

        /* 2. read present,reset,modsel status from database*/
        pthread_mutex_lock(&bms_xcvr_data_lock);
        bms_xcvr_data_read(XCVR_PRESENT, &present_cache_bmap);
        bms_xcvr_data_read(XCVR_RESET, &reset_cache_bmap);
        bms_xcvr_data_read(XCVR_MODSEL, &modsel_cache_bmap);
        bms_xcvr_data_read(XCVR_INIT_DONE, &init_done_cache_bmap);
#if XCVR_LPMODE_PIN_USE == 1 /* LPMODE is reserved */
        bms_xcvr_data_read(XCVR_LPMODE, &lpmode_cache_bmap);
#endif
        pthread_mutex_unlock(&bms_xcvr_data_lock);

        reset_bmap = reset_cache_bmap;
        modsel_bmap = modsel_cache_bmap;
#if XCVR_LPMODE_PIN_USE == 1 /* LPMODE is reserved */
        lpmode_bmap = lpmode_cache_bmap;
#endif

        /* 3. mark present_switch_bmap if switching present pin (present <-> absent)*/
        present_switch_bmap = present_bmap ^ present_cache_bmap;

        /* Handle present_switch_bmap */
        if (present_switch_bmap) {

            /* 1. filter to xcvr_insert_bmap and xcvr_remove_bmap */
            xcvr_insert_bmap = (present_switch_bmap & ~present_bmap);
            xcvr_remove_bmap = (present_switch_bmap & present_bmap);

            /* 2. deassert reset pin for xcvr insert port */
            bms_xcvr_bmap_modify( &reset_bmap, xcvr_insert_bmap, ~RST_EN);
            /* 3. assert reset pin for xcvr remove port */
            bms_xcvr_bmap_modify( &reset_bmap, xcvr_remove_bmap, RST_EN);

            /* 4. For suppot DAC to enable modsel for xcvr insert port */
            bms_xcvr_bmap_modify( &modsel_bmap, xcvr_insert_bmap, MODSEL_EN);
            /* 4. No matter what status , set unmodsel for remove port */
            bms_xcvr_bmap_modify( &modsel_bmap, xcvr_remove_bmap, ~MODSEL_EN);

#if XCVR_LPMODE_PIN_USE == 1 /* LPMODE is reserved */
            /* 4. No matter what status , set low power mode for remove port */
            bms_xcvr_bmap_modify( &lpmode_bmap, xcvr_remove_bmap, ~LPMODE_DIS);
#endif

            /* 5. Cancel init_done port for xcvr remove port */
            init_done_cache_bmap &= ~xcvr_remove_bmap;

            /* Write present,reset,modsel,init_done pin status of present switch port to database*/
            pthread_mutex_lock(&bms_xcvr_data_lock);
            if((ret_code = bms_xcvr_pin_bmap_modify(XCVR_RESET, reset_bmap, reset_cache_bmap)) < 0) {
                goto quit;
            }
            if((ret_code = bms_xcvr_pin_bmap_modify(XCVR_MODSEL, modsel_bmap, modsel_cache_bmap)) < 0) {
                goto quit;
            }
#if XCVR_LPMODE_PIN_USE == 1 /* LPMODE is reserved */
            if((ret_code = bms_xcvr_pin_bmap_modify(XCVR_LPMODE, lpmode_bmap, lpmode_cache_bmap)) < 0) {
                goto quit;
            }
            bms_xcvr_data_write(XCVR_LPMODE, lpmode_bmap);
#endif
            bms_xcvr_data_write(XCVR_PRESENT, present_bmap);
            bms_xcvr_data_write(XCVR_RESET, reset_bmap);
            bms_xcvr_data_write(XCVR_MODSEL, modsel_bmap);
            bms_xcvr_data_write(XCVR_INIT_DONE, init_done_cache_bmap);
            pthread_mutex_unlock(&bms_xcvr_data_lock);
        }
        sleep(1);
    }

quit:
    syslog(LOG_DEBUG|LOG_USER,"Quit thread from %s function (%s)\n", __func__, strerror(ret_code));
    pthread_exit(NULL);
}
