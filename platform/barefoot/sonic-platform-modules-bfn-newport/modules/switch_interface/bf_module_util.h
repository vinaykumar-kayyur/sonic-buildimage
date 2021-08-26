/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * Prototype for Util macro/funcs (include IPMI) shared across all modules
 */

#ifndef __BF_MODULE_UTIL_H__
#define __BF_MODULE_UTIL_H__

#include <linux/ipmi.h>
#include <linux/ipmi_smi.h>

/* Default loglevel = LOG_WARN, which kzalloc g_data works.*/
#define DEFAULT_LOGLEVEL_IDX (0)
#define ACCTON_IPMI_NETFN 0x34
#define IPMI_TIMEOUT (5 * HZ)
#define IPMI_ERR_RETRY_TIMES 1


struct ipmi_data {
    struct completion read_complete;
    struct ipmi_addr address;
    ipmi_user_t user;
    int interface;

    struct kernel_ipmi_msg tx_message;
    long tx_msgid;

    void *rx_msg_data;
    unsigned short rx_msg_len;
    unsigned char  rx_result;
    int rx_recv_type;

    struct ipmi_user_hndl ipmi_hndlrs;
};


int userlevel_to_kernlevel(int level);
int kernlevel_to_userlevel(int level);
int register_device_and_driver(struct platform_driver *driver, char *name,
                               struct platform_device devs[], size_t num_dev,
                               const struct attribute_group *attrs[]);
void unregister_device_and_driver(struct platform_driver *driver,
        struct platform_device devs[], size_t num_dev);
int init_ipmi_data(struct ipmi_data *ipmi, int iface);
int ipmi_send_message(struct ipmi_data *ipmi, unsigned char cmd,
                      unsigned char *tx_data, unsigned short tx_len,
                      unsigned char *rx_data, unsigned short rx_len);
/* loglevel show/store funcs must be implemented for all modules */
ssize_t loglevel_show(struct device *dev, struct device_attribute *da,
                            char *buf);
ssize_t loglevel_store(struct device *dev, struct device_attribute *da,
                            const char *buf, size_t count);
/* debug show funcs must be implemented for all modules */
ssize_t debug_show(struct device *dev, struct device_attribute *da, char *buf);
/* show 'NA' */
ssize_t na_show(struct device *dev, struct device_attribute *da, char *buf);

/* Must be defined and assigned in bf_xxx_driver.c */
extern int *module_loglevel;

/*
 * Macro to print kernel message
 * Use g_data->loglevel to prefix the loglevel.
 */
#define bf_print(fmt, ...)                                                  \
    if(module_loglevel)                                                     \
        switch(*module_loglevel){                                           \
            case 0: printk(KERN_WARNING pr_fmt(fmt), ##__VA_ARGS__); break; \
            case 1: printk(KERN_ERR pr_fmt(fmt), ##__VA_ARGS__); break;     \
            case 2: printk(KERN_INFO pr_fmt(fmt), ##__VA_ARGS__); break;    \
            case 3: printk(KERN_DEBUG pr_fmt(fmt), ##__VA_ARGS__); break;   \
        }

/* Name-Mangled version of SENSOR_ATTR */
#define SENSOR_DEVICE_ATTR_M(_name, _mangle, _mode, _show, _store, _index)  \
struct sensor_device_attribute sensor_dev_attr_##_name##_mangle             \
    = SENSOR_ATTR(_name, _mode, _show, _store, _index)

/* Name-Mangled version of BF_DEV_ATTR */
#define BF_DEV_ATTR_RO_2(_name, _mangle, _func, _index)             \
    static SENSOR_DEVICE_ATTR_M(_name, _mangle, 0444, _func##_show, \
            NULL, _index)

#define BF_DEV_ATTR_RW_2(_name, _mangle, _func, _index)             \
    static SENSOR_DEVICE_ATTR_M(_name, _mangle, 0644, _func##_show, \
            _func##_store, _index)

/* Ordinary BF_DEV_ATTR */
#define BF_DEV_ATTR_RO(_name, _func, _index)            \
    BF_DEV_ATTR_RO_2(_name, , _func, _index)

#define BF_DEV_ATTR_RW(_name, _func, _index)            \
    BF_DEV_ATTR_RW_2(_name, , _func, _index)

/* Declare platform driver one-liner */
#define DECL_PLATFORM_DRIVER(_func, _name)              \
    static struct platform_driver _func##_driver = {    \
        .probe = _func##_probe,                         \
        .remove = _func##_remove,                       \
        .driver = {                                     \
            .name = _name,                              \
            .owner = THIS_MODULE,                       \
        },                                              \
    }

#define ATTR_SHOW_NUM_FUNC(_name, _val)                                     \
    ssize_t _name##_show(struct device *dev, struct device_attribute *da,   \
                                char *buf){                                 \
        return sprintf(buf, "%d\n", _val);                                  \
    }

#define ATTR_SHOW_STR_FUNC(_name, _str)                                     \
    ssize_t _name##_show(struct device *dev, struct device_attribute *da,   \
                                char *buf){                                 \
        return sprintf(buf, "%s\n", _str);                                  \
    }

#define ATTR_STORE_NUM_FUNC(_name, _var)                                       \
    ssize_t _name##_store(struct device *dev, struct device_attribute *da,     \
                                const char *buf, size_t count)                 \
    {                                                                          \
        long val = 0;                                                          \
        int status;                                                            \
        status = kstrtol(buf, 10, &val);                                       \
        if (status)                                                            \
            return status;                                                     \
        _var = userlevel_to_kernlevel(val);                                    \
        return count;                                                          \
    }

#endif //__BF_MODULE_UTIL_H__