/*
 **********************************************************************
 *
 * @filename  bms_xcvr_isrd.c
 *
 * @purpose   BMS switch board interrupt handler
 *
 * @create    2017/3/3
 *
 * @author    yencheng.lin <yencheng.lin@mic.com.tw>
 *
 * @history   2017/3/3: init version
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
#include <unistd.h>
#include "bms_xcvr_servd.h"

#define MASTER_CPLD_START_PORT 1
#define SLAVE_CPLD_START_PORT 17

/* MIC_FEAT_XCVR_INT : 1 means interrupt, 0 means polling */
#define MIC_FEAT_XCVR_INT 0

#if MIC_FEAT_XCVR_INT == 1
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>

#define GPE_SYSFS "/sys/firmware/acpi/interrupts/gpe%.2X"
#define GPE_SYSFS_CHAR_NUM 40 /* ex. /sys/firmware/acpi/interrupts/gpe01 */
#define GPE_DISABLE 0
#define GPE_INIT_SKIP 0xFF
#define ACPID_SOCKET_SYSFS "/var/run/acpid.socket"
#define GPE_INTR_TAG "bms_acpi PNP0C01:00 000000%.2X 00000000"
#define GPE_INTR_TAG_CHAR_NUM 38 /* ex. bms_acpi PNP0C01:00 00000002 00000000 */
#endif

#if MIC_FEAT_XCVR_INT == 1
/*
 * FEATURE:
 *   bms_gpe_event_write
 * PURPOSE:
 *   set event to gpe
 * PARAMETERS:
 *   gpe_num            (IN) gpe number
 *   enable             (IN) 1 means enable, 0 means disable, others set 0.
 * RETURNS:
 *   open success, this function returns .
 *   for other cases, negative errno is returned.
 */
int
bms_gpe_event_write(unsigned int gpe_num,
                    unsigned int enable)
{
    char buf[10], filename[GPE_SYSFS_CHAR_NUM] = { 0 };
    int fd, ret_code = 0, buf_size = sizeof(buf);
    ssize_t count;

    snprintf(filename, sizeof(filename), GPE_SYSFS, gpe_num);
    /* Open file */
    if ((fd = open(filename, O_WRONLY)) < 0) {
        ret_code = errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to open %s (%s)\n", filename, strerror(ret_code));
        return -ret_code;
    }

    /* Write file */
    if (enable == GPE_DISABLE) {
        snprintf(buf, buf_size, "%s", "disable\n");
    } else if (enable == !GPE_DISABLE) {
        snprintf(buf, buf_size, "%s", "enable\n");
    } else if (enable == GPE_INIT_SKIP) {
        snprintf(buf, buf_size, "%s", "disable\n");
    } else {
        snprintf(buf, buf_size, "%d", 0);
    }
    if ((count = write(fd, buf, buf_size)) != (-1)) {;}
    else if (enable == GPE_INIT_SKIP) {;}
    else {
        ret_code = (count >= 0) ? EIO : errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to write %s (%s)\n", filename, strerror(ret_code));
        close(fd);
        return -ret_code;
    }

    close(fd);
    return ret_code;
}
#endif

/*
 * FEATURE:
 *   open_msq
 * PURPOSE:
 *   open message queue
 * PARAMETERS:
 *   qname              (IN) queue name
 *   mqd                (OUT) pointer of message queue description
 * RETURNS:
 *   open success, this function returns .
 *   for other cases, negative errno is returned.
 */
int
open_msq(const char *qname,
         mqd_t *mqd)
{
    int flags = (O_WRONLY | O_NONBLOCK), ret_code = 0;

    /* open POSIX message queue */
    if ((*mqd = mq_open(qname, flags)) == (mqd_t)-1) {
        ret_code = errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to open message queue %s (%s)\n", qname, strerror(ret_code));
    }

    return -ret_code;
}

