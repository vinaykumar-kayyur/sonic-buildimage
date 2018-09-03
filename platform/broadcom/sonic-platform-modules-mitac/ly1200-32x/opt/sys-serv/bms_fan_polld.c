#include <syslog.h>
#include <errno.h>
#include <mqueue.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>

#include "bms_sys_serv_common.h"
#include "bms_fan_servd.h"

/*
* FEATURE:
*   bms_fan_poll_msq_open
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
bms_fan_poll_msq_open(const char *qname,
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
*   bms_fan_poll_msq_send
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
bms_fan_poll_msq_send(bms_sys_serv_mq_data_t* msg,
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
*   bms_fan_poll_init
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
bms_fan_poll_init(char *mq_name,
                  mqd_t *mq_desc)
{
    int ret_code = 0;

    /* open message queue*/
    if ((ret_code = bms_fan_poll_msq_open(mq_name, mq_desc)) < 0) {
        return ret_code;
    }

    return ret_code;
}

/*
* FEATURE:
*   bms_fan_poll_detect_fan_status
* PURPOSE:
*   datect fan status is present or non present
* PARAMETERS:
*   present_bmap                  (OUT) pointer of present bmap
*   nonpresent_bmap               (OUT) pointer of non-present bmap
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
int
bms_fan_poll_detect_module_status(unsigned int *present_bmap,
                                  unsigned int *nonpresent_bmap,
                                  unsigned int *intr_bmap)
{
    int ret_code = 0, i, j;
    unsigned int module_present_bmap;
    unsigned int cache_status[BMS_FAN_MODULE_NUM], cache_type[BMS_FAN_MODULE_NUM];
    unsigned int module_intr[BMS_FAN_MODULE_NUM] = {BMS_FAN_INTR_NORMAL};
    unsigned int intr_tmp;

    for(i = 0 ; i < BMS_FAN_MODULE_NUM; i++){
        bms_fan_serv_cache_module_cache_get(i, &cache_status[i], &cache_type[i]);
    }

    /* read fan present from sysfs, 0 for present and 1 for non-present */
     if((ret_code = bms_fan_serv_fan_present_get( &module_present_bmap)) < 0){
        return ret_code;
    }

    /* get interrupt source from fan control */
    for(i = 0 ; i < BMS_FAN_MODULE_NUM; i++){
        for(j = 0 ; j < BMS_FAN_NUM_PER_MODULE; j++){
            if((ret_code = bms_fan_serv_fan_intr_get(((i * BMS_FAN_NUM_PER_MODULE) + j), &intr_tmp)) < 0){
                return ret_code;
            }
            if(intr_tmp == BMS_FAN_INTR_FAULT){
                module_intr[i] = BMS_FAN_INTR_FAULT;
                break;
            }
        }
    }

    /* present */
    for(i = 0; i < BMS_FAN_MODULE_NUM; i++){
        //bms_fan_serv_cache_module_status_get(i, &status);
        if((cache_status[i] == BMS_FAN_MODULE_STATUS_NONPRESENT) ||
            (cache_status[i] == BMS_FAN_MODULE_STATUS_NONREADY) ||
            (cache_status[i] == BMS_FAN_MODULE_STATUS_NONINIT)){
            if(!(module_present_bmap & (1 << i))){
                *present_bmap |= (1 << i);
            }
        }
    }


    //mask = 1;

    /* non preent */
    for(i = 0; i < BMS_FAN_MODULE_NUM; i++){
        //bms_fan_serv_cache_module_status_get(i, &status);
        if((cache_status[i] == BMS_FAN_MODULE_STATUS_NORMAL) ||
            (cache_status[i] == BMS_FAN_MODULE_STATUS_NONINIT) ||
            (cache_status[i] == BMS_FAN_MODULE_STATUS_FAILED)){
            if(module_present_bmap & (1 << i)){
                *nonpresent_bmap |= (1 << i);
            }
        }
    }

    /* fan fault */
    for(i = 0; i < BMS_FAN_MODULE_NUM; i++){
        if((cache_status[i] == BMS_FAN_MODULE_STATUS_NORMAL) ||
            (cache_status[i] == BMS_FAN_MODULE_STATUS_NONREADY)){
            if(module_intr[i] == BMS_FAN_INTR_FAULT){
                *intr_bmap |= (1 << i);
            }
        }
    }

    return ret_code;
}



