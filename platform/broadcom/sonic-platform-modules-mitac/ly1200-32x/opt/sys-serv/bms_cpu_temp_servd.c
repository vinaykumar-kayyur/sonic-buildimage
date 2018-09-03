/*
 **********************************************************************
 *
 * @filename  bms_cpu_temp_servd.c
 *
 * @purpose   BMS cpu temperature service
 *
 * @create    2017/3/17
 *
 * @author    eddy.weng <eddy.weng@mic.com.tw>
 *
 * @history   2017/3/17: init version
 *
 **********************************************************************
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
#include "bms_irq_sysd.h"

#include <unistd.h>

/*
* FEATURE:
*   bms_cpu_temp_msq_open
* PURPOSE:
*   open POSIX message queue
* PARAMETERS:
*   qname                (IN) message queue name
*   mqd                  (OUT) pointer of message queue description
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
static int
bms_cpu_temp_msq_open(const char *qname,
                      mqd_t *mqd)
{
    int flags = (O_RDONLY), ret_code = 0;

    /* create POSIX message queue */
    if ((*mqd = mq_open(qname, flags)) == (mqd_t)-1) {
        ret_code = errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to open message queue %s (%s)\n", qname, strerror(ret_code));
    }

    return -ret_code;
}

/*
* FEATURE:
*   bms_cpu_temp_servd
* PURPOSE:
*   service to handle message queue event of cpu temperature
* PARAMETERS:
*   args                (IN) message queue name
* RETURNS:
*   open success, this function will wait for message queue.
*   for other cases, will exit this program.
*/
void*
bms_cpu_temp_servd(void *args)
{
    char *mq_name = (char*)args;
    mqd_t mq_desc;
    bms_sys_serv_mq_data_t msg;
    int ret_code;

    /* Open message queue */
    if (bms_cpu_temp_msq_open(mq_name, &mq_desc) < 0) {
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
            case SERV_TYPE_RX_INTR: /* CPU_THERMTRIP_IRQ interrupt */
                syslog(LOG_DEBUG|LOG_USER,"%s interrupt has handled\n", msg.serv_name);
                break;

            default:
                syslog(LOG_WARNING|LOG_USER,"Receive an unknown message %d from %s\n", msg.serv_type, mq_name);
                break;
        }
    }

quit:
    pthread_exit(NULL);
}
