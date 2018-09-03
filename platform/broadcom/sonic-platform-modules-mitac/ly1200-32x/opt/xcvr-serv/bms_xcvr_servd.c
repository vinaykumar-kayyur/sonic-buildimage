/*
 **********************************************************************
 *
 * @filename  bms_xcvr_servd.c
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
#include <mqueue.h>
#include <unistd.h>
#include <string.h>
#include <pthread.h>
#include <sys/stat.h>
#include <signal.h>
#include "bms_xcvr_servd.h"
#include "bms_xcvr_access.h"

#define PROC_PRIORITY   90
/* The XCVR_LPMODE_PIN_USE is used when system can not acces with transceiver eeprom */
#define XCVR_LPMODE_PIN_USE 0

#define STR_LEN 100
char bms_xcvr_bmap_to_num_str[STR_LEN] = { 0 };

extern int bms_xcvr_isr(unsigned int port_num, char *qname, mqd_t mq_desc);
extern void* bms_xcvr_isrd(void *args);

extern pthread_mutex_t bms_xcvr_data_lock;
extern void* bms_xcvr_polld(void *args);
extern pthread_t polld_tid;

bms_xcvr_serv_data_t xcvrirq_data[] = {
    {
        .port_num = 1,
        .present  = "/sys/bus/i2c/devices/1-0032/port_1_8_present",
        .intr_src = "/sys/bus/i2c/devices/1-0032/port_1_8_irq_status",
        .intr_msk = "/sys/bus/i2c/devices/1-0032/port_1_8_irq_msk",
        .modsel   = "/sys/bus/i2c/devices/1-0032/port_1_8_modsel",
        .lpmode   = "/sys/bus/i2c/devices/1-0032/port_1_8_lpmode",
        .reset    = "/sys/bus/i2c/devices/1-0032/port_1_8_rst",
        .mq_name  = "/xcvr_isr_mq",
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = bms_xcvr_isrd,
        .smbus_num= 10,
    },
    {
        .port_num = 2,
        .present  = NULL, /* Share same byte with PORT1 */
        .intr_src = NULL, /* Share same byte with PORT1 */
        .intr_msk = NULL, /* Share same byte with PORT1 */
        .modsel   = NULL, /* Share same byte with PORT1 */
        .lpmode   = NULL, /* Share same byte with PORT1 */
        .reset    = NULL, /* Share same byte with PORT1 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT1 */
        .smbus_num= 11,
    },
    {
        .port_num = 3,
        .present  = NULL, /* Share same byte with PORT1 */
        .intr_src = NULL, /* Share same byte with PORT1 */
        .intr_msk = NULL, /* Share same byte with PORT1 */
        .modsel   = NULL, /* Share same byte with PORT1 */
        .lpmode   = NULL, /* Share same byte with PORT1 */
        .reset    = NULL, /* Share same byte with PORT1 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT1 */
        .smbus_num= 12,
    },
    {
        .port_num = 4,
        .present  = NULL, /* Share same byte with PORT1 */
        .intr_src = NULL, /* Share same byte with PORT1 */
        .intr_msk = NULL, /* Share same byte with PORT1 */
        .modsel   = NULL, /* Share same byte with PORT1 */
        .lpmode   = NULL, /* Share same byte with PORT1 */
        .reset    = NULL, /* Share same byte with PORT1 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT1 */
        .smbus_num= 13,
    },
    {
        .port_num = 5,
        .present  = NULL, /* Share same byte with PORT1 */
        .intr_src = NULL, /* Share same byte with PORT1 */
        .intr_msk = NULL, /* Share same byte with PORT1 */
        .modsel   = NULL, /* Share same byte with PORT1 */
        .lpmode   = NULL, /* Share same byte with PORT1 */
        .reset    = NULL, /* Share same byte with PORT1 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT1 */
        .smbus_num= 14,
    },
    {
        .port_num = 6,
        .present  = NULL, /* Share same byte with PORT1 */
        .intr_src = NULL, /* Share same byte with PORT1 */
        .intr_msk = NULL, /* Share same byte with PORT1 */
        .modsel   = NULL, /* Share same byte with PORT1 */
        .lpmode   = NULL, /* Share same byte with PORT1 */
        .reset    = NULL, /* Share same byte with PORT1 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT1 */
        .smbus_num= 15,
    },
    {
        .port_num = 7,
        .present  = NULL, /* Share same byte with PORT1 */
        .intr_src = NULL, /* Share same byte with PORT1 */
        .intr_msk = NULL, /* Share same byte with PORT1 */
        .modsel   = NULL, /* Share same byte with PORT1 */
        .lpmode   = NULL, /* Share same byte with PORT1 */
        .reset    = NULL, /* Share same byte with PORT1 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT1 */
        .smbus_num= 16,
    },
    {
        .port_num = 8,
        .present  = NULL, /* Share same byte with PORT1 */
        .intr_src = NULL, /* Share same byte with PORT1 */
        .intr_msk = NULL, /* Share same byte with PORT1 */
        .modsel   = NULL, /* Share same byte with PORT1 */
        .lpmode   = NULL, /* Share same byte with PORT1 */
        .reset    = NULL, /* Share same byte with PORT1 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT1 */
        .smbus_num= 17,
    },
    {
        .port_num = 9,
        .present  = "/sys/bus/i2c/devices/1-0032/port_9_16_present",
        .intr_src = "/sys/bus/i2c/devices/1-0032/port_9_16_irq_status",
        .intr_msk = "/sys/bus/i2c/devices/1-0032/port_9_16_irq_msk",
        .modsel   = "/sys/bus/i2c/devices/1-0032/port_9_16_modsel",
        .lpmode   = "/sys/bus/i2c/devices/1-0032/port_9_16_lpmode",
        .reset    = "/sys/bus/i2c/devices/1-0032/port_9_16_rst",
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT1 */
        .smbus_num= 18,
    },
    {
        .port_num = 10,
        .present  = NULL, /* Share same byte with PORT9 */
        .intr_src = NULL, /* Share same byte with PORT9 */
        .intr_msk = NULL, /* Share same byte with PORT9 */
        .modsel   = NULL, /* Share same byte with PORT9 */
        .lpmode   = NULL, /* Share same byte with PORT9 */
        .reset    = NULL, /* Share same byte with PORT9 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT1 */
        .smbus_num= 19,
    },
    {
        .port_num = 11,
        .present  = NULL, /* Share same byte with PORT9 */
        .intr_src = NULL, /* Share same byte with PORT9 */
        .intr_msk = NULL, /* Share same byte with PORT9 */
        .modsel   = NULL, /* Share same byte with PORT9 */
        .lpmode   = NULL, /* Share same byte with PORT9 */
        .reset    = NULL, /* Share same byte with PORT9 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT1 */
        .smbus_num= 20,
    },
    {
        .port_num = 12,
        .present  = NULL, /* Share same byte with PORT9 */
        .intr_src = NULL, /* Share same byte with PORT9 */
        .intr_msk = NULL, /* Share same byte with PORT9 */
        .modsel   = NULL, /* Share same byte with PORT9 */
        .lpmode   = NULL, /* Share same byte with PORT9 */
        .reset    = NULL, /* Share same byte with PORT9 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT1 */
        .smbus_num= 21,
    },
    {
        .port_num = 13,
        .present  = NULL, /* Share same byte with PORT9 */
        .intr_src = NULL, /* Share same byte with PORT9 */
        .intr_msk = NULL, /* Share same byte with PORT9 */
        .modsel   = NULL, /* Share same byte with PORT9 */
        .lpmode   = NULL, /* Share same byte with PORT9 */
        .reset    = NULL, /* Share same byte with PORT9 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT1 */
        .smbus_num= 22,
    },
    {
        .port_num = 14,
        .present  = NULL, /* Share same byte with PORT9 */
        .intr_src = NULL, /* Share same byte with PORT9 */
        .intr_msk = NULL, /* Share same byte with PORT9 */
        .modsel   = NULL, /* Share same byte with PORT9 */
        .lpmode   = NULL, /* Share same byte with PORT9 */
        .reset    = NULL, /* Share same byte with PORT9 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT1 */
        .smbus_num= 23,
    },
    {
        .port_num = 15,
        .present  = NULL, /* Share same byte with PORT9 */
        .intr_src = NULL, /* Share same byte with PORT9 */
        .intr_msk = NULL, /* Share same byte with PORT9 */
        .modsel   = NULL, /* Share same byte with PORT9 */
        .lpmode   = NULL, /* Share same byte with PORT9 */
        .reset    = NULL, /* Share same byte with PORT9 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT1 */
        .smbus_num= 24,
    },
    {
        .port_num = 16,
        .present  = NULL, /* Share same byte with PORT9 */
        .intr_src = NULL, /* Share same byte with PORT9 */
        .intr_msk = NULL, /* Share same byte with PORT9 */
        .modsel   = NULL, /* Share same byte with PORT9 */
        .lpmode   = NULL, /* Share same byte with PORT9 */
        .reset    = NULL, /* Share same byte with PORT9 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT1 */
        .smbus_num= 25,
    },
    {
        .port_num = 17,
        .present  = "/sys/bus/i2c/devices/1-0033/port_17_24_present",
        .intr_src = "/sys/bus/i2c/devices/1-0033/port_17_24_irq_status",
        .intr_msk = "/sys/bus/i2c/devices/1-0033/port_17_24_irq_msk",
        .modsel   = "/sys/bus/i2c/devices/1-0033/port_17_24_modsel",
        .lpmode   = "/sys/bus/i2c/devices/1-0033/port_17_24_lpmode",
        .reset    = "/sys/bus/i2c/devices/1-0033/port_17_24_rst",
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = bms_xcvr_isrd,
        .smbus_num= 26,
    },
    {
        .port_num = 18,
        .present  = NULL, /* Share same byte with PORT17 */
        .intr_src = NULL, /* Share same byte with PORT17 */
        .intr_msk = NULL, /* Share same byte with PORT17 */
        .modsel   = NULL, /* Share same byte with PORT17 */
        .lpmode   = NULL, /* Share same byte with PORT17 */
        .reset    = NULL, /* Share same byte with PORT17 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT17 */
        .smbus_num= 27,
    },
    {
        .port_num = 19,
        .present  = NULL, /* Share same byte with PORT17 */
        .intr_src = NULL, /* Share same byte with PORT17 */
        .intr_msk = NULL, /* Share same byte with PORT17 */
        .modsel   = NULL, /* Share same byte with PORT17 */
        .lpmode   = NULL, /* Share same byte with PORT17 */
        .reset    = NULL, /* Share same byte with PORT17 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT17 */
        .smbus_num= 28,
    },
    {
        .port_num = 20,
        .present  = NULL, /* Share same byte with PORT17 */
        .intr_src = NULL, /* Share same byte with PORT17 */
        .intr_msk = NULL, /* Share same byte with PORT17 */
        .modsel   = NULL, /* Share same byte with PORT17 */
        .lpmode   = NULL, /* Share same byte with PORT17 */
        .reset    = NULL, /* Share same byte with PORT17 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT17 */
        .smbus_num= 29,
    },
    {
        .port_num = 21,
        .present  = NULL, /* Share same byte with PORT17 */
        .intr_src = NULL, /* Share same byte with PORT17 */
        .intr_msk = NULL, /* Share same byte with PORT17 */
        .modsel   = NULL, /* Share same byte with PORT17 */
        .lpmode   = NULL, /* Share same byte with PORT17 */
        .reset    = NULL, /* Share same byte with PORT17 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT17 */
        .smbus_num= 30,
    },
    {
        .port_num = 22,
        .present  = NULL, /* Share same byte with PORT17 */
        .intr_src = NULL, /* Share same byte with PORT17 */
        .intr_msk = NULL, /* Share same byte with PORT17 */
        .modsel   = NULL, /* Share same byte with PORT17 */
        .lpmode   = NULL, /* Share same byte with PORT17 */
        .reset    = NULL, /* Share same byte with PORT17 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT17 */
        .smbus_num= 31,
    },
    {
        .port_num = 23,
        .present  = NULL, /* Share same byte with PORT17 */
        .intr_src = NULL, /* Share same byte with PORT17 */
        .intr_msk = NULL, /* Share same byte with PORT17 */
        .modsel   = NULL, /* Share same byte with PORT17 */
        .lpmode   = NULL, /* Share same byte with PORT17 */
        .reset    = NULL, /* Share same byte with PORT17 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT17 */
        .smbus_num= 32,
    },
    {
        .port_num = 24,
        .present  = NULL, /* Share same byte with PORT17 */
        .intr_src = NULL, /* Share same byte with PORT17 */
        .intr_msk = NULL, /* Share same byte with PORT17 */
        .modsel   = NULL, /* Share same byte with PORT17 */
        .lpmode   = NULL, /* Share same byte with PORT17 */
        .reset    = NULL, /* Share same byte with PORT17 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT17 */
        .smbus_num= 33,
    },
    {
        .port_num = 25,
        .present  = "/sys/bus/i2c/devices/1-0033/port_25_32_present",
        .intr_src = "/sys/bus/i2c/devices/1-0033/port_25_32_irq_status",
        .intr_msk = "/sys/bus/i2c/devices/1-0033/port_25_32_irq_msk",
        .modsel   = "/sys/bus/i2c/devices/1-0033/port_25_32_modsel",
        .lpmode   = "/sys/bus/i2c/devices/1-0033/port_25_32_lpmode",
        .reset    = "/sys/bus/i2c/devices/1-0033/port_25_32_rst",
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT17 */
        .smbus_num= 34,
    },
    {
        .port_num = 26,
        .present  = NULL, /* Share same byte with PORT25 */
        .intr_src = NULL, /* Share same byte with PORT25 */
        .intr_msk = NULL, /* Share same byte with PORT25 */
        .modsel   = NULL, /* Share same byte with PORT25 */
        .lpmode   = NULL, /* Share same byte with PORT25 */
        .reset    = NULL, /* Share same byte with PORT25 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT17 */
        .smbus_num= 35,
    },
    {
        .port_num = 27,
        .present  = NULL, /* Share same byte with PORT25 */
        .intr_src = NULL, /* Share same byte with PORT25 */
        .intr_msk = NULL, /* Share same byte with PORT25 */
        .modsel   = NULL, /* Share same byte with PORT25 */
        .lpmode   = NULL, /* Share same byte with PORT25 */
        .reset    = NULL, /* Share same byte with PORT25 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT17 */
        .smbus_num= 36,
    },
    {
        .port_num = 28,
        .present  = NULL, /* Share same byte with PORT25 */
        .intr_src = NULL, /* Share same byte with PORT25 */
        .intr_msk = NULL, /* Share same byte with PORT25 */
        .modsel   = NULL, /* Share same byte with PORT25 */
        .lpmode   = NULL, /* Share same byte with PORT25 */
        .reset    = NULL, /* Share same byte with PORT25 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT17 */
        .smbus_num= 37,
    },
    {
        .port_num = 29,
        .present  = NULL, /* Share same byte with PORT25 */
        .intr_src = NULL, /* Share same byte with PORT25 */
        .intr_msk = NULL, /* Share same byte with PORT25 */
        .modsel   = NULL, /* Share same byte with PORT25 */
        .lpmode   = NULL, /* Share same byte with PORT25 */
        .reset    = NULL, /* Share same byte with PORT25 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT17 */
        .smbus_num= 38,
    },
    {
        .port_num = 30,
        .present  = NULL, /* Share same byte with PORT25 */
        .intr_src = NULL, /* Share same byte with PORT25 */
        .intr_msk = NULL, /* Share same byte with PORT25 */
        .modsel   = NULL, /* Share same byte with PORT25 */
        .lpmode   = NULL, /* Share same byte with PORT25 */
        .reset    = NULL, /* Share same byte with PORT25 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT17 */
        .smbus_num= 39,
    },
    {
        .port_num = 31,
        .present  = NULL, /* Share same byte with PORT25 */
        .intr_src = NULL, /* Share same byte with PORT25 */
        .intr_msk = NULL, /* Share same byte with PORT25 */
        .modsel   = NULL, /* Share same byte with PORT25 */
        .lpmode   = NULL, /* Share same byte with PORT25 */
        .reset    = NULL, /* Share same byte with PORT25 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT17 */
        .smbus_num= 40,
    },
    {
        .port_num = 32,
        .present  = NULL, /* Share same byte with PORT25 */
        .intr_src = NULL, /* Share same byte with PORT25 */
        .intr_msk = NULL, /* Share same byte with PORT25 */
        .modsel   = NULL, /* Share same byte with PORT25 */
        .lpmode   = NULL, /* Share same byte with PORT25 */
        .reset    = NULL, /* Share same byte with PORT25 */
        .mq_name  = NULL, /* Share same message queue with PORT1 */
        .mq_desc  = (mqd_t)-1,
        .isr      = bms_xcvr_isr,
        .isrd     = NULL, /* Share same interrupt service routine (ISR) with PORT17 */
        .smbus_num= 41,
    },
};
int xcvrirq_data_num = sizeof(xcvrirq_data) / sizeof(xcvrirq_data[0]);

