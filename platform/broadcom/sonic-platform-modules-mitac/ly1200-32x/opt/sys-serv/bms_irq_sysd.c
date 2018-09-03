/*
 **********************************************************************
 *
 * @filename  bms_irq_sysd.c
 *
 * @purpose   BMS irq system daemon
 *
 * @create    2017/3/16
 *
 * @author    eddy.weng <eddy.weng@mic.com.tw>
 *
 * @history   2017/3/16: init version
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
#include <mqueue.h>
#include <unistd.h>
#include <string.h>
#include <pthread.h>
#include <sys/stat.h>
#include <signal.h>
#include "bms_irq_sysd.h"
#include "bms_sys_serv_common.h"
#include "bms_fan_servd.h"
#include "bms_psu_servd.h"

#define PROC_PRIORITY   90

/* MIC_FEAT_SYS_INT : 1 means interrupt, 0 means polling */
#define MIC_FEAT_SYS_INT 1



#if (MIC_FEAT_SYS_INT)
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>

#define BMS_SYS_GPE_SYSFS "/sys/firmware/acpi/interrupts/gpe%.2X"
#define BMS_SYS_GPE_SYSFS_CHAR_NUM 40 /* ex. /sys/firmware/acpi/interrupts/gpe01 */
#define BMS_SYS_GPE_DISABLE 0
#define BMS_SYS_GPE_INIT_SKIP 0xFF
#define BMS_SYS_ACPID_SOCKET_SYSFS "/var/run/acpid.socket"
#define BMS_SYS_GPE_INTR_TAG "bms_acpi PNP0C01:00 000000%.2X 00000000"
#define BMS_SYS_GPE_INTR_TAG_CHAR_NUM 38 /* ex. bms_acpi PNP0C01:00 00000002 00000000 */
#endif


bms_sys_serv_data_t bms_sys_serv_data[] = {
    {
        .name = "VRHOT",
        .intr_src = "/sys/bus/i2c/devices/1-0031/vrhot_irq",
        .intr_msk = "/sys/bus/i2c/devices/1-0031/vrhot_irq_en",
        .mq_name = "/sys_vrhot_mq",
        .mq_desc = (mqd_t)-1,
        .isr = bms_irq_sys_isr,
        .isrd = bms_vrhot_servd,
        .polld = NULL,
        .intr_msk_default = !SYS_SERV_INTR_MASK_EN,
    },
    {
        .name = "CPU_TEMP",
        .intr_src = "/sys/bus/i2c/devices/1-0031/cpu_thermtrip_irq",
        .intr_msk = "/sys/bus/i2c/devices/1-0031/cpu_thermtrip_irq_en",
        .mq_name = "/sys_isr_cpu_thermtrip_mq",
        .mq_desc = (mqd_t)-1,
        .isr = bms_irq_sys_isr,
        .isrd = bms_cpu_temp_servd,
        .polld = NULL,
        .intr_msk_default = !SYS_SERV_INTR_MASK_EN,
    },
    {
        .name = "SYS_TEMP",
        .intr_src = "/sys/bus/i2c/devices/1-0031/temp_alert_irq",
        .intr_msk = "/sys/bus/i2c/devices/1-0031/temp_alert_irq_en",
        .mq_name = "/sys_temp_alert_mq",
        .mq_desc = (mqd_t)-1,
        .isr = bms_irq_sys_isr,
        .isrd = bms_sys_temp_servd,
        .polld = NULL,
        .intr_msk_default = !SYS_SERV_INTR_MASK_EN,
    },
    {
        .name = "PS1",
        .intr_src = "/sys/bus/i2c/devices/1-0032/ps1_int",
        .intr_msk = "/sys/bus/i2c/devices/1-0032/ps1_int_msk",
        .mq_name = "/sys_psu_mq",
        .mq_desc = (mqd_t)-1,
        .isr = bms_irq_sys_isr,
        .isrd = bms_psu_servd,
        .polld = bms_psu_polld,
        .intr_msk_default = SYS_SERV_INTR_MASK_EN,/* detect by polling */
    },
    {
        .name = "PS2",
        .intr_src = "/sys/bus/i2c/devices/1-0032/ps2_int",
        .intr_msk = "/sys/bus/i2c/devices/1-0032/ps2_int_msk",
        .mq_name = "/sys_psu_mq",
        .mq_desc = (mqd_t)-1,
        .isr = bms_irq_sys_isr,
        .isrd = NULL, /* Share same interrupt service routine (ISR) with PSU1 */
        .polld = NULL,
        .intr_msk_default = SYS_SERV_INTR_MASK_EN,/* detect by polling */
    },
    {
        .name = "USB",
        .intr_src = "/sys/bus/i2c/devices/1-0032/usb_fault",
        .intr_msk = "/sys/bus/i2c/devices/1-0032/usb_fault_msk",
        .mq_name = "/sys_usb_fault_mq",
        .mq_desc = (mqd_t)-1,
        .isr = bms_irq_sys_isr,
        .isrd = bms_usb_servd,
        .polld = NULL,
        .intr_msk_default = !SYS_SERV_INTR_MASK_EN,
    },
    {
        .name = "PCIE",
        .intr_src = "/sys/bus/i2c/devices/1-0032/pcie_int",
        .intr_msk = "/sys/bus/i2c/devices/1-0032/pcie_int_msk",
        .mq_name = "/sys_pcie_mq",
        .mq_desc = (mqd_t)-1,
        .isr = bms_irq_sys_isr,
        .isrd = bms_pcie_servd,
        .polld = NULL,
        .intr_msk_default = SYS_SERV_INTR_MASK_EN,
    },
    {
        .name = "FAN",
        .intr_src = "/sys/bus/i2c/devices/1-0032/fan_alert_int",
        .intr_msk = "/sys/bus/i2c/devices/1-0032/fan_alert_int_msk",
        .mq_name = "/sys_fan_alert_mq",
        .mq_desc = (mqd_t)-1,
        .isr = bms_irq_sys_isr,
        .isrd = bms_fan_servd,
        .polld = bms_fan_polld,
        .intr_msk_default = SYS_SERV_INTR_MASK_EN,
    },
};

