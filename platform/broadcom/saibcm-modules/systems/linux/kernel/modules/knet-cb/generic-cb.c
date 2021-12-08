/*
 * Copyright 2017-2019 Broadcom
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
 * $Id: generic_cb.c $
 * $Copyright: (c) 2019 Broadcom Corp.
 * All Rights Reserved.$
 */

/*
 * TODO: https://buganizer.corp.google.com/issues/177370884
 * Current code duplicates knet interface cache and utility functions/defines
 * from psample-cb.c.
 * The generic_cb.c needs to be integrated with psample_cb.c.
 * Knet interface cache and meta data extraction utilities need to pulled out
 * into a shared file.
 */

/*
 * Driver for call-back functions for Linux KNET driver.
 *
 * This code is used to integrate KNET callback to
 * the generic infra for sending CPU pkts along with metadata to userspace
 * applications such as P4RT using genetlink interfaces.
 *
 * The module can be built from the standard Linux user mode target
 * directories using the following command (assuming bash), e.g.
 *
 *   cd $SDK/systems/linux/user/<target>
 *   make BUILD_KNET_CB=1
 *
 */
#ifdef GENL_PACKET_SUPPORT

#include <gmodule.h> /* Must be included first */
#include <kcom.h>
#include <bcm-knet.h>
#include <linux/if_vlan.h>
#include <linux/skbuff.h>
#include <linux/sched.h>
#include <linux/netdevice.h>
#include <linux/namei.h>
#include <net/net_namespace.h>
#include <net/genl-packet.h>
#include "generic-cb.h"

#define GENERIC_CB_DBG
#ifdef GENERIC_CB_DBG
extern int debug;

#define DBG_LVL_PRINT   0x1
#define DBG_LVL_PDMP    0x2
#define GENERIC_CB_DBG_PRINT(...) \
    if (debug & DBG_LVL_PRINT) {         \
        gprintk(__VA_ARGS__);  \
    }
#else
#define GENERIC_CB_DBG_PRINT(...)
#endif

/* HIGIG2 header fields */
#define SOC_HIGIG_SOP         (0xfb)
#define SOC_HIGIG_START(x)    ((x[0] >> 24) & 0xff)
#define SOC_HIGIG_DSTPORT(x)  ((x[1] >> 11) & 0x1f)
#define SOC_HIGIG_SRCPORT(x)  ((x[1] >> 16) & 0x1f)
#define SOC_HIGIG2_SOP        (0xfb) //0xfc - TODO: how can we differentiate between Higig and higig2?
#define SOC_HIGIG2_START(x)   ((x[0] >> 24) & 0xff)
#define SOC_HIGIG2_IS_MC(x)   ((x[0] >> 20) &  0x1)
#define SOC_HIGIG2_DSTPORT(x) ((x[0] >>  0) & 0xff)
#define SOC_HIGIG2_SRCPORT(x) ((x[1] >> 16) & 0xff)
#define SOC_DCB32_HG_OFFSET   (6)

#define DSTPORT_TYPE_DISCARD 1
#define DSTPORT_TYPE_MC      2

#define DSTPORT_TYPE_OFFSET  30
#define DSTPORT_TYPE_MASK    0x3
#define DSTPORT_TYPE_CLR(_dst) (_dst &= ~(DSTPORT_TYPE_MASK << DSTPORT_TYPE_OFFSET))
#define DSTPORT_TYPE_SET(_dst,_type) (_dst |= ((_type & DSTPORT_TYPE_MASK) << DSTPORT_TYPE_OFFSET))
#define DSTPORT_TYPE_GET(_dst) ((_dst >> DSTPORT_TYPE_OFFSET) & DSTPORT_TYPE_MASK)
#define DSTPORT_GET(_dst)      (_dst & ~(DSTPORT_TYPE_MASK << DSTPORT_TYPE_OFFSET))

#define FCS_SZ 4

#define GENERIC_QLEN_DFLT 1024
static int generic_qlen = GENERIC_QLEN_DFLT;
LKM_MOD_PARAM(generic_qlen, "i", int, 0);
MODULE_PARM_DESC(generic_qlen,
"generic cb queue length (default 1024 buffers)");

