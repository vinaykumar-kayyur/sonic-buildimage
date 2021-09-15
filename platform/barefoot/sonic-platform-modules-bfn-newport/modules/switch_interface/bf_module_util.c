/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * Implementation of common module utilities, includes IPMI funcs
 */

/* Must be assigned with init_bf_print() by bf_xxx_driver.c */
const char *module_name="";
int *module_loglevel;

#define pr_fmt(fmt) "%s:%s: " fmt, module_name,  __func__

#include <linux/module.h>
#include <linux/platform_device.h>
#include "bf_module_util.h"

enum switch_log_levels{
    LOG_ERR = 0X1,
    LOG_WARN = 0X2,
    LOG_INFO = 0X4,
    LOG_DEBUG = 0X8
};

static int level_map[] = {LOG_WARN, LOG_ERR, LOG_INFO, LOG_DEBUG};

int userlevel_to_kernlevel(int level){
    int i, ret = DEFAULT_LOGLEVEL_IDX; //default level while not exist
    for(i=0 ; i<ARRAY_SIZE(level_map) ; i++){
        if(level_map[i] == level){
            ret = i;
            break;
        }
    }
    return ret;
}

int kernlevel_to_userlevel(int level){
    if(level >= ARRAY_SIZE(level_map))
        return -EINVAL;
    return level_map[level];
}

void init_bf_print(const char *modname, int *loglevel)
{
    module_loglevel = loglevel;
    module_name = modname;
}

void deinit_bf_print(void)
{
    static int dummy_loglevel = 0; //LOG_WARN
    module_loglevel = &dummy_loglevel;
    module_name = "";
}

static void blanked_device_release(struct device *dev){ }

static inline void init_pdev(struct platform_device *pdev, char *name, int id,
        const struct attribute_group **groups)
{
    pdev->name = name;
    pdev->id = id;
    pdev->dev.groups = groups;
    pdev->dev.release = blanked_device_release;
}

int register_device_and_driver(struct platform_driver *driver, char *name,
                               struct platform_device devs[], size_t num_dev,
                               const struct attribute_group *attrs[])
{
    int i, j, ret;

    ret = platform_driver_register(driver);
    if (ret < 0)
        goto dri_reg_err;

    for (i = 0 ; i < num_dev ; i++) {
        struct platform_device *pdev = &devs[i];
        init_pdev(pdev, name, i, attrs);
        ret = platform_device_register(pdev);
        if (ret != 0)
            goto dev_reg_err;
    }
    return 0;

dev_reg_err:
    for(j=0 ; j<i ; j++)
        platform_device_unregister(&devs[j]);
    platform_driver_unregister(driver);
dri_reg_err:
    return ret;
}

void unregister_device_and_driver(struct platform_driver *driver,
        struct platform_device devs[], size_t num_dev)
{
    int i;
    for (i = 0 ; i < num_dev ; i++)
        platform_device_unregister(&devs[i]);
    platform_driver_unregister(driver);
}

/* common DeviceAttribute handler functions for all modules */
ATTR_SHOW_STR_FUNC(na, "NA")
ATTR_SHOW_NUM_FUNC(loglevel, kernlevel_to_userlevel(*module_loglevel))
ATTR_STORE_NUM_FUNC(loglevel, *module_loglevel)

/* Functions to talk to the IPMI layer */

/* Dispatch IPMI messages to callers */
void ipmi_msg_handler(struct ipmi_recv_msg *msg, void *user_msg_data)
{
    unsigned short rx_len;
    struct ipmi_data *ipmi = user_msg_data;

    if (msg->msgid != ipmi->tx_msgid) {
        bf_print("Mismatch between received msgid "
            "(%02x) and transmitted msgid (%02x)!\n",
            (int)msg->msgid,
            (int)ipmi->tx_msgid);
        ipmi_free_recv_msg(msg);
        return;
    }

    ipmi->rx_recv_type = msg->recv_type;
    if (msg->msg.data_len > 0)
        ipmi->rx_result = msg->msg.data[0];
    else
        ipmi->rx_result = IPMI_UNKNOWN_ERR_COMPLETION_CODE;

    if (msg->msg.data_len > 1) {
        rx_len = msg->msg.data_len - 1;
        if (ipmi->rx_msg_len < rx_len)
            rx_len = ipmi->rx_msg_len;
        ipmi->rx_msg_len = rx_len;
        memcpy(ipmi->rx_msg_data, msg->msg.data + 1, ipmi->rx_msg_len);
    } else
        ipmi->rx_msg_len = 0;

    ipmi_free_recv_msg(msg);
    complete(&ipmi->read_complete);
}