int bms_sys_serv_data_num = sizeof(bms_sys_serv_data) / sizeof(bms_sys_serv_data[0]);

/*
* FEATURE:
*   bms_irq_sys_isr
* PURPOSE:
*   Handle system interrupt routine
* PARAMETERS:
*   name                 (IN) service name
*   qname                (IN) message queue name
*   mq_desc              (IN) pointer of message queue description
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
int
bms_irq_sys_isr(char *name,
                char *qname,
                mqd_t mq_desc)
{
    int ret_code = 0;
    bms_sys_serv_mq_data_t msg;

    msg.serv_type = SERV_TYPE_RX_INTR;
    msg.serv_name = name;

    if (mq_send(mq_desc, (char*)&msg, sizeof(msg), 0) < 0) {
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

#if MIC_FEAT_SYS_INT == 1
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
bms_sys_serv_gpe_event_write(unsigned int gpe_num,
                             unsigned int enable)
{
    char buf[10], filename[BMS_SYS_GPE_SYSFS_CHAR_NUM] = { 0 };
    int fd, ret_code = 0, buf_size = sizeof(buf);
    ssize_t count;

    snprintf(filename, sizeof(filename), BMS_SYS_GPE_SYSFS, gpe_num);
    /* Open file */
    if ((fd = open(filename, O_WRONLY)) < 0) {
        ret_code = errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to open %s (%s)\n", filename, strerror(ret_code));
        return -ret_code;
    }

    /* Write file */
    if (enable == BMS_SYS_GPE_DISABLE) {
        snprintf(buf, buf_size, "%s", "disable\n");
    } else if (enable == !BMS_SYS_GPE_DISABLE) {
        snprintf(buf, buf_size, "%s", "enable\n");
    } else if (enable == BMS_SYS_GPE_INIT_SKIP) {
        snprintf(buf, buf_size, "%s", "disable\n");
    } else {
        snprintf(buf, buf_size, "%d", 0);
    }
    if ((count = write(fd, buf, buf_size)) != (-1)) {;}
    else if (enable == BMS_SYS_GPE_INIT_SKIP) {;}
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
*   bms_irq_sys_msq_create
* PURPOSE:
*   Create message queue
* PARAMETERS:
*   qname                 (IN) message queue name
*   mqd                   (OUT) pointer of message queue description
* RETURNS:
*   open success, this function returns 0.
*   for other cases, negative errno is returned.
*/
int
bms_irq_sys_msq_create(char *qname,
                       mqd_t *mqd)
{
    int flags = (O_CREAT | O_EXCL | O_WRONLY | O_NONBLOCK), ret_code = 0, i;
    mode_t mode = S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP | S_IROTH | S_IWOTH;
    struct mq_attr attr = {
        .mq_maxmsg = 64,
        .mq_msgsize = sizeof(bms_sys_serv_mq_data_t),
    };

    /* Check others item had the same qname that already created */
    for(i = 0; i < bms_sys_serv_data_num; i++){
        if(bms_sys_serv_data[i].mq_name){
            if(strcmp(bms_sys_serv_data[i].mq_name, qname) == 0){
                if(bms_sys_serv_data[i].mq_desc != (mqd_t)-1){
                    *mqd = bms_sys_serv_data[i].mq_desc;
                    return 0;
                }
            }
        }
    }

    /* destroy message queue if it presents */
    if ((mq_unlink(qname) < 0) && (errno != ENOENT)) {
        ret_code = errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to destroy message queue %s (%s)\n", qname, strerror(ret_code));
    }

    /* create POSIX message queue */
    if ((*mqd = mq_open(qname, flags, mode, &attr)) == (mqd_t)-1) {
        ret_code = errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to create message queue %s (%s)\n", qname, strerror(ret_code));
        return -ret_code;
    }

    syslog(LOG_DEBUG|LOG_USER,"Create message queue %s\n", qname);

    return -ret_code;
}