/* driver proc entry root */
static struct proc_dir_entry *generic_proc_root = NULL;
static struct proc_dir_entry *knet_cb_proc_root = NULL;

/* generic general info */
typedef struct {
    struct list_head netif_list;
    int netif_count;
    knet_hw_info_t hw;
    struct net *netns;
    spinlock_t lock;
} generic_info_t;
static generic_info_t g_generic_info = {0};

/* Maintain sampled pkt statistics */
typedef struct generic_stats_s {
    unsigned long pkts_f_generic_cb;
    unsigned long pkts_f_generic_mod;
    unsigned long pkts_f_handled;
    unsigned long pkts_f_tag_stripped;
    unsigned long pkts_f_dst_mc;
    unsigned long pkts_f_src_cpu;
    unsigned long pkts_f_dst_cpu;
    unsigned long pkts_c_qlen_cur;
    unsigned long pkts_c_qlen_hi;
    unsigned long pkts_d_qlen_max;
    unsigned long pkts_d_no_mem;
    unsigned long pkts_d_not_ready;
    unsigned long pkts_d_metadata;
    unsigned long pkts_d_meta_srcport;
    unsigned long pkts_d_meta_dstport;
    unsigned long pkts_d_invalid_size;
} generic_stats_t;
static generic_stats_t g_generic_stats = {0};

typedef struct generic_meta_s {
    int src_ifindex;
    int dst_ifindex;
    uint32 user_data;
} generic_meta_t;

typedef struct generic_pkt_s {
    struct list_head list;
    struct net *netns;
    generic_meta_t meta;
    struct sk_buff *skb;
} generic_pkt_t;

typedef struct generic_work_s {
    struct list_head pkt_list;
    struct work_struct wq;
    spinlock_t lock;
} generic_work_t;
static generic_work_t g_generic_work = {0};

static generic_netif_t*
generic_netif_lookup_by_port(int unit, int port)
{
    struct list_head *list;
    generic_netif_t *generic_netif = NULL;
    unsigned long flags;

    /* look for port from list of available net_devices */
    spin_lock_irqsave(&g_generic_info.lock, flags);
    list_for_each(list, &g_generic_info.netif_list) {
        generic_netif = (generic_netif_t*)list;
        if (generic_netif->port == port) {
            spin_unlock_irqrestore(&g_generic_info.lock, flags);
            return generic_netif;
        }
    }
    spin_unlock_irqrestore(&g_generic_info.lock, flags);
    return (NULL);
}
        
static int
generic_info_get (int unit, generic_info_t *generic_info)
{
    int rv = 0;
    if (!generic_info) {
        gprintk("%s: generic_info is NULL\n", __func__);
        return (-1);
    }

    /* get hw info */
    rv = bkn_hw_info_get(unit, &generic_info->hw);
    if (rv < 0) {
        gprintk("%s: failed to get hw info\n", __func__);
        return (-1);
    }

    GENERIC_CB_DBG_PRINT("%s: DCB type %d\n",
            __func__, generic_info->hw.dcb_type);
    return (0);
}

static int
generic_meta_srcport_get(uint8_t *pkt, void *pkt_meta)
{
    int srcport = 0;
    uint32_t *metadata = (uint32_t*)pkt_meta;

    switch(g_generic_info.hw.dcb_type) {
        case 36: /* TD3 */
        case 38: /* TH3 */
            break;
        case 32: /* TH1/TH2 */
        case 26: /* TD2 */
        case 23: /* HX4 */
            metadata += SOC_DCB32_HG_OFFSET;
        default:
            break;
    }

    if (SOC_HIGIG2_START(metadata) == SOC_HIGIG2_SOP) 
    {
        srcport = SOC_HIGIG2_SRCPORT(metadata);
    } 
    else if (SOC_HIGIG_START(metadata) == SOC_HIGIG_SOP) 
    {
        srcport = SOC_HIGIG_SRCPORT(metadata);
    } 
    else 
    {
        GENERIC_CB_DBG_PRINT("%s: Could not detect metadata sop type: 0x%02x (w[0]: 0x%04x)\n", __func__,
                SOC_HIGIG_START(metadata), metadata[0]);
        return -1;
    }
    return srcport;
}