/* Initialize IPMI address, message buffers and user data */
int init_ipmi_data(struct ipmi_data *ipmi, int iface)
{
    int err;

    init_completion(&ipmi->read_complete);

    /* Initialize IPMI address */
    ipmi->address.addr_type = IPMI_SYSTEM_INTERFACE_ADDR_TYPE;
    ipmi->address.channel = IPMI_BMC_CHANNEL;
    ipmi->address.data[0] = 0;
    ipmi->interface = iface;

    /* Initialize message buffers */
    ipmi->tx_msgid = 0;
    ipmi->tx_message.netfn = ACCTON_IPMI_NETFN;

    ipmi->ipmi_hndlrs.ipmi_recv_hndl = ipmi_msg_handler;

    /* Create IPMI messaging interface user */
    err = ipmi_create_user(ipmi->interface, &ipmi->ipmi_hndlrs,
                   ipmi, &ipmi->user);
    if (err < 0) {
        bf_print("Unable to register user with IPMI "
            "interface %d\n", ipmi->interface);
        return -EACCES;
    }

    return 0;
}

/* Send an IPMI command */
static int _ipmi_send_message(struct ipmi_data *ipmi, unsigned char cmd,
                                unsigned char *tx_data, unsigned short tx_len,
                                unsigned char *rx_data, unsigned short rx_len)
{
    int err;

    ipmi->tx_message.cmd      = cmd;
    ipmi->tx_message.data     = tx_data;
    ipmi->tx_message.data_len = tx_len;
    ipmi->rx_msg_data         = rx_data;
    ipmi->rx_msg_len          = rx_len;

    err = ipmi_validate_addr(&ipmi->address, sizeof(ipmi->address));
    if (err)
        goto addr_err;

    ipmi->tx_msgid++;
    err = ipmi_request_settime(ipmi->user, &ipmi->address, ipmi->tx_msgid,
                   &ipmi->tx_message, ipmi, 0, 0, 0);
    if (err)
        goto ipmi_req_err;

    err = wait_for_completion_timeout(&ipmi->read_complete, IPMI_TIMEOUT);
    if (!err)
        goto ipmi_timeout_err;

    return 0;

ipmi_timeout_err:
    err = -ETIMEDOUT;
    bf_print("request_timeout=%x\n", err);
    return err;
ipmi_req_err:
    bf_print("request_settime=%x\n", err);
    return err;
addr_err:
    bf_print("validate_addr=%x\n", err);
    return err;
}

/* Send an IPMI command with retry */
int ipmi_send_message(struct ipmi_data *ipmi, unsigned char cmd,
                      unsigned char *tx_data, unsigned short tx_len,
                      unsigned char *rx_data, unsigned short rx_len)
{
    int status = 0, retry = 0;

    for (retry = 0; retry <= IPMI_ERR_RETRY_TIMES; retry++) {
        status = _ipmi_send_message(ipmi, cmd, tx_data, tx_len, rx_data, rx_len);
        if (unlikely(status != 0)) {
            bf_print("ipmi_send_message_%d err status(%d)\r\n", retry, status);
            continue;
        }

        if (unlikely(ipmi->rx_result != 0)) {
            bf_print("ipmi_send_message_%d err result(%d)\r\n",
                                        retry, ipmi->rx_result);
            continue;
        }

        break;
    }

    return status;
}