/*
 * FEATURE:
 *   bms_xcvr_isr
 * PURPOSE:
 *   send message queue
 * PARAMETERS:
 *   port_bmap          (IN) bmap of triggered port
 *   qname              (IN) queue name
 *   mq_desc            (IN) message queue description
 * RETURNS:
 *   open success, this function returns .
 *   for other cases, negative errno is returned.
 */
int
bms_xcvr_isr(unsigned int port_bmap,
             char *qname,
             mqd_t mq_desc)
{
    int ret_code = 0;
    bms_xcvr_serv_mq_data_t msg;

    msg.intr_type = INTR_TYPE_RX_INTR;
    msg.port_bmap = port_bmap;

    if (mq_send(mq_desc, (const char*)&msg, sizeof(msg), 0) < 0) {
        ret_code = errno;
        if (ret_code == EAGAIN) {
            syslog(LOG_WARNING|LOG_USER,"Message queue %s is full\n", qname);
        }
        else {
            syslog(LOG_WARNING|LOG_USER,"Failed to send message to %s (%s)\n", qname, strerror(ret_code));
        }
    }

    return -ret_code;
}

/*
 * FEATURE:
 *   bms_xcvr_isrd
 * PURPOSE:
 *   wait for interrupt and call bms_xcvr_isr function
 * PARAMETERS:
 *   args               (IN) base port number by master or slave CPLD
 * RETURNS:
 *   no.
 */