static int
generic_meta_dstport_get(uint8_t *pkt, void *pkt_meta)
{
    int dstport = 0;
    uint32_t *metadata = (uint32_t*)pkt_meta;

    switch(g_generic_info.hw.dcb_type) {
        case 36: /* TD3 */
        case 38: /* TH3 */
            break;
        case 32: /* TH1/TH2 */
        case 26: /* TD2 */
        case 23: /* HX4 */
        default:
            metadata += SOC_DCB32_HG_OFFSET;
            break;
    }
    
    if (SOC_HIGIG2_START(metadata) == SOC_HIGIG2_SOP) 
    {
        if (SOC_HIGIG2_IS_MC(metadata))
        {
            DSTPORT_TYPE_CLR(dstport);
            DSTPORT_TYPE_SET(dstport, DSTPORT_TYPE_MC);
        }
        else
        {
            dstport = SOC_HIGIG2_DSTPORT(metadata);
        }
    } 
    else if (SOC_HIGIG_START(metadata) == SOC_HIGIG_SOP) 
    {
        dstport = SOC_HIGIG_DSTPORT(metadata);
    } 
    else 
    {
        GENERIC_CB_DBG_PRINT("%s: Could not detect metadata sop type: 0x%02x (w[0]: 0x%04x)\n", __func__,
                SOC_HIGIG_START(metadata), metadata[0]);
        return (-1);
    }
    return dstport;
}

static int
generic_meta_get(int unit, uint8_t *pkt, void *pkt_meta, generic_meta_t *generic_meta)
{
    int srcport, dstport, dstport_type;
    int src_ifindex = 0;
    int dst_ifindex = 0;
    generic_netif_t *generic_netif = NULL;

#ifdef GENERIC_CB_DBG
    if (debug & 0x1) {
        int i=0;
        uint8_t *meta = (uint8_t*)pkt_meta;
        GENERIC_CB_DBG_PRINT("%s: generic pkt metadata, header size %d\n",
                             __func__, g_generic_info.hw.pkt_hdr_size);
        for (i=0; i<64; i+=16) {
            GENERIC_CB_DBG_PRINT("%02x %02x %02x %02x %02x %02x %02x %02x %02x %02x %02x %02x %02x %02x %02x %02x\n",
                    meta[i+0], meta[i+1], meta[i+2], meta[i+3], meta[i+4], meta[i+5], meta[i+6], meta[i+7],
                    meta[i+8], meta[i+9], meta[i+10], meta[i+11], meta[i+12], meta[i+13], meta[i+14], meta[i+15]);
        }
    }
#endif

    /* parse pkt metadata for src and dst ports */
    srcport = generic_meta_srcport_get(pkt, pkt_meta);
    dstport = generic_meta_dstport_get(pkt, pkt_meta);
    if ((srcport == -1) || (dstport == -1)) {
        gprintk("%s: invalid srcport %d or dstport %d\n", __func__, srcport, dstport);
        return (-1);
    }

    /* find src port netif (no need to lookup CPU port) */
    if (srcport != 0) {
        if ((generic_netif = generic_netif_lookup_by_port(unit, srcport))) {
            src_ifindex = generic_netif->dev->ifindex;
        } else {
            src_ifindex = -1;
            g_generic_stats.pkts_d_meta_srcport++;
            GENERIC_CB_DBG_PRINT("%s: could not find srcport(%d)\n", __func__, srcport);
        }
    } else {
        g_generic_stats.pkts_f_src_cpu++;
    }

    dstport_type = DSTPORT_TYPE_GET(dstport);
    dstport = DSTPORT_GET(dstport);

    /* set generic dst type for MC pkts */
    if (dstport_type == DSTPORT_TYPE_MC) {
        g_generic_stats.pkts_f_dst_mc++;

    /* find dst port netif for UC pkts (no need to lookup CPU port) */
    } else if (dstport != 0) {
        if ((generic_netif = generic_netif_lookup_by_port(unit, dstport))) {
            dst_ifindex = generic_netif->dev->ifindex;
        } else {
            dst_ifindex = -1;
            g_generic_stats.pkts_d_meta_dstport++;
            GENERIC_CB_DBG_PRINT("%s: could not find dstport(%d)\n", __func__, dstport);
        }
    } else if (dstport == 0) {
        g_generic_stats.pkts_f_dst_cpu++;
    }

    GENERIC_CB_DBG_PRINT("%s: srcport %d, dstport %d, src_ifindex 0x%x, dst_ifindex 0x%x\n",
            __func__, srcport, dstport, src_ifindex, dst_ifindex);

    generic_meta->src_ifindex = src_ifindex;
    generic_meta->dst_ifindex = dst_ifindex;
    return (0);
}

