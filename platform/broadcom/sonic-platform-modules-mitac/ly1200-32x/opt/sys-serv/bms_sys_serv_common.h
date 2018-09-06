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

#ifndef __BMS_SYS_SERV_COMMON_H__
#define __BMS_SYS_SERV_COMMON_H__

#define BMS_SYSFS_BOARD_TYPE  "/sys/bus/i2c/devices/1-0032/brd_type"

extern int bms_sys_serv_msq_open(const char *qname, mqd_t *mqd);
extern int bms_sys_serv_hex_read(char *filename, unsigned int *value);
extern int bms_sys_serv_write(char *filename, unsigned int value);
extern int bms_sys_serv_dec_read(char *filename, unsigned int *value);
extern int bms_sys_serv_char_read(char *filename, char *value);
extern int bms_sys_serv_hwmon_path_find(char *filepath, char *filename);
extern int bms_sys_serv_buf_write(char *filename, char *buf, int buf_size);
extern int bms_sys_serv_file_exist(char *filename);


#endif /* __BMS_SYS_SERV_COMMON_H__ */