/*
* FEATURE:
*   bms_fan_poll_module_fault_reset
* PURPOSE:
*   reset fan fault status in fan controller
* PARAMETERS:
*   fan_number                (IN) fan number
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
int
bms_fan_poll_module_fault_reset(unsigned int module_number)
{
    return bms_fan_serv_fan_pwm_set(module_number, BMS_FAN_PWM_DUTY_CYCLE_MAX);
}

/*
* FEATURE:
*   bms_fan_polld
* PURPOSE:
*   bms fan module polling daemon
* PARAMETERS:
*   args                (IN) input value(message name)
* RETURNS:
*   The process will always polling fan module.
*/
void*
bms_fan_polld(void *args)
{
    char *mq_name = (char*)args;
    mqd_t mq_desc;
    int ret_code = 0, i;
    unsigned int module_type;
    bms_sys_serv_mq_data_t msg;
    unsigned int present_bmap = 0, nonpresent_bmap = 0, intr_bmap = 0;
    unsigned int cache_status, cache_type, cache_retry;

    msg.serv_name = mq_name;

    if((ret_code = bms_fan_poll_init(mq_name, &mq_desc)) < 0){
        goto quit;
    }

    while(!bms_fan_init_done){
        sleep(1);
    }

    while(1){
        present_bmap = 0;
        nonpresent_bmap = 0;
        intr_bmap = 0;

        if((ret_code = bms_fan_poll_detect_module_status(&present_bmap, &nonpresent_bmap, &intr_bmap)) < 0){
            goto wait;
        }

        if((present_bmap == 0) &&
           (nonpresent_bmap == 0) &&
           (intr_bmap == 0))
            goto wait;

        if(present_bmap != 0){
            for(i = 0; i < BMS_FAN_MODULE_NUM; i++){
                if(present_bmap & (1 << i)){
                    bms_fan_serv_cache_module_cache_get(i, &cache_status, &cache_type);

                    bms_fan_serv_cache_module_cache_retry_get(i, &cache_retry);

                    /* Due to max31790 driver has cache to protect i2c, so we will get older data sometimes.
                     * That data will confuse the fan fault status.
                     * So we will read fan fault status after wait 3 second delay.
                     */
                    if(cache_retry == BMS_FAN_NONREADY_RETRY_INIT){
                        if((ret_code = bms_fan_poll_module_fault_reset(i)) < 0){
                            continue;
                        }
                        bms_fan_serv_cache_module_cache_retry_set(i, ++cache_retry);
                    }else{
                        if(cache_retry < BMS_FAN_NONREADY_RETRY){
                            bms_fan_serv_cache_module_cache_retry_set(i, ++cache_retry);
                            continue;
                        }
                    }
                    msg.serv_type = SERV_TYPE_FAN_MODULE_PRESENT;
                    msg.number = i;

                    if((ret_code = bms_fan_serv_module_type_get(i, &module_type)) < 0){
                        continue;
                    }
                    msg.type = module_type;

                    bms_fan_poll_msq_send(&msg, &mq_desc);
                }
            }
        }

        if(nonpresent_bmap != 0){
            for(i = 0; i < BMS_FAN_MODULE_NUM; i++){
                if(nonpresent_bmap & (1 << i)){
                    msg.number = i;
                    msg.serv_type = SERV_TYPE_FAN_MODULE_NONPRESENT;
                    bms_fan_poll_msq_send(&msg, &mq_desc);
                }
            }
        }

        /* handle interrupt bit map */
        if(intr_bmap != 0){
            for(i = 0; i < BMS_FAN_MODULE_NUM; i++){
                if(intr_bmap & (1 << i)){

                    bms_fan_serv_cache_module_cache_retry_get(i, &cache_retry);

                    if(cache_retry < BMS_FAN_NONREADY_RETRY){
                        continue;
                    }

                    msg.number = i;
                    msg.serv_type = SERV_TYPE_RX_INTR;
                    bms_fan_poll_msq_send(&msg, &mq_desc);
                }
            }
        }

wait:
        sleep(1);
    }

quit:
    pthread_exit(NULL);
}