static void dump_pkt(struct sk_buff *skb)
{
    int idx;
    char str[128];
    uint8_t *data = skb->data;

    for (idx = 0; idx < skb->len; idx++) {
        if ((idx & 0xf) == 0) {
            sprintf(str, "%04x: ", idx);
        }
        if ((idx & 0xf) == 8) {
            sprintf(&str[strlen(str)], "- ");
        }
        sprintf(&str[strlen(str)], "%02x ", data[idx]);
        if ((idx & 0xf) == 0xf) {
            sprintf(&str[strlen(str)], "\n");
            gprintk(str);
        }
    }
    if ((idx & 0xf) != 0) {
        sprintf(&str[strlen(str)], "\n");
        gprintk(str);
    }
}

static void
generic_task(struct work_struct *work)
{
    generic_work_t *generic_work = container_of(work, generic_work_t, wq);
    unsigned long flags;
    struct list_head *list_ptr, *list_next;
    generic_pkt_t *pkt;

    spin_lock_irqsave(&generic_work->lock, flags);
    list_for_each_safe(list_ptr, list_next, &generic_work->pkt_list) {
        /* dequeue pkt from list */
        pkt = list_entry(list_ptr, generic_pkt_t, list);
        list_del(list_ptr);
        g_generic_stats.pkts_c_qlen_cur--;
        spin_unlock_irqrestore(&generic_work->lock, flags);
 
        /* send to generic */
        if (pkt) {
            GENERIC_CB_DBG_PRINT("%s: netns 0x%p, src_ifdx 0x%x, dst_ifdx 0x%x\n",
                    __func__, pkt->netns, pkt->meta.src_ifindex,
                    pkt->meta.dst_ifindex);

            if (debug & DBG_LVL_PDMP) {
                dump_pkt(pkt->skb);
            }

            genl_packet_send_packet(pkt->netns,
                                  pkt->skb, 
                                  pkt->meta.src_ifindex,
                                  pkt->meta.dst_ifindex,
                                  pkt->meta.user_data);
            g_generic_stats.pkts_f_generic_mod++;
 
            dev_kfree_skb_any(pkt->skb);
            kfree(pkt);
        }
        spin_lock_irqsave(&generic_work->lock, flags);
    }
    spin_unlock_irqrestore(&generic_work->lock, flags);
}

