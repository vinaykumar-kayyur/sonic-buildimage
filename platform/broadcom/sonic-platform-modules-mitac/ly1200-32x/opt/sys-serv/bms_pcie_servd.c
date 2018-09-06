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
#include "bms_irq_sysd.h"

#include <unistd.h>


/*
* FEATURE:
*   bms_pcie_msq_open
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
bms_pcie_msq_open(const char *qname,
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
*   bms_pcie_servd
* PURPOSE:
*   service to handle message queue event of pcie
* PARAMETERS:
*   args                (IN) message queue name
* RETURNS:
*   open success, this function will wait for message queue.
*   for other cases, will exit this program.
*/
void*
bms_pcie_servd(void *args)
{
    char *mq_name = (char*)args;
    mqd_t mq_desc;
    bms_sys_serv_mq_data_t msg;
    int ret_code;

    /* Open message queue */
    if (bms_pcie_msq_open(mq_name, &mq_desc) < 0) {
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
            case SERV_TYPE_RX_INTR: /* PCIE_INT interrupt */
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