/*
* FEATURE:
*   bms_irq_sys_terminator
* PURPOSE:
*   Do someting when terminator flag coming
* PARAMETERS:
*   sig                   (IN) signal
* RETURNS:
*/
void
bms_irq_sys_terminator(int sig)
{
    int i;
    if (sig) {;}

    for (i = 0; i < bms_sys_serv_data_num; i++) {
        /* Disable interrupt function */
        bms_sys_serv_write(bms_sys_serv_data[i].intr_msk, SYS_SERV_INTR_MASK_EN);

        /* destroy message queue */
        mq_unlink(bms_sys_serv_data[i].mq_name);
    }

    syslog(LOG_DEBUG|LOG_USER,"Terminate %s\n", __FILE__);

    exit(0);
}



/*
* FEATURE:
*   main
* PURPOSE:
*   main start
* PARAMETERS:
*
* RETURNS:
*/
int
main(void)
{
    int i, value = 0, ret_code = 0;
    struct sched_param sched_param = {.sched_priority = PROC_PRIORITY};
    pthread_attr_t attr;

#if(MIC_FEAT_SYS_INT)
    int socket_dsc = 0;
    struct sockaddr_un socket_addr;
    char buf[BMS_SYS_GPE_INTR_TAG_CHAR_NUM],gpe_tag[BMS_SYS_GPE_INTR_TAG_CHAR_NUM];
    unsigned int gpe_num = 0x1;
    int unknow_interrupt = 1;
#else
    int mask;
#endif

    /* Set priority and make it be real-time */
    nice(-1);
    sched_setscheduler(0, SCHED_FIFO, &sched_param);

    /* Make the process be a background daemon */
    daemon(0 /* change working directory to root */,
           0 /* redirect stdin, stdout, and stderr to /dev/null */);

    /* Register handler for termination */
    signal(SIGTERM, bms_irq_sys_terminator);

    /* Create message queue for each interrupt service routine (ISR) */
    for (i = 0; i < bms_sys_serv_data_num; i++) {
        if (bms_sys_serv_data[i].mq_name) {
            if ((ret_code = bms_irq_sys_msq_create(bms_sys_serv_data[i].mq_name, &bms_sys_serv_data[i].mq_desc)) < 0) {
                goto quit;
            }
        }
    }

    /* Enable Interrupt function */
    for (i = 0; i < bms_sys_serv_data_num; i++) {
        if((ret_code = bms_sys_serv_write(bms_sys_serv_data[i].intr_msk, bms_sys_serv_data[i].intr_msk_default)) < 0) {
            goto quit;
        }
    }

    /* Disable fan module led */
    for(i = 0; i < BMS_FAN_MODULE_NUM; i++ ){
        if((ret_code = bms_sys_serv_write(bms_fan_serv_data[i * BMS_FAN_NUM_PER_MODULE].tray_led, BMS_FAN_MODULE_LED_OFF)) < 0) {
            goto quit;
        }
    }

    /* Disable panel fan led */
    if((ret_code = bms_sys_serv_write(BMS_SYSFS_FAN_PANEL_LED, BMS_FAN_PANEL_LED_OFF)) < 0) {
        goto quit;
    }


    /* Spawn interrupt service routine (ISR) daemon */
    for (i = 0; i < bms_sys_serv_data_num; i++) {
        if (bms_sys_serv_data[i].isrd) {
            pthread_attr_init(&attr);
            pthread_attr_setschedpolicy(&attr, SCHED_FIFO);
            pthread_attr_setschedparam(&attr, &sched_param);
            if (pthread_create(&bms_sys_serv_data[i].isrd_tid, &attr, bms_sys_serv_data[i].isrd, (void*)bms_sys_serv_data[i].mq_name) < 0) {
                ret_code = errno;
                syslog(LOG_WARNING|LOG_USER,"Failed to create pthread (%s)\n", strerror(ret_code));
                goto quit;
            }
        }
        if (bms_sys_serv_data[i].polld) {
            pthread_attr_init(&attr);
            pthread_attr_setschedpolicy(&attr, SCHED_FIFO);
            pthread_attr_setschedparam(&attr, &sched_param);
            if (pthread_create(&bms_sys_serv_data[i].polld_tid, &attr, bms_sys_serv_data[i].polld, (void*)bms_sys_serv_data[i].mq_name) < 0) {
                ret_code = errno;
                syslog(LOG_WARNING|LOG_USER,"Failed to create pthread (%s)\n", strerror(ret_code));
                goto quit;
            }
        }
    }

#if(MIC_FEAT_SYS_INT)
    snprintf(gpe_tag, sizeof(gpe_tag), BMS_SYS_GPE_INTR_TAG, gpe_num);
    /* set default value for GPE status */
    bms_sys_serv_gpe_event_write(gpe_num, BMS_SYS_GPE_INIT_SKIP);

    /* 3. Open the acpi socket. */
    if ((socket_dsc = socket(AF_UNIX, SOCK_STREAM, 0)) == (-1)) {
        ret_code = errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to open ACPI socket for GPE%.2X (%s)\n", gpe_num, strerror(ret_code));
        goto quit;
    }
    socket_addr.sun_family = AF_UNIX;
    strcpy(socket_addr.sun_path, BMS_SYS_ACPID_SOCKET_SYSFS);
    if (connect(socket_dsc, (struct sockaddr *)&socket_addr, sizeof(socket_addr)) == (-1)) {
        ret_code = errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to connect ACPI socket for GPE%.2X (%s)\n", gpe_num, strerror(ret_code));

    }
#endif


    while (1) {
#if(MIC_FEAT_SYS_INT)
        unknow_interrupt = 1;
        /* 3. Enable IRQ */
        if((ret_code = bms_sys_serv_gpe_event_write(gpe_num, !BMS_SYS_GPE_DISABLE)) < 0)
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
            if((ret_code = bms_sys_serv_gpe_event_write(gpe_num, BMS_SYS_GPE_DISABLE)) < 0)
                goto quit;
        } else {
            goto wait_irq;
        }
#endif

        /* Probe all interrupt sources */
        for (i = 0; i < bms_sys_serv_data_num; i++) {
            /* Detect which source(s) trigger the interrupt. 0 is assert, 1 is not assert */
            if ((ret_code = bms_sys_serv_hex_read(bms_sys_serv_data[i].intr_src, (unsigned int*)&value)) < 0) {
                goto quit;
            }

#if(MIC_FEAT_SYS_INT)
            if (value != SYS_SERV_INTR_STATUS_EN)
                continue;
#else
            /* 0 is masked, 1 is not mask */
            if ((ret_code = bms_sys_serv_hex_read(bms_sys_serv_data[i].intr_msk, (unsigned int*)&mask)) < 0) {
                goto quit;
            }

            if((value != SYS_SERV_INTR_STATUS_EN) || (mask != (!SYS_SERV_INTR_MASK_EN)))
                continue;
#endif

            /* Disable the source that triggers the interrupt */
            if ((ret_code = bms_sys_serv_write(bms_sys_serv_data[i].intr_msk, SYS_SERV_INTR_MASK_EN)) < 0) {
                goto quit;
            }

            /* Call interrupt service routine (ISR) */
            syslog(LOG_DEBUG|LOG_USER,"%s interrupt arrivals\n", bms_sys_serv_data[i].name);
            bms_sys_serv_data[i].isr(bms_sys_serv_data[i].name, bms_sys_serv_data[i].mq_name, bms_sys_serv_data[i].mq_desc);
#if(MIC_FEAT_SYS_INT)
            unknow_interrupt = 0;
#endif
        }
#if(MIC_FEAT_SYS_INT)
        /* Log unknown interrupt */
        if (unknow_interrupt) {
            syslog(LOG_WARNING|LOG_USER,"Receive an unknown interrupt from system interrput\n");
        }
#else
        sleep(2);
#endif

    }

quit:
    syslog(LOG_DEBUG|LOG_USER,"Quit daemon %s\n", __FILE__);
    exit(ret_code);
}