int 
generic_filter_cb(uint8_t * pkt, int size, int dev_no, void *pkt_meta,
                  int chan, kcom_filter_t *kf)
{
    generic_meta_t meta;   
    int rv = 0;
    static int info_get = 0;
    unsigned long flags;
    generic_pkt_t *generic_pkt;
    struct sk_buff *skb;
    bool strip_tag = false;

    if (!info_get) {
        rv = generic_info_get (dev_no, &g_generic_info);
        if (rv < 0) {
            gprintk("%s: failed to get generic info\n", __func__);
            goto generic_FILTER_CB_PKT_HANDLED;
        }
        info_get = 1;
    }

    GENERIC_CB_DBG_PRINT("%s: pkt size %d, kf->dest_id %d, kf->cb_user_data %d\n",
            __func__, size, kf->dest_id, kf->cb_user_data);

    g_generic_stats.pkts_f_generic_cb++;

    /* get generic metadata */
    rv = generic_meta_get(dev_no, pkt, pkt_meta, &meta);
    if (rv < 0) {
        gprintk("%s: Could not parse pkt metadata\n", __func__);
        g_generic_stats.pkts_d_metadata++;
        goto generic_FILTER_CB_PKT_HANDLED;
    }

    meta.user_data =  kf->cb_user_data;

    /* Adjust original pkt size to remove 4B FCS */
    if (size < FCS_SZ) {
        g_generic_stats.pkts_d_invalid_size++;
        goto generic_FILTER_CB_PKT_HANDLED;
    } else {
       size -= FCS_SZ; 
    }

    GENERIC_CB_DBG_PRINT("%s: netns 0x%p, src_ifdx 0x%x, dst_ifdx 0x%x, user_data %d\n",
                      __func__, g_generic_info.netns, meta.src_ifindex, meta.dst_ifindex, meta.user_data);

    if (g_generic_stats.pkts_c_qlen_cur >= generic_qlen)
    {
        gprintk("%s: tail drop due to max qlen %d reached\n", __func__, generic_qlen);
        g_generic_stats.pkts_d_qlen_max++;
        goto generic_FILTER_CB_PKT_HANDLED;
    }

    if ((generic_pkt = kmalloc(sizeof(generic_pkt_t), GFP_ATOMIC)) == NULL)
    {
        gprintk("%s: failed to alloc generic mem for pkt\n", __func__);
        g_generic_stats.pkts_d_no_mem++;
        goto generic_FILTER_CB_PKT_HANDLED;
    }
    memcpy(&generic_pkt->meta, &meta, sizeof(generic_meta_t));
    generic_pkt->netns = g_generic_info.netns;

    if (size >= 16) {
        uint16_t vlan_proto = (uint16_t) ((pkt[12] << 8) | pkt[13]);
        uint16_t vlan = (uint16_t) ((pkt[14] << 8) | pkt[15]);
        strip_tag =  ((vlan_proto == 0x8100) || (vlan_proto == 0x88a8) || (vlan_proto == 0x9100))
                     && (vlan == 0xFFF);
    }

    if (strip_tag) {
        size -= 4;
    }

    if ((skb = dev_alloc_skb(size)) == NULL)
    {
        gprintk("%s: failed to alloc generic mem for pkt skb\n", __func__);
        g_generic_stats.pkts_d_no_mem++;
        goto generic_FILTER_CB_PKT_HANDLED;
    }

    /* setup skb by copying packet content */
    /*
     * Strip reserved vlan tag
     * FIXME: enhance GENL interface to support FILTER_TAG_STRIP,
     * FILTER_TAG_KEEP and FILTER_TAG_ORIGINAL
     */
    if(strip_tag) {
        memcpy(skb->data, pkt, 12);
        memcpy(skb->data + 12, pkt + 16, size - 12);
        g_generic_stats.pkts_f_tag_stripped++;
    } else {
        memcpy(skb->data, pkt, size);
    }

    skb_put(skb, size);
    skb->len = size;
    generic_pkt->skb = skb;

    spin_lock_irqsave(&g_generic_work.lock, flags);
    list_add_tail(&generic_pkt->list, &g_generic_work.pkt_list);

    g_generic_stats.pkts_c_qlen_cur++;
    if (g_generic_stats.pkts_c_qlen_cur > g_generic_stats.pkts_c_qlen_hi)
    {
        g_generic_stats.pkts_c_qlen_hi = g_generic_stats.pkts_c_qlen_cur;
    }

    schedule_work(&g_generic_work.wq);
    spin_unlock_irqrestore(&g_generic_work.lock, flags);

    /* expected rv values:
     * -ve for error
     * 0 for passthrough
     * 1 for packet handled
     *  */

    /* Set rv to packet handled */
    rv = 1;

generic_FILTER_CB_PKT_HANDLED:
    g_generic_stats.pkts_f_handled++;
    return rv;
}

