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

#include <stdio.h>
#include <syslog.h>
#include <stdlib.h>
#include <errno.h>
#include <mqueue.h>
#include <string.h>
#include <unistd.h>
#include <dirent.h>

/*
* FEATURE:
*   bms_sys_serv_msq_open
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
bms_sys_serv_msq_open(const char *qname,
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
 *   bms_sys_serv_hex_read
 * PURPOSE:
 *   hex read from file system
 * PARAMETERS:
 *   filename           (IN) file path in the sysfs
 *   value              (OUT) pointer of current value buffer
 * RETURNS:
 *   open success, this function returns zero.
 *   for other cases, negative errno is returned.
 */
int
bms_sys_serv_hex_read(char *filename,
                      unsigned int *value)
{
    char buf[32] = {0};
    int fd, ret_code = 0, buf_size = sizeof(buf);
    ssize_t count;

    /* Open xcvr pin file */
    if ((fd = open(filename, O_RDONLY)) < 0) {
        ret_code = errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to open %s (%s)\n", filename, strerror(ret_code));
        return -ret_code;
    }

    /* Read pin file */
    if ((count = read(fd, buf, buf_size)) != (-1)) {
        *value = strtol(buf, NULL, 16);
    }
    else {
        ret_code = (count >= 0) ? EIO : errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to read %s (%s)\n", filename, strerror(ret_code));
        close(fd);
        return -ret_code;
    }

    close(fd);
    return ret_code;
}

/*
 * FEATURE:
 *   bms_sys_serv_dec_read
 * PURPOSE:
 *   dec read from file system
 * PARAMETERS:
 *   filename           (IN) file path in the sysfs
 *   value              (OUT) pointer of current value buffer
 * RETURNS:
 *   open success, this function returns zero.
 *   for other cases, negative errno is returned.
 */
int
bms_sys_serv_dec_read(char *filename,
                      unsigned int *value)
{
    char buf[32];
    int fd, ret_code = 0, buf_size = sizeof(buf);
    ssize_t count;

    /* Open  file */
    if ((fd = open(filename, O_RDONLY)) < 0) {
        ret_code = errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to open %s (%s)\n", filename, strerror(ret_code));
        return -ret_code;
    }

    /* Read pin file */
    if ((count = read(fd, buf, buf_size)) != (-1)) {
        *value = strtol(buf, NULL, 10);
    }
    else {
        ret_code = (count >= 0) ? EIO : errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to read %s (%s)\n", filename, strerror(ret_code));
        close(fd);
        return -ret_code;
    }

    close(fd);
    return ret_code;
}

/*
 * FEATURE:
 *   bms_sys_serv_char_read
 * PURPOSE:
 *   char read from file system
 * PARAMETERS:
 *   filename           (IN) file path in the sysfs
 *   value              (OUT) pointer of current value buffer
 * RETURNS:
 *   open success, this function returns zero.
 *   for other cases, negative errno is returned.
 */
int
bms_sys_serv_char_read(char *filename,
                       char *value)
{
    char buf[32];
    int fd, ret_code = 0, buf_size = sizeof(buf);
    ssize_t count;

    /* Open  file */
    if ((fd = open(filename, O_RDONLY)) < 0) {
        ret_code = errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to open %s (%s)\n", filename, strerror(ret_code));
        return -ret_code;
    }

    /* Read pin file */
    if ((count = read(fd, buf, buf_size)) != (-1)) {
        /* the last character was \n*/
        memcpy(value, buf, count);
    }
    else {
        ret_code = (count >= 0) ? EIO : errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to read %s (%s)\n", filename, strerror(ret_code));
        close(fd);
        return -ret_code;
    }

    close(fd);
    return ret_code;
}


/*
 * FEATURE:
 *   bms_sys_serv_write
 * PURPOSE:
 *   byte data write to file system
 * PARAMETERS:
 *   filename           (IN) file path in the sysfs
 *   value              (IN) new register value
 * RETURNS:
 *   open success, this function returns .
 *   for other cases, negative errno is returned.
 */
int
bms_sys_serv_write(char *filename,
                   unsigned int value)
{
    char buf[4];
    int fd, ret_code = 0, buf_size = sizeof(buf);
    ssize_t count;

    /* Open file */
    if ((fd = open(filename, O_WRONLY)) < 0) {
        ret_code = errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to open %s (%s)\n", filename, strerror(ret_code));
        return -ret_code;
    }

    /* Write file */
    snprintf(buf, buf_size, "%d", value);
    if ((count = write(fd, buf, buf_size)) != (-1)) {;}
    else {
        ret_code = (count >= 0) ? EIO : errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to write %s (%s)\n", filename, strerror(ret_code));
        close(fd);
        return -ret_code;
    }

    close(fd);
    return ret_code;
}

/*
 * FEATURE:
 *   bms_sys_serv_buf_write
 * PURPOSE:
 *   buf data write to file system
 * PARAMETERS:
 *   filename           (IN) file path in the sysfs
 *   buf                (IN) buf data
 *   buf_size           (IN) buf size
 * RETURNS:
 *   open success, this function returns .
 *   for other cases, negative errno is returned.
 */
int
bms_sys_serv_buf_write(char *filename,
                       char *buf,
                       int buf_size)
{
    int fd, ret_code = 0;
    ssize_t count;

    /* Open file */
    if ((fd = open(filename, O_WRONLY)) < 0) {
        ret_code = errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to open %s (%s)\n", filename, strerror(ret_code));
        return -ret_code;
    }

    /* Write file */
    if ((count = write(fd, buf, buf_size)) != (-1)) {;}
    else {
        ret_code = (count >= 0) ? EIO : errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to write %s (%s)\n", filename, strerror(ret_code));
        close(fd);
        return -ret_code;
    }

    close(fd);
    return ret_code;
}

/*
 * FEATURE:
 *   bms_sys_serv_hwmon_path_find
 * PURPOSE:
 *   find hwmon path for when insert different order
 * PARAMETERS:
 *   filename           (IN) file path in the sysfs
 *   value              (IN) new register value
 * RETURNS:
 *   open success, this function returns .
 *   for other cases, negative errno is returned.
 */
int
bms_sys_serv_hwmon_path_find(char *filepath,
                             char *filename)
{
    struct dirent **namelist;
    int ret_code = 0;
    char name[32];

    memcpy(name, filename, strlen(filename)+1);

    ret_code = scandir(filepath , &namelist, NULL, alphasort);

    if (ret_code < 0){
        ret_code = errno;
        syslog(LOG_WARNING|LOG_USER,"Failed to scandir %s (%s)\n", filepath, strerror(ret_code));
        return -ret_code;
    }

    /* if counter is 2, that mean the folder is empty that include "." and ".." */
    if(ret_code <= 2){
        syslog(LOG_WARNING|LOG_USER,"Failed to find folder hwmon (%s)\n", strerror(ret_code));
        return -ENXIO;
    }

    sprintf(filename, "%s/%s/%s", filepath, namelist[--ret_code]->d_name, name);
    free(namelist);
    return ret_code;
}

/*
 * FEATURE:
 *   bms_sys_serv_file_exist
 * PURPOSE:
 *   find file name exist
 * PARAMETERS:
 *   filename           (IN) file name
 * RETURNS:
 *   file exist, return zero
 *   for other cases, return 1
 */
int
bms_sys_serv_file_exist(char *filename)
{
    if( access( filename, F_OK ) != -1 ) {
    // file exists
        return 0;
    }
    // file doesn't exist
    return 1;
}
