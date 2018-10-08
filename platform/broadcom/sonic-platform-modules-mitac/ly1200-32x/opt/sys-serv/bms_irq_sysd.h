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

#ifndef __BMS_IRQ_SYSD_H__
#define __BMS_IRQ_SYSD_H__

#define SYS_SERV_INTR_STATUS_EN 0
#define SYS_SERV_INTR_MASK_EN 0

typedef int (*isr_t)(char *, char *, mqd_t);
typedef void* (*isrd_t)(void*);

typedef struct {
    char *name;
    char *intr_src;
    char *intr_msk;
    char *mq_name;
    mqd_t mq_desc;
    isr_t isr;
    pthread_t isrd_tid;
    isrd_t isrd;
    pthread_t polld_tid;
    isrd_t polld;
    unsigned int intr_msk_default;
} bms_sys_serv_data_t;

typedef struct {
    unsigned char serv_type;
#define SERV_TYPE_RX_INTR 1 /* Receving an interrupt */
    char *serv_name; /* service name */
    unsigned int number;
    unsigned int type;
    unsigned int cause;
} bms_sys_serv_mq_data_t;

extern void* bms_vrhot_servd(void *args);
extern void* bms_cpu_temp_servd(void *args);
extern void* bms_sys_temp_servd(void *args);
extern void* bms_psu_servd(void *args);
extern void* bms_usb_servd(void *args);
extern void* bms_pcie_servd(void *args);
extern void* bms_fan_servd(void *args);
extern void* bms_fan_polld(void *args);
extern int bms_irq_sys_isr(char *name, char *qname, mqd_t mq_desc);
extern void* bms_psu_polld(void *args);
#endif /* __BMS_IRQ_SYSD_H__ */