int 
generic_netif_create_cb(int unit, kcom_netif_t *netif, struct net_device *dev)
{
    int found;
    struct list_head *list;
    generic_netif_t *generic_netif, *lgeneric_netif;
    unsigned long flags;

    if ((generic_netif = kmalloc(sizeof(generic_netif_t), GFP_ATOMIC)) == NULL) {
        gprintk("%s: failed to alloc generic mem for netif '%s'\n", 
                __func__, dev->name);
        return (-1);
    }

    spin_lock_irqsave(&g_generic_info.lock, flags);

    generic_netif->dev = dev;
    generic_netif->id = netif->id;
    generic_netif->port = netif->port;
    generic_netif->vlan = netif->vlan;
    generic_netif->qnum = netif->qnum;

    /* insert netif sorted by ID similar to bkn_knet_netif_create() */
    found = 0;
    list_for_each(list, &g_generic_info.netif_list) {
        lgeneric_netif = (generic_netif_t*)list;
        if (netif->id < lgeneric_netif->id) {
            found = 1;
            g_generic_info.netif_count++; 
            break;
        }
    }

    if (found) {
        /* Insert before the found interface */
        list_add_tail(&generic_netif->list, &lgeneric_netif->list);
    } else {
        /* Insert to end of list */
        list_add_tail(&generic_netif->list, &g_generic_info.netif_list);
    }
    
    spin_unlock_irqrestore(&g_generic_info.lock, flags);

    GENERIC_CB_DBG_PRINT("%s: added generic netif '%s'\n", __func__, dev->name);
    return (0);
}

int
generic_netif_destroy_cb(int unit, kcom_netif_t *netif, struct net_device *dev)
{
    int found = 0;
    struct list_head *list;
    generic_netif_t *generic_netif;
    unsigned long flags; 

    if (!netif || !dev) {
        gprintk("%s: netif or net_device is NULL\n", __func__);
        return (-1);
    }

    spin_lock_irqsave(&g_generic_info.lock, flags);
    
    list_for_each(list, &g_generic_info.netif_list) {
        generic_netif = (generic_netif_t*)list;
        if (netif->id == generic_netif->id) {
            found = 1; 
            list_del(&generic_netif->list);
            GENERIC_CB_DBG_PRINT("%s: removing generic netif '%s'\n", __func__, dev->name);
            kfree(generic_netif);
            g_generic_info.netif_count--; 
            break;
        }
    }

    spin_unlock_irqrestore(&g_generic_info.lock, flags);
    
    if (!found) {    
        gprintk("%s: netif ID %d not found!\n", __func__, netif->id);
        return (-1);
    }
    return (0);
}

/*
 * generic map Proc Read Entry
 */
static int
generic_proc_map_show(struct seq_file *m, void *v)
{
    struct list_head *list;
    generic_netif_t *generic_netif;
    unsigned long flags;

    seq_printf(m, "  Interface      logical port   ifindex\n");
    seq_printf(m, "-------------    ------------   -------\n");
    spin_lock_irqsave(&g_generic_info.lock, flags);
    
    list_for_each(list, &g_generic_info.netif_list) {
        generic_netif = (generic_netif_t*)list;
        seq_printf(m, "  %-14s %-14d %d\n",
                generic_netif->dev->name,
                generic_netif->port,
                generic_netif->dev->ifindex);
    }

    spin_unlock_irqrestore(&g_generic_info.lock, flags);
    return 0;
}

static int
generic_proc_map_open(struct inode * inode, struct file * file)
{
    return single_open(file, generic_proc_map_show, NULL);
}

struct file_operations generic_proc_map_file_ops = {
    owner:      THIS_MODULE,
    open:       generic_proc_map_open,
    read:       seq_read,
    llseek:     seq_lseek,
    write:      NULL,
    release:    single_release,
};

/*
 * generic debug Proc Read Entry
 */
static int
generic_proc_debug_show(struct seq_file *m, void *v)
{
    seq_printf(m, "BCM KNET %s Callback Config\n", GENERIC_CB_NAME);
    seq_printf(m, "  debug:           0x%x\n", debug);
    seq_printf(m, "  cmic_type:       %d\n",   g_generic_info.hw.cmic_type);
    seq_printf(m, "  dcb_type:        %d\n",   g_generic_info.hw.dcb_type);
    seq_printf(m, "  dcb_size:        %d\n",   g_generic_info.hw.dcb_size);
    seq_printf(m, "  pkt_hdr_size:    %d\n",   g_generic_info.hw.pkt_hdr_size);
    seq_printf(m, "  cdma_channels:   %d\n",   g_generic_info.hw.cdma_channels);
    seq_printf(m, "  netif_count:     %d\n",   g_generic_info.netif_count);
    seq_printf(m, "  queue length:    %d\n",   generic_qlen);

    return 0;
}