void*
bms_xcvr_isrd(void *args)
{
    mqd_t mq_handle;
    unsigned int port_num = *(unsigned int *)args, start_port, end_port, value = 0;
    unsigned int irq_trigger_bmap = 0, intr_msk_bmap = 0, intr_msk_cache_bmap = 0;
    int i, ret_code = 0;
#if MIC_FEAT_XCVR_INT == 1
    int socket_dsc = 0;
    struct sockaddr_un socket_addr;
    char buf[GPE_INTR_TAG_CHAR_NUM],gpe_tag[GPE_INTR_TAG_CHAR_NUM];
    unsigned int gpe_num = 0x0;
#endif
    /* Initial of bms_xcvr_isrd */

    /* 1. the ISR is for master or slave CPLD */
    if (port_num == MASTER_CPLD_START_PORT) {
        start_port = MASTER_CPLD_START_PORT - 1;
#if MIC_FEAT_XCVR_INT == 1
        gpe_num = 0x47;
#endif
    } else if (port_num == SLAVE_CPLD_START_PORT) {
        start_port = SLAVE_CPLD_START_PORT - 1;
#if MIC_FEAT_XCVR_INT == 1
        gpe_num = 0x2;
#endif
    }
    end_port = start_port + (SLAVE_CPLD_START_PORT - MASTER_CPLD_START_PORT);

    /* 2. Open message queue */
    if (open_msq(xcvrirq_data[0].mq_name, &mq_handle) < 0) {
        goto quit;
    }

#if MIC_FEAT_XCVR_INT == 1
    snprintf(gpe_tag, sizeof(gpe_tag), GPE_INTR_TAG, gpe_num);
    /* set default value for GPE status */
    bms_gpe_event_write(gpe_num, GPE_INIT_SKIP);

    /* 3. Open the acpi socket. */
    if ((socket_dsc = socket(AF_UNIX, SOCK_STREAM, 0)) == (-1)) {
        ret_code = errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to open ACPI socket for GPE%.2X (%s)\n", gpe_num, strerror(ret_code));
        goto quit;
    }
    socket_addr.sun_family = AF_UNIX;
    strcpy(socket_addr.sun_path, ACPID_SOCKET_SYSFS);
    if (connect(socket_dsc, (struct sockaddr *)&socket_addr, sizeof(socket_addr)) == (-1)) {
        ret_code = errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to connect ACPI socket for GPE%.2X (%s)\n", gpe_num, strerror(ret_code));
        goto quit;
    }
#endif

    while (1) {
#if MIC_FEAT_XCVR_INT == 1
        /* 3. Enable IRQ */
        if((ret_code = bms_gpe_event_write(gpe_num, !GPE_DISABLE)) < 0)
            goto quit;

        /* Wait for interrupt occurs; this is a blocking call and may leave
         * the blocking state unexpectly while receiving a signal. In such
         * a case, we go back to wait for the arriving of interrupt.
         */
wait_irq:
        memset(buf,0,sizeof(buf));
        if (recv(socket_dsc, buf, sizeof(buf), 0) <= 0) {
            if (errno == EINTR) {goto wait_irq;}
            ret_code = errno;
            syslog(LOG_WARNING|LOG_USER,"Failed to receive ACPI socket for GPE%.2X (%s)\n", gpe_num, strerror(ret_code));
            goto quit;
        }
        if (!strncmp(buf, gpe_tag, sizeof(gpe_tag)-1)) {
            /* Due to bms_gpe hanlder does not set disable now. */
            if((ret_code = bms_gpe_event_write(gpe_num, GPE_DISABLE)) < 0)
                goto quit;
        } else {
            goto wait_irq;
        }
#else
        usleep(100000);
#endif

        /* Detect xcvr interrupt pin - mark irq_trigger_bmap from xcvr interrupt pin */
        /* Detect which source(s) trigger the interrupt from 16 port */
        for (i = (int)start_port, irq_trigger_bmap = 0; i < (int)end_port; i++) {
            if (xcvrirq_data[i].intr_src) {
                if ((ret_code = bms_xcvr_pin_read(xcvrirq_data[i].intr_src, &value)) < 0) {
                    goto quit;
                }
                irq_trigger_bmap |= ((~value & 0xff) << i);
            }
        }

        /* send event with irq_trigger_bmap */
        if (irq_trigger_bmap) {
            /* 1. enable irq_trigger_bmap that triggers the interrupt mask */
            /* Read irq_msk pin from cache */
            pthread_mutex_lock(&bms_xcvr_data_lock);
            bms_xcvr_data_read(XCVR_INTR_MSK, &intr_msk_cache_bmap);
            pthread_mutex_unlock(&bms_xcvr_data_lock);

            intr_msk_bmap = intr_msk_cache_bmap;

            /* Disable the source that triggers the interrupt mask */
            bms_xcvr_bmap_modify( &intr_msk_bmap, irq_trigger_bmap, INTR_MASK_EN);

            pthread_mutex_lock(&bms_xcvr_data_lock);
            if ((ret_code = bms_xcvr_pin_bmap_modify(XCVR_INTR_MSK, intr_msk_bmap, intr_msk_cache_bmap)) < 0) {
                goto quit;
            }
            bms_xcvr_data_write(XCVR_INTR_MSK, intr_msk_bmap);
            pthread_mutex_unlock(&bms_xcvr_data_lock);

            bms_xcvr_bmap_to_num(irq_trigger_bmap);
            syslog(LOG_DEBUG|LOG_USER,"Interrupt port %s arrivals.\n", bms_xcvr_bmap_to_num_str);
            /* 2. send event to message queue */
            /* Call interrupt service routine (ISR) with only one queue name (xcvrirq_data[0]) */
            xcvrirq_data[start_port].isr(irq_trigger_bmap, xcvrirq_data[0].mq_name, mq_handle);
        } else {
#if MIC_FEAT_XCVR_INT == 1
            /* Log unknown interrupt */
            syslog(LOG_WARNING|LOG_USER,"Receive unknown interrupt from port%d - port%d (%s)\n", start_port + 1, end_port, buf);
#endif
        }
    }

quit:
    syslog(LOG_WARNING|LOG_USER,"Quit thread from %s function (port%d - port%d)\n", __func__, start_port + 1, end_port);
#if MIC_FEAT_XCVR_INT == 1
    close(socket_dsc);
#endif
    pthread_exit(NULL);
}
