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
#include <unistd.h>
#include "bms_psu_servd.h"
#include "bms_sys_serv_common.h"


/*
* FEATURE:
*   bms_psu_poll_msq_open
* PURPOSE:
*   open POSIX message queue
* PARAMETERS:
*   qname                (IN) message queue name
*   mqd                  (OUT) pointer of message queue description
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
int
bms_psu_poll_msq_open(const char *qname,
                      mqd_t *mqd)
{
    int flags = (O_WRONLY | O_NONBLOCK), ret_code = 0;

    /* create POSIX message queue */
    if ((*mqd = mq_open(qname, flags)) == (mqd_t)-1) {
        ret_code = errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to open message queue %s (%s)\n", qname, strerror(ret_code));
    }

    return -ret_code;
}


/*
* FEATURE:
*   bms_psu_poll_init
* PURPOSE:
*   initial all
* PARAMETERS:
*   qname                (IN) message queue name
*   mqd                  (OUT) pointer of message queue description
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
int
bms_psu_poll_init(char *mq_name,
                  mqd_t *mq_desc)
{
    int ret_code = 0;

    /* open message queue*/
    if ((ret_code = bms_psu_poll_msq_open(mq_name, mq_desc)) < 0) {
        return ret_code;
    }

    return ret_code;
}


/*
* FEATURE:
*   bms_psu_poll_detect_psu_status
* PURPOSE:
*   datect psu status is present or non present
* PARAMETERS:
*   present_bmap                  (OUT) pointer of present bmap
*   nonpresent_bmap               (OUT) pointer of non-present bmap
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
int
bms_psu_poll_detect_module_status(unsigned int *present_pg_bmap,
                                  unsigned int *present_bmap,
                                  unsigned int *nonpresent_bmap,
                                  unsigned int *intr_table,
                                  unsigned int *intr_recovery_table)
{
    int ret_code = 0, i;
    unsigned int ps_pg_status;
    unsigned int cache_status[BMS_PSU_NUM], cache_type[BMS_PSU_NUM],psu_present[BMS_PSU_NUM], psu_power_good[BMS_PSU_NUM];
    unsigned int intr_status[BMS_PSU_NUM * BMS_PSU_INTR_NUM], intr_cache[BMS_PSU_NUM * BMS_PSU_INTR_NUM];

    memset(intr_status, 0, sizeof(unsigned int) * BMS_PSU_NUM * BMS_PSU_INTR_NUM);
    memset(intr_cache, 0, sizeof(unsigned int) * BMS_PSU_NUM * BMS_PSU_INTR_NUM);

    /* read  pg */
    if((ret_code = bms_psu_serv_power_status_get(&ps_pg_status)) < 0) {
        return ret_code;
    }

    for(i = 0; i < BMS_PSU_NUM; i++) {
        bms_psu_serv_cache_get(i, &cache_status[i], &cache_type[i]);
        psu_present[i] = ((ps_pg_status & (1 << (bms_psu_serv_data[i].ps_offset))) > 0) ? BMS_PSU_PS_NONPRESENT : BMS_PSU_PS_PRESENT;
        psu_power_good[i] = ((ps_pg_status & (1 << (bms_psu_serv_data[i].pg_offset))) > 0) ? BMS_PSU_PG_FAILED : BMS_PSU_PG_GOOD;
    }

    /* read interrupt cache */
    bms_psu_serv_intr_cache_get(intr_cache);

    /* read interrupt from file system */
    for(i = 0; i < BMS_PSU_NUM * BMS_PSU_INTR_NUM; i++){
        if((cache_status[i / BMS_PSU_INTR_NUM] != BMS_PSU_STATUS_NORMAL) &&
           (cache_status[i / BMS_PSU_INTR_NUM] != BMS_PSU_STATUS_FAULT)) {
            continue;
        }
        if((ret_code = bms_sys_serv_dec_read(bms_psu_serv_data[i / BMS_PSU_INTR_NUM].intr_src[i % BMS_PSU_INTR_NUM], &intr_status[i])) < 0){
            return ret_code;
        }
    }

    for(i = 0; i < BMS_PSU_NUM; i++) {
        if(cache_status[i] == BMS_PSU_STATUS_ABSENT) {
            if(psu_present[i] == BMS_PSU_PS_PRESENT) {
                /* case 1 current status is absent, and have a psu plug in */
                *present_bmap |= (1 << i);
            }
            continue;
        }

        if(cache_status[i] == BMS_PSU_STATUS_PRESENT) {
            if(psu_present[i] == BMS_PSU_PS_PRESENT) {
                if(psu_power_good[i] == BMS_PSU_PG_GOOD) {
                    /* case 2 current status is present, and detect power good now */
                    *present_pg_bmap |= (1 << i);
                }
            }else
            if(psu_present[i] == BMS_PSU_PS_NONPRESENT) {
                /* case 3 current status is is present, and detect non present */
                *nonpresent_bmap |= (1 << i);
            }
            continue;
        }

        if((cache_status[i] == BMS_PSU_STATUS_NORMAL) ||
           (cache_status[i] == BMS_PSU_STATUS_FAULT)) {
            if(psu_present[i] == BMS_PSU_PS_NONPRESENT) {
                /* case 4 current status is is normal or fault, and detect non present */
                *nonpresent_bmap |= (1 << i);
            }else
            if(psu_present[i] == BMS_PSU_PS_PRESENT) {
                if(psu_power_good[i] == BMS_PSU_PG_FAILED) {
                    /* case 5 current status is is normal or fault, and detect non power good */
                    *present_bmap |= (1 << i);
                }
            }
            continue;
        }

        syslog(LOG_DEBUG|LOG_USER,"[%s] Unknown cache status %u and present status %u\n", __FUNCTION__, cache_status[i], psu_present[i]);

    }

    for(i = 0; i < BMS_PSU_NUM * BMS_PSU_INTR_NUM; i++){
        if(intr_status[i] == intr_cache[i])
            continue;

        if(psu_power_good[i / BMS_PSU_INTR_NUM] == BMS_PSU_PG_FAILED){
            continue;
        }

        if(intr_status[i] == BMS_PSU_SOURCE_INTR_ASSERTED){
            intr_table[i] = 1;
        }
        else{
            intr_recovery_table[i] = 1;
        }
    }

    return ret_code;
}