static int
generic_proc_debug_open(struct inode * inode, struct file * file)
{
    return single_open(file, generic_proc_debug_show, NULL);
}

/*
 * generic debug Proc Write Entry
 *
 *   Syntax:
 *   debug=<mask>
 *
 *   Where <mask> corresponds to the debug module parameter.
 *
 *   Examples:
 *   debug=0x1
 */
static ssize_t
generic_proc_debug_write(struct file *file, const char *buf,
                    size_t count, loff_t *loff)
{
    char debug_str[40];
    char *ptr;

    if (count > sizeof(debug_str)) {
        count = sizeof(debug_str) - 1;
        debug_str[count] = '\0';
    }
    if (copy_from_user(debug_str, buf, count)) {
        return -EFAULT;
    }

    if ((ptr = strstr(debug_str, "debug=")) != NULL) {
        ptr += 6;
        debug = simple_strtol(ptr, NULL, 0);
    } else {
        gprintk("Warning: unknown configuration setting\n");
    }

    return count;
}

struct file_operations generic_proc_debug_file_ops = {
    owner:      THIS_MODULE,
    open:       generic_proc_debug_open,
    read:       seq_read,
    llseek:     seq_lseek,
    write:      generic_proc_debug_write,
    release:    single_release,
};

static int
generic_proc_stats_show(struct seq_file *m, void *v)
{
    seq_printf(m, "BCM KNET %s Callback Stats\n", GENERIC_CB_NAME);
    seq_printf(m, "  DCB type %d\n",                          g_generic_info.hw.dcb_type);
    seq_printf(m, "  pkts filter generic cb         %10lu\n", g_generic_stats.pkts_f_generic_cb);
    seq_printf(m, "  pkts sent to generic module    %10lu\n", g_generic_stats.pkts_f_generic_mod);
    seq_printf(m, "  pkts handled by generic cb     %10lu\n", g_generic_stats.pkts_f_handled);
    seq_printf(m, "  pkts with vlan tag stripped    %10lu\n", g_generic_stats.pkts_f_tag_stripped);
    seq_printf(m, "  pkts with mc destination       %10lu\n", g_generic_stats.pkts_f_dst_mc);
    seq_printf(m, "  pkts with cpu source           %10lu\n", g_generic_stats.pkts_f_src_cpu);
    seq_printf(m, "  pkts with cpu destination      %10lu\n", g_generic_stats.pkts_f_dst_cpu);
    seq_printf(m, "  pkts current queue length      %10lu\n", g_generic_stats.pkts_c_qlen_cur);
    seq_printf(m, "  pkts high queue length         %10lu\n", g_generic_stats.pkts_c_qlen_hi);
    seq_printf(m, "  pkts drop max queue length     %10lu\n", g_generic_stats.pkts_d_qlen_max);
    seq_printf(m, "  pkts drop no memory            %10lu\n", g_generic_stats.pkts_d_no_mem);
    seq_printf(m, "  pkts drop generic not ready    %10lu\n", g_generic_stats.pkts_d_not_ready);
    seq_printf(m, "  pkts drop metadata parse error %10lu\n", g_generic_stats.pkts_d_metadata);
    seq_printf(m, "  pkts with invalid src port     %10lu\n", g_generic_stats.pkts_d_meta_srcport);
    seq_printf(m, "  pkts with invalid dst port     %10lu\n", g_generic_stats.pkts_d_meta_dstport);
    seq_printf(m, "  pkts with invalid orig pkt sz  %10lu\n", g_generic_stats.pkts_d_invalid_size);
    return 0;
}

static int
generic_proc_stats_open(struct inode * inode, struct file * file)
{
    return single_open(file, generic_proc_stats_show, NULL);
}