/*
 * FEATURE:
 *   bms_xcvr_create_msq
 * PURPOSE:
 *   Create POSIX message queue
 * PARAMETERS:
 *   qname                (IN) I2C bus to be looking for
 *   mqd                  (OUT) pointer of message queue description
 * RETURNS:
 *   open success, this function returns .
 *   for other cases, negative errno is returned.
 */
int
bms_xcvr_create_msq(char *qname,
                    mqd_t *mqd)
{
    int flags = (O_CREAT | O_EXCL | O_RDONLY), ret_code = 0;
    mode_t mode = S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP | S_IROTH | S_IWOTH;
    struct mq_attr attr = {
        .mq_maxmsg = 64,
        .mq_msgsize = sizeof(bms_xcvr_serv_mq_data_t),
    };

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
 *   bms_xcvr_terminator
 * PURPOSE:
 *   restore xcvr pin status based on CPLD spec when system reboot/halt
 * PARAMETERS:
 *   sig                (IN) system signature
 * RETURNS:
 *   no.
 */
void
bms_xcvr_terminator(int sig)
{
    char *mq_name = xcvrirq_data[0].mq_name;
    if (sig) {;}

    /* disable interrupt function */
    bms_xcvr_pin_bmap_write(XCVR_INTR_MSK, INTR_MASK_EN);

    /* disable module select function */
    bms_xcvr_pin_bmap_write(XCVR_MODSEL, ~MODSEL_EN);

    /* assert reset function */
    bms_xcvr_pin_bmap_write(XCVR_RESET, RST_EN);

    /* assert lpmode function */
    bms_xcvr_pin_bmap_write(XCVR_LPMODE, ~LPMODE_DIS);

    /* destroy message queue */
    mq_unlink(mq_name);

    /* destroy mutex lock */
    pthread_mutex_destroy(&bms_xcvr_data_lock);

    syslog(LOG_DEBUG|LOG_USER,"Terminate %s\n", __FILE__);

    exit(0);
}

/*
 * FEATURE:
 *   bms_xcvr_bmap_modify
 * PURPOSE:
 *   modify the status of pin bmap
 * PARAMETERS:
 *   changed_bmap       (OUT) pointer of pin bmap
 *   check_bmap         (IN) modified when the bit is 1.
 *   switch_status      (IN) status that it will switch
 * RETURNS:
 *   no.
 */
void
bms_xcvr_bmap_modify(unsigned int *changed_bmap,
                     unsigned int check_bmap,
                     unsigned int switch_status)
{
    if ( switch_status ) {
        *changed_bmap |= check_bmap;
    } else {
        *changed_bmap &= ~check_bmap;
    }
}

/*
 * FEATURE:
 *   bms_xcvr_bmap_to_num
 * PURPOSE:
 *   translate to number from bit-map
 * PARAMETERS:
 *   bmap               (IN) bit-map.
 * RETURNS:
 *   no.
 */
void bms_xcvr_bmap_to_num(unsigned int bmap)
{
    char temp[4] = { 0 };
    int i, first = 1;
    memset(bms_xcvr_bmap_to_num_str, 0, sizeof(bms_xcvr_bmap_to_num_str));
    for (i = 0; i < xcvrirq_data_num; i++) {
        if (bmap & (((unsigned int)1) << i)) {
            if (first) {
                snprintf(temp, sizeof(temp), "%d", i + 1);
                first = 0;
            } else {
                snprintf(temp, sizeof(temp), ",%d", i + 1);
            }
            strncat(bms_xcvr_bmap_to_num_str, temp, 4);
        }
    }
}

/*
* FEATURE:
*   bms_xcvr_mutex_init
* PURPOSE:
*   initial mutex
* PARAMETERS:
*
* RETURNS:
*   init success, this function shall return zero.
*   otherwise, an error number shall be returned to indicate the error.
*/
static int
bms_xcvr_mutex_init(void)
{
    int ret_code;

    if((ret_code = pthread_mutex_init(&bms_xcvr_data_lock, NULL)) != 0){
        return -ret_code;
    }

    return ret_code;
}

/*
 * FEATURE:
 *   bms_xcvr_reset
 * PURPOSE:
 *   reset transceiver
 * PARAMETERS:
 *   bmap                 (IN) port bmap for reset
 * RETURNS:
 *   no.
 */
static int
bms_xcvr_reset(unsigned int bmap)
{
    int ret_code = 0;
    unsigned int reset_cache_bmap, modsel_cache_bmap, reset_bmap, modsel_bmap;

    if (bmap) {
        /* Read reset,modsel status of all port from database*/
        pthread_mutex_lock(&bms_xcvr_data_lock);
        bms_xcvr_data_read(XCVR_RESET, &reset_cache_bmap);
        bms_xcvr_data_read(XCVR_MODSEL, &modsel_cache_bmap);
        pthread_mutex_unlock(&bms_xcvr_data_lock);

        /* 1. Assert ResetL of the transceiver. */
        reset_bmap = reset_cache_bmap;
        bms_xcvr_bmap_modify( &reset_bmap, bmap, RST_EN);
        /* 2. De-assert ModSelL of the transceiver. */
        modsel_bmap = modsel_cache_bmap;
        bms_xcvr_bmap_modify( &modsel_bmap, bmap, ~MODSEL_EN);

        pthread_mutex_lock(&bms_xcvr_data_lock);
        if((ret_code = bms_xcvr_pin_bmap_modify(XCVR_RESET, reset_bmap, reset_cache_bmap)) < 0)
            return -1;
        if((ret_code = bms_xcvr_pin_bmap_modify(XCVR_MODSEL, modsel_bmap, modsel_cache_bmap)) < 0)
            return -1;
        bms_xcvr_data_write(XCVR_RESET, reset_bmap);
        bms_xcvr_data_write(XCVR_MODSEL, modsel_bmap);
        pthread_mutex_unlock(&bms_xcvr_data_lock);

        /* 3. Wait 2 micro second (t_reset_init from SFF-8679). */
        usleep(2);

        /* Read reset,modsel status of all port from database*/
        pthread_mutex_lock(&bms_xcvr_data_lock);
        bms_xcvr_data_read(XCVR_RESET, &reset_cache_bmap);
        pthread_mutex_unlock(&bms_xcvr_data_lock);

        /* 4. De-assert ResetL of the transceiver */
        reset_bmap = reset_cache_bmap;
        bms_xcvr_bmap_modify( &reset_bmap, bmap, ~RST_EN);

        pthread_mutex_lock(&bms_xcvr_data_lock);
        if((ret_code = bms_xcvr_pin_bmap_modify(XCVR_RESET, reset_bmap, reset_cache_bmap)) < 0)
            return -1;
        bms_xcvr_data_write(XCVR_RESET, reset_bmap);
        pthread_mutex_unlock(&bms_xcvr_data_lock);

        bms_xcvr_bmap_to_num(bmap);
        syslog(LOG_WARNING|LOG_USER,"Transceiver is reset, port %s .\n", bms_xcvr_bmap_to_num_str);
    }
    return 0;
}

/*
 * FEATURE:
 *   main
 * PURPOSE:
 *   initial xcvr service and handle the message queue
 * PARAMETERS:
 *   no
 * RETURNS:
 *   open success, this function returns .
 *   for other cases, negative errno is returned.
 */
int
main(void)
{
    int i, ret_code = 0, unused;
    struct sched_param sched_param = {.sched_priority = PROC_PRIORITY};
    pthread_attr_t attr;
    char *mq_name = xcvrirq_data[0].mq_name;
    bms_xcvr_serv_mq_data_t msg;
    unsigned char xcvr_bus, xcvr_read_byte, xcvr_power_class;
    unsigned int modsel_cache_bmap, intr_msk_cache_bmap;
    unsigned int modsel_bmap, intr_msk_bmap;
    unsigned int xcvr_init_intr_bmap, xcvr_intr_bmap;
    unsigned int irq_trigger_bmap, init_fail_bmap, insert_port, xcvr_init_done_bmap;
    unsigned int xcvr_init_pass_bmap;
    unsigned int reset_port_bmap,intr_port;
#if XCVR_LPMODE_PIN_USE == 1 /* LPMODE is reserved */
    unsigned int lpmode_bmap, lpmode_cache_bmap;
#endif

    /* Initial of bms_irq_xcvrd */
    /* 0. initial Mutexes */
    if ((ret_code = bms_xcvr_mutex_init() < 0)) {
        return ret_code;
    }

    /* 1. Set priority and parameter of this process */
    nice(-1);
    sched_setscheduler(0, SCHED_FIFO, &sched_param);

    /* 2. Daemonize, make the process be a background daemon */
    daemon(0 /* change working directory to root */,
           0 /* redirect stdin, stdout, and stderr to /dev/null */);

    /* 3. Register handler for termination */
    signal(SIGTERM, bms_xcvr_terminator);

    /* 4. set default for xcvr pin status */
    if ((ret_code = bms_xcvr_pin_bmap_write(XCVR_RESET, RST_EN)) < 0)
        goto quit;
    if ((ret_code = bms_xcvr_pin_bmap_write(XCVR_MODSEL, ~MODSEL_EN)) < 0)
        goto quit;
    if ((ret_code = bms_xcvr_pin_bmap_write(XCVR_INTR_MSK, ~INTR_MASK_EN)) < 0)
        goto quit;
    if ((ret_code = bms_xcvr_pin_bmap_write(XCVR_LPMODE, ~LPMODE_DIS)) < 0)
        goto quit;

    /* set default for xcvr pin cache */
    pthread_mutex_lock(&bms_xcvr_data_lock);
    bms_xcvr_data_write(XCVR_PRESENT, ~PRESENT_EN);
    bms_xcvr_data_write(XCVR_RESET, RST_EN);
    bms_xcvr_data_write(XCVR_MODSEL, ~MODSEL_EN);
    bms_xcvr_data_write(XCVR_INTR_MSK, ~INTR_MASK_EN);
    bms_xcvr_data_write(XCVR_INIT_DONE, INIT_DONE_DIS);
    bms_xcvr_data_write(XCVR_LPMODE, ~LPMODE_DIS);
    pthread_mutex_unlock(&bms_xcvr_data_lock);

    /* 5. Create message queue for each interrupt service routine (ISR) */
    for (i = 0; i < xcvrirq_data_num; i++) {
        if (xcvrirq_data[i].mq_name) {
            if ((ret_code = bms_xcvr_create_msq(xcvrirq_data[i].mq_name, &xcvrirq_data[i].mq_desc)) < 0) {
                goto quit;
            }
        }
    }

    /* 6. Spawn interrupt service routine (ISR) daemon */
    for (i = 0; i < xcvrirq_data_num; i++) {
        if (xcvrirq_data[i].isrd) {
            pthread_attr_init(&attr);
            pthread_attr_setschedpolicy(&attr, SCHED_FIFO);
            pthread_attr_setschedparam(&attr, &sched_param);
            if (pthread_create(&xcvrirq_data[i].isrd_tid, &attr, xcvrirq_data[i].isrd, (void*)&xcvrirq_data[i].port_num) < 0) {
                ret_code = errno;
                syslog(LOG_WARNING|LOG_USER,"Failed to create pthread to headle transceiver interrupt (%s)\n", strerror(ret_code));
                goto quit;
            }
        }
    }

    /* 6. Spawn polling daemon */
    pthread_attr_init(&attr);
    pthread_attr_setschedpolicy(&attr, SCHED_FIFO);
    pthread_attr_setschedparam(&attr, &sched_param);
    if (pthread_create(&polld_tid, &attr, bms_xcvr_polld, (void*)&unused) < 0) {
        ret_code = errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to create pthread for polling transceiver present (%s)\n", strerror(ret_code));
        goto quit;
    }

    while (1) {

        /* Wait for message queue */
        if (mq_receive(xcvrirq_data[0].mq_desc, (char*)&msg, sizeof(msg), 0) < 0) {
            ret_code = errno;
            syslog(LOG_WARNING|LOG_USER,"Failed to receive message from %s (%s)\n", mq_name, strerror(ret_code));
            goto quit;
        }

        /* Handle irq_trigger_bmap */
        irq_trigger_bmap = msg.port_bmap;

        /* Read modsel,init_done status of all port from database*/
        pthread_mutex_lock(&bms_xcvr_data_lock);
        bms_xcvr_data_read(XCVR_MODSEL, &modsel_cache_bmap);
        bms_xcvr_data_read(XCVR_INIT_DONE, &xcvr_init_done_bmap);
        pthread_mutex_unlock(&bms_xcvr_data_lock);

        modsel_bmap = modsel_cache_bmap;

        /* Filter to xcvr_init_intr and xcvr_intr bmap by xcvr_init_done_bmap from irq_trigger_bmap */
        xcvr_intr_bmap = xcvr_init_done_bmap & irq_trigger_bmap;
        xcvr_init_intr_bmap = xcvr_intr_bmap ^ irq_trigger_bmap;

        if ( xcvr_init_intr_bmap ) {

            /* Enable modsel for xcvr init intr port*/
            modsel_cache_bmap = modsel_bmap;
            bms_xcvr_bmap_modify( &modsel_bmap, xcvr_init_intr_bmap, MODSEL_EN);

            /* Write modsel status to xcvr pin and database */
            pthread_mutex_lock(&bms_xcvr_data_lock);
            if ((ret_code = bms_xcvr_pin_bmap_modify(XCVR_MODSEL, modsel_bmap, modsel_cache_bmap)) < 0)
                goto quit;
            bms_xcvr_data_write(XCVR_MODSEL, modsel_bmap);
            pthread_mutex_unlock(&bms_xcvr_data_lock);

            /* Some QSFP cables have a quirk that asserts the IntN line as a side
             * effect of power up on plug-in. We ignore this false positive
             * interrupt until the module has finished powering up by waiting for
             * a minimum timeout of the module inrush initialization time of
             * 500 ms (SFF 8679 Table 5-6) to ensure the voltage rails in the
             * module have stabilized.
             */
            usleep(500000);

            for (i = 0, init_fail_bmap = 0, xcvr_init_pass_bmap = 0; i < xcvrirq_data_num; i++) {

                insert_port = xcvr_init_intr_bmap & (((unsigned int)1) << i);
                if (insert_port) {
                    xcvr_bus = xcvrirq_data[i].smbus_num;
                    /* read DataNotReady */
                    ret_code = bms_xcvr_read(xcvr_bus, bms_xcvr_addr, REG_DATA_NOT_READY, &xcvr_read_byte);
                    /* Init xcvr */
                    if (xcvr_read_byte == XCVR_READY) {
                        if (ret_code >= 0) {
                            /* 1. Read "Initialization commplete flag" bit (SFF-8636 page 0 byte 6) and the bit is introduced after SFF rev2.5 (SFF-8636 page 0 byte 221) */
                            ret_code = bms_xcvr_read(xcvr_bus, bms_xcvr_addr, REG_INITIALIZATION_COMPLETE_FLAG, &xcvr_read_byte);
                        }
                        if (ret_code >= 0) {
                            /* 2. Mask interrupts of the transceiver for init process */
                            ret_code = bms_xcvr_intr_mask(xcvr_bus, bms_xcvr_addr);
                        }
                        if (ret_code >= 0) {
                            /* 3. Read power class (SFF-8636 page 0 byte 129) of the transceiver */
                            ret_code = bms_xcvr_read(xcvr_bus, bms_xcvr_addr, REG_HIGH_POWER_CLASS, &xcvr_read_byte);
                            bms_xcvr_check_power_class(xcvr_read_byte, &xcvr_power_class);
                            if (ret_code >= 0) {
                                /* 3.1 If the transceiver's allowed max power class is 1, set 1 to "High_Power_Class_enable" bit, set 1 to "Power_override" bit, set 1 to "Power_set" bit (SFF-8636 page 0 byte 93, SFF-8679 table 5-5) */
                                if (xcvr_power_class == 1) {
                                    ret_code = bms_xcvr_min_power_class(xcvr_bus, bms_xcvr_addr);
                                } else if (xcvr_power_class < 5) {
                                /* 3.2 If the transceiver's allowed max power class is 2-4, set 0 to "High_Power_Class_enable" bit, set 1 to "Power_override" bit, set 0 to "Power_set" bit (SFF-8636 page 0 byte 93, SFF-8679 table 5-5) */
                                    ret_code = bms_xcvr_max_power_class(xcvr_bus, bms_xcvr_addr, XCVR_LEGACY_POWER);
                                } else {
                                /* 3.3 If the transceiver's allowed max power class is 5-7, set 1 to "High_Power_Class_enable" bit, set 1 to "Power_override" bit, set 0 to "Power_set" bit (SFF-8636 page 0 byte 93, SFF-8679 table 5-5). */
                                    ret_code = bms_xcvr_max_power_class(xcvr_bus, bms_xcvr_addr, !XCVR_LEGACY_POWER);
                                }
                            }
                        }
                        /* 4. If xcvr access fail, go to (INIT FAIL) */
                        if (ret_code < 0) {
                            init_fail_bmap |= insert_port;
                            syslog(LOG_DEBUG|LOG_USER,"Port %d transceiver is ready by DataNotReady bit, but setup fail\n", i+1);
                        } else {
                            /* 5. mark xcvr_init_done_bmap for init success port */
                            xcvr_init_done_bmap |= insert_port;
                            xcvr_init_pass_bmap |= insert_port;
                            syslog(LOG_DEBUG|LOG_USER,"Port %d transceiver is ready by DataNotReady bit and setup pass\n", i+1);
                        }
                    } else {
                        init_fail_bmap |= insert_port;
                        syslog(LOG_DEBUG|LOG_USER,"Port %d transceiver is not ready and re-init\n", i+1);
                    }
                }
            }

            /* Reset xcvr - (INIT FAIL) When "Data_Not_Ready" bit (SFF-8636 page 0 byte 2) is not ready */
            if (bms_xcvr_reset(init_fail_bmap) < 0)
              goto quit;
        }

        if ( xcvr_intr_bmap ) {

            for (i = 0, reset_port_bmap = 0; i < xcvrirq_data_num; i++) {

                intr_port = xcvr_intr_bmap & (((unsigned int)1) << i);
                if (intr_port) {
                    xcvr_bus = xcvrirq_data[i].smbus_num;
                    ret_code = bms_xcvr_read(xcvr_bus, bms_xcvr_addr, REG_POWER_MODE_CONTROL, &xcvr_read_byte);
                    if (ret_code >= 0) {
                        if (!(xcvr_read_byte & XCVR_POWER_INIT_MASK)) {
                            reset_port_bmap |= intr_port;
                            /* Read "Initialization commplete flag" bit (SFF-8636 page 0 byte 6) and the bit is introduced after SFF rev2.5 (SFF-8636 page 0 byte 221) */
                            bms_xcvr_read(xcvr_bus, bms_xcvr_addr, REG_INITIALIZATION_COMPLETE_FLAG, &xcvr_read_byte);
                            syslog(LOG_DEBUG|LOG_USER,"Port %d transceiver is reset by re-insert\n", i+1);
                        }
                    } else {
                        reset_port_bmap |= intr_port;
                    }
                }
            }

            bms_xcvr_bmap_modify( &xcvr_init_done_bmap, reset_port_bmap, INIT_DONE_DIS);

            if (bms_xcvr_reset(reset_port_bmap) < 0)
              goto quit;

            /* TODO : handle transceiver interrupt */

            bms_xcvr_bmap_to_num(xcvr_intr_bmap);
            syslog(LOG_DEBUG|LOG_USER,"Transceiver interrupt has handled, port %s\n", bms_xcvr_bmap_to_num_str);
        }

        /* Read intr_msk status of all port from database*/
        pthread_mutex_lock(&bms_xcvr_data_lock);
        bms_xcvr_data_read(XCVR_INTR_MSK, &intr_msk_cache_bmap);
#if XCVR_LPMODE_PIN_USE == 1 /* LPMODE is reserved */
        bms_xcvr_data_read(XCVR_LPMODE, &lpmode_cache_bmap);
#endif
        pthread_mutex_unlock(&bms_xcvr_data_lock);

        /* Disable the source that triggers the interrupt */
        intr_msk_bmap = intr_msk_cache_bmap;
#if XCVR_LPMODE_PIN_USE == 1 /* LPMODE is reserved */
        lpmode_bmap = lpmode_cache_bmap;
        bms_xcvr_bmap_modify( &lpmode_bmap, xcvr_init_pass_bmap, LPMODE_DIS);
#endif
        bms_xcvr_bmap_modify( &intr_msk_bmap, irq_trigger_bmap, ~INTR_MASK_EN);

        pthread_mutex_lock(&bms_xcvr_data_lock);
        if ((ret_code = bms_xcvr_pin_bmap_modify(XCVR_INTR_MSK, intr_msk_bmap, intr_msk_cache_bmap)) < 0)
            goto quit;
#if XCVR_LPMODE_PIN_USE == 1 /* LPMODE is reserved */
        if ((ret_code = bms_xcvr_pin_bmap_modify(XCVR_LPMODE, lpmode_bmap, lpmode_cache_bmap)) < 0)
            goto quit;
        bms_xcvr_data_write(XCVR_LPMODE, lpmode_bmap);
#endif
        bms_xcvr_data_write(XCVR_INTR_MSK, intr_msk_bmap);
        bms_xcvr_data_write(XCVR_INIT_DONE, xcvr_init_done_bmap);
        pthread_mutex_unlock(&bms_xcvr_data_lock);
    }

quit:
    pthread_mutex_destroy(&bms_xcvr_data_lock);
    syslog(LOG_DEBUG|LOG_USER,"Quit daemon %s for monitor xcvr status\n", __FILE__);
    exit(-ret_code);
}