/*
* FEATURE:
*   bms_psu_poll_msq_send
* PURPOSE:
*   send POSIX message queue
* PARAMETERS:
*   msg                  (IN) message of send data
*   mqd                  (OUT) pointer of message queue description
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
int
bms_psu_poll_msq_send(bms_sys_serv_mq_data_t* msg,
                      mqd_t *mqd)
{
    int ret_code;

    if (mq_send(*mqd, (char*)msg, sizeof(*msg), 0) < 0) {
        ret_code = errno;
        if (ret_code == EAGAIN) {
            syslog(LOG_WARNING|LOG_USER,"Message queue %s is full\n", msg->serv_name);
        }
        else {
            syslog(LOG_WARNING|LOG_USER,"Failed to send message to %s (%s)\n", msg->serv_name, strerror(ret_code));
        }
    }

    return -ret_code;
}


/*
* FEATURE:
*   bms_psu_polld
* PURPOSE:
*   bms psu polling daemon
* PARAMETERS:
*   args                (IN) input value(message name)
* RETURNS:
*   The process will always polling psu module.
*/
void*
bms_psu_polld(void *args)
{
    char *mq_name = (char*)args;
    mqd_t mq_desc;
    int ret_code = 0, i;

    bms_sys_serv_mq_data_t msg;
    unsigned int present_pg_bmap = 0, nonpresent_bmap = 0;
    unsigned int present_bmap = 0;
    unsigned int intr_table[BMS_PSU_NUM * BMS_PSU_INTR_NUM], intr_recovery_table[BMS_PSU_NUM * BMS_PSU_INTR_NUM];

    msg.serv_name = mq_name;

    if((ret_code = bms_psu_poll_init(mq_name, &mq_desc)) < 0) {
        goto quit;
    }

    while(!bms_psu_init_done) {
        sleep(1);
    }

    while(1) {
        present_pg_bmap = 0;
        nonpresent_bmap = 0;
        present_bmap = 0;
        memset(intr_table, 0, sizeof(unsigned int) * BMS_PSU_NUM * BMS_PSU_INTR_NUM);
        memset(intr_recovery_table, 0, sizeof(unsigned int) * BMS_PSU_NUM * BMS_PSU_INTR_NUM);

        if((ret_code = bms_psu_poll_detect_module_status(&present_pg_bmap, &present_bmap,
                                                         &nonpresent_bmap, intr_table, intr_recovery_table)) < 0) {
            goto wait;
        }


        if(present_pg_bmap != 0) {
            for(i = 0; i < BMS_PSU_NUM; i++) {
                if(present_pg_bmap & (1 << i)) {
                    msg.serv_type = SERV_TYPE_PSU_NORMAL;
                    msg.number = i;
                    bms_psu_poll_msq_send(&msg, &mq_desc);
                }
            }
        }

        if(present_bmap != 0) {
            for(i = 0; i < BMS_PSU_NUM; i++) {
                if(present_bmap & (1 << i)) {
                    msg.serv_type = SERV_TYPE_PSU_PRESENT;
                    msg.number = i;
                    bms_psu_poll_msq_send(&msg, &mq_desc);
                }
            }
        }

        if(nonpresent_bmap != 0) {
            for(i = 0; i < BMS_PSU_NUM; i++) {
                if(nonpresent_bmap & (1 << i)) {
                    msg.serv_type = SERV_TYPE_PSU_ABSENT;
                    msg.number = i;
                    bms_psu_poll_msq_send(&msg, &mq_desc);
                }
            }
        }

        for(i = 0; i < BMS_PSU_NUM * BMS_PSU_INTR_NUM; i++) {
            if(intr_table[i] == 1) {
                msg.serv_type = SERV_TYPE_RX_INTR;
                msg.number = i / BMS_PSU_INTR_NUM;
                msg.cause = i % BMS_PSU_INTR_NUM;
                bms_psu_poll_msq_send(&msg, &mq_desc);
            }
        }

        for(i = 0; i < BMS_PSU_NUM * BMS_PSU_INTR_NUM; i++) {
            if(intr_recovery_table[i] == 1) {
                msg.serv_type = SERV_TYPE_PSU_INTR_RECOVERY;
                msg.number = i / BMS_PSU_INTR_NUM;
                msg.cause = i % BMS_PSU_INTR_NUM;
                bms_psu_poll_msq_send(&msg, &mq_desc);
            }
        }

wait:
        sleep(1);
    }

quit:
    pthread_exit(NULL);
}