/*
 * generic stats Proc Write Entry
 *
 *   Syntax:
 *   write any value to clear stats 
 */
static ssize_t
generic_proc_stats_write(struct file *file, const char *buf,
                    size_t count, loff_t *loff)
{
    int qlen_cur = 0;
    unsigned long flags;

    spin_lock_irqsave(&g_generic_work.lock, flags);
    qlen_cur = g_generic_stats.pkts_c_qlen_cur;
    memset(&g_generic_stats, 0, sizeof(generic_stats_t));
    g_generic_stats.pkts_c_qlen_cur = qlen_cur;
    spin_unlock_irqrestore(&g_generic_work.lock, flags);

    return count;
}
struct file_operations generic_proc_stats_file_ops = {
    owner:      THIS_MODULE,
    open:       generic_proc_stats_open,
    read:       seq_read,
    llseek:     seq_lseek,
    write:      generic_proc_stats_write,
    release:    single_release,
};

int generic_cb_cleanup(void)
{
    cancel_work_sync(&g_generic_work.wq);
    remove_proc_entry("stats", generic_proc_root);
    remove_proc_entry("debug", generic_proc_root);
    remove_proc_entry("map"  , generic_proc_root);
    remove_proc_entry("generic", knet_cb_proc_root);
    return 0;
}

int generic_cb_init(void)
{
    #define PROCFS_MAX_PATH 1024
    char generic_procfs_path[PROCFS_MAX_PATH];
    struct proc_dir_entry *entry;
    struct path path;

    /* create procfs for generic */
    snprintf(generic_procfs_path, PROCFS_MAX_PATH, "bcm/knet-cb");
    if (kern_path ("/proc/bcm/knet-cb", LOOKUP_DIRECTORY, &path)) {
        knet_cb_proc_root = proc_mkdir(generic_procfs_path, NULL);
    }

    snprintf(generic_procfs_path, PROCFS_MAX_PATH, "%s/%s", generic_procfs_path, GENERIC_CB_NAME);
    generic_proc_root = proc_mkdir(generic_procfs_path, NULL);

    /* create procfs for generic stats */
    PROC_CREATE(entry, "stats", 0666, generic_proc_root, &generic_proc_stats_file_ops);
    if (entry == NULL) {
        gprintk("%s: Unable to create procfs entry '/procfs/%s/stats'\n", __func__, generic_procfs_path);
        return -1;
    }

    /* create procfs for getting netdev mapping */
    PROC_CREATE(entry, "map", 0666, generic_proc_root, &generic_proc_map_file_ops);
    if (entry == NULL) {
        gprintk("%s: Unable to create procfs entry '/procfs/%s/map'\n", __func__, generic_procfs_path);
        return -1;
    }

    /* create procfs for debug log */
    PROC_CREATE(entry, "debug", 0666, generic_proc_root, &generic_proc_debug_file_ops);
    if (entry == NULL) {
        gprintk("%s: Unable to create procfs entry '/procfs/%s/debug'\n", __func__, generic_procfs_path);
        return -1;
    }

    /* clear data structs */
    memset(&g_generic_stats, 0, sizeof(generic_stats_t));
    memset(&g_generic_info, 0, sizeof(generic_info_t));
    memset(&g_generic_work, 0, sizeof(generic_work_t));

    /* setup generic_info struct */
    INIT_LIST_HEAD(&g_generic_info.netif_list); 
    spin_lock_init(&g_generic_info.lock);

    /* setup generic work queue */
    spin_lock_init(&g_generic_work.lock); 
    INIT_LIST_HEAD(&g_generic_work.pkt_list); 
    INIT_WORK(&g_generic_work.wq, generic_task);

    /* get net namespace */ 
    g_generic_info.netns = get_net_ns_by_pid(current->pid);
    if (!g_generic_info.netns) {
        gprintk("%s: Could not get network namespace for pid %d\n", __func__, current->pid);
        return (-1);
    }
    GENERIC_CB_DBG_PRINT("%s: current->pid %d, netns 0x%p\n", __func__,
            current->pid, g_generic_info.netns);

    return 0;
}

#endif  // GENL_PACKET_SUPPORT