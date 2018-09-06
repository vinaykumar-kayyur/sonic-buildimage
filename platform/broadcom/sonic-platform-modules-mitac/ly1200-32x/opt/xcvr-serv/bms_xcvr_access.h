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

#ifndef __BMS_XCVR_ACCESS_H__
#define __BMS_XCVR_ACCESS_H__
enum {
    REG_DATA_NOT_READY = 0,
    REG_PAGE_SELECT,
    REG_INITIALIZATION_COMPLETE_FLAG,
    REG_HIGH_POWER_CLASS,
    REG_POWER_MODE_CONTROL,
};

extern unsigned char bms_xcvr_addr;
#define XCVR_READY 0
#define XCVR_INIT_COMPLETE 1
#define XCVR_LEGACY_POWER 1
#define XCVR_POWER_INIT_MASK 0x1

#define POWER_CLASS_MASK 0xC3

extern void bms_xcvr_check_power_class(unsigned char xcvr_read_byte, unsigned char *xcvr_power_class);
extern int bms_xcvr_intr_mask(unsigned char bus, unsigned char addr);
extern int bms_xcvr_read(unsigned char bus, unsigned char addr, int reg_item, unsigned char *val);
extern int bms_xcvr_max_power_class(unsigned char bus, unsigned char addr, unsigned char legacy_power);
extern int bms_xcvr_min_power_class(unsigned char bus, unsigned char addr);

#endif /*__BMS_XCVR_ACCESS_H__*/
