/*
 * Copyright 2017 Broadcom
 * Copyright 2020 Google LLC
 * 
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License, version 2, as
 * published by the Free Software Foundation (the "GPL").
 * 
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License version 2 (GPLv2) for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * version 2 (GPLv2) along with this source code.
 */
/*
 * $Id: generic_cb.h $
 * $Copyright: (c) 2019 Broadcom Corp.
 * All Rights Reserved.$
 */
#ifndef __GENERIC_CB_H__
#define __GENERIC_CB_H__

#include <gmodule.h>
#include <kcom.h>
#include <linux/netdevice.h>

#define GENERIC_CB_NAME "generic"

extern int
generic_cb_init(void);

extern int
generic_cb_cleanup(void);

extern int
generic_filter_cb(uint8_t * pkt, int size, int dev_no, void *pkt_meta,
                  int chan, kcom_filter_t *kf);

/* generic data per interface */
typedef struct {
    struct list_head list;
    struct net_device *dev;
    uint16 id;
    uint8  port;
    uint16 vlan;
    uint16 qnum;
} generic_netif_t;

extern int
generic_netif_create_cb(int unit, kcom_netif_t *netif, struct net_device *dev);

extern int
generic_netif_destroy_cb(int unit, kcom_netif_t *netif, struct net_device *dev);

#endif /* __GENERIC_CB_H__ */
