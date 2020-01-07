/*
 * Copyright (C) 2018 Inspur Electronic Information Industry Co.,Ltd
 *
 * Licensed under the GNU General Public License Version 2
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 */

/* ----------------------------------------------------------------------------
 * Include files
 * ----------------------------------------------------------------------------
 */
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/mutex.h>
#include <linux/delay.h>
#include <linux/completion.h>
#include <linux/ipmi.h>
#include <linux/ipmi_smi.h>

/* ----------------------------------------------------------------------------
 * Constant
 * ----------------------------------------------------------------------------
 */
#define _IPMI_MAX_RESP_LEN     64

/* ----------------------------------------------------------------------------
 * IPMI functions
 * ----------------------------------------------------------------------------
 */
static atomic_t _dummy_count = ATOMIC_INIT(0);

static void _dummy_smi_free(struct ipmi_smi_msg *msg)
{
    atomic_dec(&_dummy_count);
}

static struct ipmi_smi_msg _halt_smi_msg =
{
    .done = _dummy_smi_free
};

static void _dummy_recv_free(struct ipmi_recv_msg *msg)
{
    atomic_dec(&_dummy_count);
}

static struct ipmi_recv_msg _halt_recv_msg =
{
    .done = _dummy_recv_free
};

DEFINE_MUTEX(_ipmi_mutex);

static void _msg_handler(
    struct ipmi_recv_msg    *recv_msg,
    void                    *handler_data
)
{
    struct completion *comp = recv_msg->user_msg_data;

    if (comp) {
        complete(comp);
    } else {
        printk(KERN_DEBUG "[%s()#%d: IPMI receive message incompleted\n", __FUNCTION__, __LINE__);
        ipmi_free_recv_msg(recv_msg);
    }

    return;
}

static struct ipmi_user_hndl _ipmi_hndlrs =
{
    .ipmi_recv_hndl = _msg_handler,
};

/*!
 *  execute IPMI command and get result
 *
 *  @param netfn        [in]  code of network function
 *  @param cmd          [in]  code of command
 *  @param data         [in]  array of command data
 *  @param data_len     [in]  length of data
 *  @param result       [out] array of result
 *  @param result_len   [inout] in:  length of result array buffer
 *                              out: length of executed result
 *
 *  @return     0   successful
 *             -1   IPMI response failed
 *             -2   IPMI create user failed
 *             -3   IPMI request failed
 *             -4   IPMI response failed
 *
 *  @note       result and result_len do _NOT_ include the complete code.
 */
int ipmi_cmd(
    char    netfn,
    char    cmd,
    char    *data,
    int     data_len,
    char    *result,
    int     *result_len
)
{
    int rc = 0;
    int i;

    struct  ipmi_system_interface_addr  addr;
    struct  kernel_ipmi_msg             msg;
    uint8_t                             msg_data[data_len];
    struct  completion                  comp;
    ipmi_user_t                         ipmi_mh_user = NULL;

    printk(KERN_DEBUG "[%s()#%d: Enter, netfn=0x%02x, cmd=0x%02x, data_len=%d\n", __FUNCTION__, __LINE__, netfn, cmd, data_len);

    /* Check invalid input parameters */
    if (data_len && data == NULL) {
        printk(KERN_ERR "[%s()#%d: Exit, invalid input parameter, data_len != 0 but data == NULL]\n", __FUNCTION__, __LINE__);
        return -1;
    }
    if (result_len && result == NULL) {
        printk(KERN_ERR "[%s()#%d: Exit, invalid input parameter, result_len != 0 but result == NULL]\n", __FUNCTION__, __LINE__);
        return -1;
    }
    if (result_len && (*result_len > _IPMI_MAX_RESP_LEN)) {
        printk(KERN_ERR "[%s()#%d: Exit, invalid input parameter, result_len > %d]\n", __FUNCTION__, __LINE__, _IPMI_MAX_RESP_LEN);
        return -1;
    }

    for (i = 0; i < data_len; i++) {
        printk(KERN_DEBUG "data[%d]=0x%02x(%d) ", i, data[i], data[i]);
    }
    printk(KERN_DEBUG "\n");

    mutex_lock(&_ipmi_mutex);

    rc = ipmi_create_user(0, &_ipmi_hndlrs, NULL, &ipmi_mh_user);
    if (rc < 0) {
        mutex_unlock(&_ipmi_mutex);
        printk(KERN_ERR "[%s()#%d: Exit, ipmi_create_user() failed, rc=%d]\n", __FUNCTION__, __LINE__, rc);
        return -2;
    }

    if (data_len) {
        memcpy(msg_data, data, data_len);
    }

    addr.addr_type = IPMI_SYSTEM_INTERFACE_ADDR_TYPE;
    addr.channel   = IPMI_BMC_CHANNEL;
    addr.lun       = 0;

    msg.netfn    = netfn;
    msg.cmd      = cmd;
    msg.data     = msg_data;
    msg.data_len = data_len;

    init_completion(&comp);
    rc = ipmi_request_supply_msgs(ipmi_mh_user,
                                  (struct ipmi_addr*)&addr,
                                  0,
                                  &msg,
                                  &comp,
                                  &_halt_smi_msg,
                                  &_halt_recv_msg,
                                  0);
    if (rc) {
        ipmi_destroy_user(ipmi_mh_user);
        mutex_unlock(&_ipmi_mutex);
        printk(KERN_ERR "[%s()#%d: Exit, ipmi_request_supply_msgs() failed, rc=%d]\n",  __FUNCTION__, __LINE__, rc);
        return -3;
    }
    wait_for_completion(&comp);

    if (_halt_recv_msg.msg.data[0]) {  // IPMI return failed (none zero)
        ipmi_free_recv_msg(&_halt_recv_msg);
        ipmi_destroy_user(ipmi_mh_user);
        mutex_unlock(&_ipmi_mutex);
        printk(KERN_ERR "[%s()#%d: Exit, ipmi_request_supply_msgs() failed, rc=%d]\n",  __FUNCTION__, __LINE__, _halt_recv_msg.msg.data[0]);
        return -4;
    }

    if (result_len && result) {
        *result_len = _halt_recv_msg.msg.data_len - 1;
        memcpy(result, &_halt_recv_msg.msg.data[1], *result_len);
    }

    ipmi_free_recv_msg(&_halt_recv_msg);
    ipmi_destroy_user(ipmi_mh_user);
    msleep(10);
    mutex_unlock(&_ipmi_mutex);

#if 0 // For debugging
    printk(KERN_DEBUG "[%s()#%d: _halt_recv_msg.msg.data_len=0x%d]\n", __FUNCTION__, __LINE__, _halt_recv_msg.msg.data_len);
    printk(KERN_DEBUG "[%s()#%d: _halt_recv_msg.msg.data[0]=0x%02x]\n", __FUNCTION__, __LINE__, _halt_recv_msg.msg.data[0]);

    printk(KERN_DEBUG "[%s()#%d: ipmi exec success len=%u]\n", __FUNCTION__, __LINE__, result_len ? *result_len : -1);
    for (i = 0; i < _halt_recv_msg.msg.data_len - 1; i++) {
        printk(KERN_DEBUG "[%d]=0x%02x", i, _halt_recv_msg.msg.data[i]);
    }
    printk(KERN_DEBUG "\n");
#endif

    printk(KERN_DEBUG "[%s()#%d: Exit, result_len=%d]\n", __FUNCTION__, __LINE__, result_len ? *result_len : -1);
    return 0;
}
