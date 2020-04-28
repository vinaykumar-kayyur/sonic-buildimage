/*
 *  mlacp_link_handler.c
 *  mLACP link handler
 *
 * Copyright(c) 2016-2019 Nephos/Estinet.
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms and conditions of the GNU General Public License,
 * version 2, as published by the Free Software Foundation.
 *
 * This program is distributed in the hope it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along with
 * this program; if not, see <http://www.gnu.org/licenses/>.
 *
 * The full GNU General Public License is included in this distribution in
 * the file called "COPYING".
 *
 *  Maintainer: jianjun, grace Li from nephos
 */

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <arpa/inet.h>
#include <sys/queue.h>
#include <sys/epoll.h>
#include <unistd.h>
#include <linux/un.h>
#include <linux/if_arp.h>
#include <sys/ioctl.h>
#include "../include/system.h"
#include "../include/logger.h"
#include "../include/mlacp_tlv.h"

#include "../include/iccp_csm.h"
#include "mclagdctl/mclagdctl.h"
#include "../include/iccp_cmd_show.h"
#include "../include/iccp_cli.h"
#include "../include/iccp_cmd.h"
#include "../include/mlacp_link_handler.h"
#include "../include/iccp_netlink.h"
#include "../include/scheduler.h"

/*****************************************
* Enum
*
* ***************************************/
typedef enum route_manipulate_type
{
    ROUTE_NONE,
    ROUTE_ADD,
    ROUTE_DEL
} ROUTE_MANIPULATE_TYPE_E;


/*****************************************
* Global
*
* ***************************************/
char g_ipv4_str[INET_ADDRSTRLEN];
char g_iccp_mlagsyncd_recv_buf[ICCP_MLAGSYNCD_RECV_MSG_BUFFER_SIZE] = { 0 };
char g_iccp_mlagsyncd_send_buf[ICCP_MLAGSYNCD_SEND_MSG_BUFFER_SIZE] = { 0 };

/*****************************************
* Tool : show ip string
*
* ***************************************/
char *show_ip_str(uint32_t ipv4_addr)
{
    struct in_addr in_addr;

    memset(g_ipv4_str, 0, sizeof(g_ipv4_str));
    in_addr.s_addr = ipv4_addr;
    inet_ntop(AF_INET, &in_addr, g_ipv4_str, INET_ADDRSTRLEN);

    return g_ipv4_str;
}

static int getHwAddr(char *buff, char *mac)
{
    int i = 0;
    unsigned int p[6];

    if ( buff == NULL || mac == NULL )
    {
        return MCLAG_ERROR;
    }

    if (sscanf(mac, "%x:%x:%x:%x:%x:%x", &p[0], &p[1], &p[2], &p[3], &p[4], &p[5]) < 6)
    {
        return MCLAG_ERROR;
    }

    for (i = 0; i < 6; i++)
    {
        buff[i] = p[i];
    }

    return 0;
}

/* Set an entry in the ARP cache. */
int mlacp_fsm_arp_set(char *ifname, uint32_t ip, char *mac)
{
    struct arpreq arpreq;
    struct sockaddr_in *sin;
    struct in_addr ina;
    int flags;
    int rc;
    int sock_fd = 0;

    ICCPD_LOG_DEBUG(__FUNCTION__, "Set arp entry for IP:%s  MAC:%s  ifname:%s", show_ip_str(htonl(ip)), mac, ifname);

    if (ifname == NULL || ip == 0 || mac == NULL)
    {
        return MCLAG_ERROR;
    }

    /*you must add this becasue some system will return "Invlid argument"
       because some argument isn't zero */
    memset(&arpreq, 0, sizeof(struct arpreq));
    sin = (struct sockaddr_in *)&arpreq.arp_pa;
    memset(sin, 0, sizeof(struct sockaddr_in));
    sin->sin_family = AF_INET;
    ina.s_addr = htonl(ip);
    memcpy(&sin->sin_addr, (char *)&ina, sizeof(struct in_addr));

    if (getHwAddr((char *)arpreq.arp_ha.sa_data, mac) < 0)
    {
        return MCLAG_ERROR;
    }

    strncpy(arpreq.arp_dev, ifname, 15);

    flags = ATF_COM;  //note, must set flag, if not,you will get error

    arpreq.arp_flags = flags;

    sock_fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock_fd < 0)
    {
        return MCLAG_ERROR;
    }

    rc = ioctl(sock_fd, SIOCSARP, &arpreq);
    if (rc < 0)
    {
        close(sock_fd);
        return MCLAG_ERROR;
    }

    close(sock_fd);

    return 0;
}

/* Delete an entry from the ARP cache. */
int mlacp_fsm_arp_del(char *ifname, uint32_t ip)
{
    struct arpreq arpreq;
    struct sockaddr_in *sin;
    struct in_addr ina;
    int rc;
    int sock_fd = 0;

    ICCPD_LOG_DEBUG(__FUNCTION__, "Del arp entry for IP : %s ifname:%s", show_ip_str(htonl(ip)), ifname);

    if (ifname == NULL || ip == 0)
    {
        return MCLAG_ERROR;
    }

    /*you must add this becasue some system will return "Invlid argument"
       because some argument isn't zero */
    memset(&arpreq, 0, sizeof(struct arpreq));

    sin = (struct sockaddr_in *)&arpreq.arp_pa;
    memset(sin, 0, sizeof(struct sockaddr_in));
    sin->sin_family = AF_INET;
    ina.s_addr = htonl(ip);
    memcpy(&sin->sin_addr, (char *)&ina, sizeof(struct in_addr));

    strncpy(arpreq.arp_dev, ifname, 15);

    sock_fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock_fd < 0)
    {
        return MCLAG_ERROR;
    }

    rc = ioctl(sock_fd, SIOCDARP, &arpreq);
    if (rc < 0)
    {
        close(sock_fd);
        return MCLAG_ERROR;
    }

    close(sock_fd);

    return 0;
}

static int arp_set_handler(struct CSM* csm,
                           struct LocalInterface* lif,
                           int add)
{
    struct Msg* msg = NULL;
    struct ARPMsg* arp_msg = NULL;
    char mac_str[18] = "";

    if (!csm || !lif)
        return 0;

    if (add)
        goto add_arp;
    else
        goto del_arp;

    /* Process Add */
 add_arp:
    if (MLACP(csm).current_state != MLACP_STATE_EXCHANGE)
        return 0;

    TAILQ_FOREACH(msg, &MLACP(csm).arp_list, tail)
    {
        mac_str[0] = '\0';
        arp_msg = (struct ARPMsg*)msg->buf;

        /* only process add*/
        if (arp_msg->op_type == ARP_SYNC_DEL)
            continue;

        /* find the ARP for lif_list*/
        if (strcmp(lif->name, arp_msg->ifname) != 0)
            continue;

        sprintf(mac_str, "%02x:%02x:%02x:%02x:%02x:%02x", arp_msg->mac_addr[0], arp_msg->mac_addr[1], arp_msg->mac_addr[2],
                arp_msg->mac_addr[3], arp_msg->mac_addr[4], arp_msg->mac_addr[5]);

        mlacp_fsm_arp_set(arp_msg->ifname, arp_msg->ipv4_addr, mac_str);
        /*ICCPD_LOG_DEBUG(__FUNCTION__, "Add dynamic ARP to kernel [%s]",
                        show_ip_str(htonl(arp_msg->ipv4_addr)));*/
    }
    goto done;

 del_arp:
    /* Process Del */
    TAILQ_FOREACH(msg, &MLACP(csm).arp_list, tail)
    {
        arp_msg = (struct ARPMsg*)msg->buf;

        /* find the ARP for lif_list*/
        if (strcmp(lif->name, arp_msg->ifname) != 0)
            continue;

        /* don't process del*/
        if (arp_msg->op_type == ARP_SYNC_DEL)
            continue;

        /* link broken, del all dynamic arp on the lif*/
        mlacp_fsm_arp_del(arp_msg->ifname, arp_msg->ipv4_addr);
        /*ICCPD_LOG_DEBUG(__FUNCTION__, "Del dynamic ARP [%s]",
                        show_ip_str(htonl(arp_msg->ipv4_addr)));*/
    }

 done:
    return 0;
}

/*****************************************
 * Port-Channel Status Handler
 *
 ****************************************/
static void set_route_by_linux_route(struct CSM* csm,
                                     struct LocalInterface *local_if,
                                     int is_add)
{
    /* TODO Need to remove this function
         when set static route with zebra works fine*/

    char ipv4_dest_str[INET_ADDRSTRLEN];
    char syscmd[128];
    char *ptr;
    int ret = 0;

    /* enable kernel forwarding support*/
    system("echo 1 > /proc/sys/net/ipv4/ip_forward");

    if (!csm || !local_if)
        return;

    sprintf(ipv4_dest_str, "%s", show_ip_str(htonl(local_if->ipv4_addr)));
    ptr = strrchr(ipv4_dest_str, '.'); strcpy(ptr, ".0\0");

#if 1
    /* set gw route*/
    /*sprintf(syscmd, "ip route %s %s/%d proto static metric 200 nexthop via %s > /dev/null 2>&1",*/
    sprintf(syscmd, "ip route %s %s/%d metric 200 nexthop via %s > /dev/null 2>&1",
            (is_add) ? "add" : "del", ipv4_dest_str, local_if->prefixlen,
            csm->peer_ip);
#else
    // set interface route
    sprintf(syscmd, "route %s -net %s/%d %s > /dev/null 2>&1",
            (is_add) ? "add" : "del", ipv4_dest_str, local_if->prefixlen,
            local_if->name);
#endif

    ret = system(syscmd);
    ICCPD_LOG_DEBUG(__FUNCTION__, "%s  ret = %d", syscmd, ret);

    return;
}

static void update_vlan_if_info(struct CSM *csm,
                                struct LocalInterface *local_if,
                                struct LocalInterface *vlan_if,
                                int po_state)
{
    if (!csm || !local_if || !vlan_if)
        return;

    vlan_if->mlacp_state = MLACP(csm).current_state;

    return;
}

static void update_l3_if_info(struct CSM *csm,
                              struct LocalInterface *local_if,
                              struct LocalInterface *l3_if,
                              int po_state)
{
    if (!csm || !l3_if)
        return;

    l3_if->mlacp_state = MLACP(csm).current_state;

    return;
}

static void update_po_if_info(struct CSM *csm,
                              struct LocalInterface *local_if,
                              int po_state)
{
    if (!csm || !local_if)
        return;

    /* update local po info*/
    if (local_if->po_active != po_state)
    {
        local_if->changed = 1;
        local_if->po_active = (po_state != 0);
        /*printf("update po [%s=%d]\n",local_if->name, local_if->po_active);*/
    }
    local_if->mlacp_state = MLACP(csm).current_state;

    return;
}

static void set_l3_itf_state(struct CSM *csm,
                             struct LocalInterface *set_l3_local_if,
                             ROUTE_MANIPULATE_TYPE_E route_type)
{
    if (!csm || !set_l3_local_if)
        return;

    if (set_l3_local_if && (route_type != ROUTE_NONE))
    {
        /*set_default_route(csm);*/

        /*ICCPD_LOG_DEBUG(__FUNCTION__, "  route set Interface = %s   route type = %d   route = %s   nexthop via = %s ",
                        set_l3_local_if->name, route_type, show_ip_str(htonl(set_l3_local_if->ipv4_addr)), csm->peer_ip );*/

        /* set static route*/
        if (route_type == ROUTE_ADD)
        {
            /*set_route_by_linux_route(csm, set_l3_local_if, 1);*/   /*add static route by linux route tool*/
            /*If the L3 intf is not Vlan, del ARP; else wait ARP age*/
            if (strncmp(set_l3_local_if->name, VLAN_PREFIX, 4) != 0)
            {
                arp_set_handler(csm, set_l3_local_if, 0);     /* del arp*/
            }
        }
        else if (route_type == ROUTE_DEL)
        {
            /*set_route_by_linux_route(csm, set_l3_local_if, 0);*/    /*del static route by linux route tool*/
            arp_set_handler(csm, set_l3_local_if, 1);     /* add arp*/
        }
    }

    return;
}

static int peer_po_is_alive(struct CSM *csm, int po_ifindex)
{
    struct PeerInterface *pif = NULL;
    int pif_active = 0;

    if (!csm)
        return 0;

    LIST_FOREACH(pif, &(MLACP(csm).pif_list), mlacp_next)
    {
        if (pif->type != IF_T_PORT_CHANNEL)
            continue;
        if (pif->po_id != po_ifindex)
            continue;

        if (pif->po_active)
            pif_active = 1; /*pif alive*/
        break;
    }

    return pif_active;
}

static void mlacp_clean_fdb(void)
{
    struct IccpSyncdHDr * msg_hdr;
    char *msg_buf = g_csm_buf;

    struct System *sys;

    sys = system_get_instance();
    if (sys == NULL)
        return;
    memset(msg_buf, 0, CSM_BUFFER_SIZE);
    msg_hdr = (struct IccpSyncdHDr *)msg_buf;
    msg_hdr->ver = 1;
    msg_hdr->type = MCLAG_MSG_TYPE_FLUSH_FDB;
    msg_hdr->len = sizeof(struct IccpSyncdHDr);

    if (sys->sync_fd)
        write(sys->sync_fd, msg_buf, msg_hdr->len);

    ICCPD_LOG_DEBUG(__FUNCTION__, "Notify mclagsyncd to clear FDB");

    return;
}

void set_peerlink_mlag_port_learn(struct LocalInterface *lif, int enable)
{
    struct IccpSyncdHDr * msg_hdr;
    mclag_sub_option_hdr_t * sub_msg;
    char *msg_buf = g_csm_buf;
    int msg_len;
    struct System *sys;

    sys = system_get_instance();
    if (sys == NULL)
        return;

    if (!lif)
        return;
    memset(msg_buf, 0, CSM_BUFFER_SIZE);
    msg_hdr = (struct IccpSyncdHDr *)msg_buf;
    msg_hdr->ver = 1;
    msg_hdr->type = MCLAG_MSG_TYPE_PORT_MAC_LEARN_MODE;

    msg_hdr->len = sizeof(struct IccpSyncdHDr);

    sub_msg = (mclag_sub_option_hdr_t*)&msg_buf[msg_hdr->len];
    sub_msg->op_type = MCLAG_SUB_OPTION_TYPE_MAC_LEARN_DISABLE;

    if (enable)
        sub_msg->op_type = MCLAG_SUB_OPTION_TYPE_MAC_LEARN_ENABLE;

    msg_len = strlen(lif->name);
    memcpy(sub_msg->data, lif->name, msg_len);

    sub_msg->op_len = msg_len;
    msg_hdr->len += sizeof(mclag_sub_option_hdr_t);
    msg_hdr->len += sub_msg->op_len;

    ICCPD_LOG_DEBUG(__FUNCTION__, "Send %s port MAC learn msg to mclagsyncd for %s",
                    sub_msg->op_type == MCLAG_SUB_OPTION_TYPE_MAC_LEARN_DISABLE ? "DISABLE":"ENABLE", lif->name);

    /*send msg*/
    if (sys->sync_fd)
        write(sys->sync_fd, msg_buf, msg_hdr->len);

    return;
}

static void set_peerlink_mlag_port_kernel_forward(
    struct CSM *csm,
    struct LocalInterface *lif,
    int enable)
{
    if (!csm || !csm->peer_link_if || !lif)
        return;

    char cmd[256] = { 0 };

    sprintf(cmd, "ebtables %s FORWARD -i %s -o %s -j DROP",
            "-D", csm->peer_link_if->name, lif->name);
    ICCPD_LOG_DEBUG(__FUNCTION__, " ebtable cmd  %s", cmd );
    system(cmd);

    sprintf(cmd, "ebtables %s FORWARD -i %s -o %s -j DROP",
            (enable) ? "-A" : "-D", csm->peer_link_if->name, lif->name);
    ICCPD_LOG_DEBUG(__FUNCTION__, " ebtable cmd  %s", cmd );
    system(cmd);

    return;
}

void update_peerlink_isolate_from_all_csm_lif(
    struct CSM* csm)
{
    struct LocalInterface *lif = NULL;
    struct IccpSyncdHDr * msg_hdr;
    mclag_sub_option_hdr_t * sub_msg;
    char msg_buf[4096];
    struct System *sys;

    char mlag_po_buf[512];
    int src_len = 0, dst_len = 0;

    sys = system_get_instance();
    if (sys == NULL)
        return;

    if (!csm || !csm->peer_link_if)
        return;

    memset(msg_buf, 0, 4095);
    memset(mlag_po_buf, 0, 511);

    msg_hdr = (struct IccpSyncdHDr *)msg_buf;
    msg_hdr->ver = 1;
    msg_hdr->type = MCLAG_MSG_TYPE_PORT_ISOLATE;
    msg_hdr->len = sizeof(struct IccpSyncdHDr);

    /*sub msg src*/
    sub_msg = (mclag_sub_option_hdr_t *)&msg_buf[msg_hdr->len];
    sub_msg->op_type = MCLAG_SUB_OPTION_TYPE_ISOLATE_SRC;

    if (csm->peer_link_if->type == IF_T_VXLAN)
    {
        /*TBD: vxlan tunnel port isolation will be supportted later*/
        return;
#if 0
        int begin_eth_port = 0;

        /*VTTNL0001;Ethernet0001,Ethernet0002*/
        /*src_len= strlen(csm->peer_link_if->name); */
        src_len += snprintf(src_buf + src_len, sizeof(src_buf) - src_len, "%s", csm->peer_link_if->name);
        src_len += snprintf(src_buf + src_len, sizeof(src_buf) - src_len, "%s", ";");

        /*traverse all ethernet port  */
        LIST_FOREACH(lif, &(sys->lif_list), system_next)
        {
            if (lif->type != IF_T_PORT)
                continue;

            /* need to isolate port,  get it's name */
            if (begin_eth_port != 0)
            {
                src_len += snprintf(src_buf + src_len, sizeof(src_buf) - src_len, "%s", ",");
            }

            src_len += snprintf(src_buf + src_len, sizeof(src_buf) - src_len, "%s", lif->name);
            begin_eth_port = 1;
        }
        memcpy(sub_msg->data, src_buf, src_len);

        ICCPD_LOG_DEBUG(__FUNCTION__, "isolate src %s, data %s, len %d", src_buf, sub_msg->data, src_len);
#endif
    }
    else
    {
        src_len = strlen(csm->peer_link_if->name);
        memcpy(sub_msg->data, csm->peer_link_if->name, src_len);
    }
    sub_msg->op_len = src_len;

    /*sub msg dst */
    msg_hdr->len += sub_msg->op_len;
    msg_hdr->len += sizeof(mclag_sub_option_hdr_t);
    sub_msg = (mclag_sub_option_hdr_t  *)&msg_buf[msg_hdr->len];
    sub_msg->op_type = MCLAG_SUB_OPTION_TYPE_ISOLATE_DST;

    /*traverse all portchannel member port and send msg to syncd */
    LIST_FOREACH(lif, &(MLACP(csm).lif_list), mlacp_next)
    {
        if (lif->type != IF_T_PORT_CHANNEL)
            continue;

        /* check pif port state and lif pochannel state */
        if (lif->isolate_to_peer_link == 1)
        {
            /* need to isolate port,  get it's member name */
            if (strlen(mlag_po_buf) != 0)
                dst_len += snprintf(mlag_po_buf + dst_len, sizeof(mlag_po_buf) - dst_len, "%s", ",");

            dst_len += snprintf(mlag_po_buf + dst_len, sizeof(mlag_po_buf) - dst_len, "%s", lif->portchannel_member_buf);
        }
    }

    sub_msg->op_len = dst_len;
    msg_hdr->len += sizeof(mclag_sub_option_hdr_t);
    msg_hdr->len += sub_msg->op_len;

    if (dst_len)
    {
        memcpy(sub_msg->data, mlag_po_buf, dst_len);
        ICCPD_LOG_DEBUG(__FUNCTION__, "Send port isolate msg to mclagsyncd, src port %s, dst port %s", csm->peer_link_if->name, mlag_po_buf);
    }
    else
    {
        ICCPD_LOG_DEBUG(__FUNCTION__, "Send port isolate msg to mclagsyncd, src port %s, dst port is NULL", csm->peer_link_if->name);
    }

    /*send msg*/
    if (sys->sync_fd)
        write(sys->sync_fd, msg_buf, msg_hdr->len);

    return;
}

static void set_peerlink_mlag_port_isolate(
    struct CSM *csm,
    struct LocalInterface *lif,
    int enable)
{
    if (!lif)
        return;

    lif->isolate_to_peer_link = enable;

    if (!csm || !csm->peer_link_if )
        return;

    if (MLACP(csm).current_state != MLACP_STATE_EXCHANGE)
        return;

    ICCPD_LOG_DEBUG(__FUNCTION__, "%s  port-isolate from %s to %s",
                    enable ? "Enable" : "Disable", csm->peer_link_if->name, lif->name);
    update_peerlink_isolate_from_all_csm_lif(csm);

    /* Kernel also needs to block traffic from peerlink to mlag-port*/
    set_peerlink_mlag_port_kernel_forward(csm, lif, enable);

    return;
}

void peerlink_port_isolate_cleanup(struct CSM* csm)
{
    struct LocalInterface *local_if = NULL;

    if (!csm)
        return;

    /* Clean all port block*/
    LIST_FOREACH(local_if, &(MLACP(csm).lif_list), mlacp_next)
    {
        if (local_if->type == IF_T_PORT_CHANNEL)
        {
            set_peerlink_mlag_port_isolate(csm, local_if, 0);
        }
    }

    return;
}

void update_peerlink_isolate_from_pif(
    struct CSM *csm,
    struct PeerInterface *pif,
    int pif_po_state,
    int new_create)
{
    struct LocalInterface *lif = NULL;
    int lif_po_state = 1;

    if (!csm || !csm->peer_link_if || !pif)
        return;
    if (new_create == 0 && pif_po_state == pif->po_active)
        return;
    if (MLACP(csm).current_state != MLACP_STATE_EXCHANGE)
        return;

    /* peer link changed*/
    LIST_FOREACH(lif, &(MLACP(csm).lif_list), mlacp_next)
    {
        if (strcmp(lif->name, pif->name) != 0)
            continue;

        lif_po_state = lif->po_active;
        break;
    }

    if (!lif)
    {
        ICCPD_LOG_WARN(__FUNCTION__, "Can't find local if for %s", pif->name);
        return;
    }

    ICCPD_LOG_DEBUG(__FUNCTION__, "From if %s local(%s) / peer(%s)",
                    lif->name,
                    (lif_po_state) ? "up" : "down",
                    (pif_po_state) ? "up" : "down");

    if (lif_po_state == 1)
    {
        if (pif_po_state == 1)
        {
            /* both peer-pair link up, enable port-isolate*/
            ICCPD_LOG_DEBUG(__FUNCTION__, "Enable port-isolate from %s to %s",
                            csm->peer_link_if->name, lif->name);
            set_peerlink_mlag_port_isolate(csm, lif, 1);
        }
        else
        {
            /* local link up, and peer link changes to down, disable port-isolate*/
            ICCPD_LOG_DEBUG(__FUNCTION__, "Disable port-isolate from %s to %s",
                            csm->peer_link_if->name, lif->name);
            set_peerlink_mlag_port_isolate(csm, lif, 0);
        }
    }
    else
    {
        ;/* local link down, do nothing*/
    }

    return;
}

static void update_peerlink_isolate_from_lif(
    struct CSM* csm,
    struct LocalInterface* lif,
    int lif_po_state)
{
    struct PeerInterface *pif = NULL;
    int pif_po_state = 1;

    if (!csm || !csm->peer_link_if || !lif)
        return;
    /*if (lif_po_state == lif->po_active) return;*/
    if (MLACP(csm).current_state != MLACP_STATE_EXCHANGE)
        return;

    /* local link changed*/
    LIST_FOREACH(pif, &(MLACP(csm).pif_list), mlacp_next)
    {
        if (strcmp(pif->name, lif->name) != 0)
            continue;

        pif_po_state = pif->po_active;
        break;
    }

    ICCPD_LOG_DEBUG(__FUNCTION__, "From if %s local(%s) / peer(%s)",
                    lif->name, (lif_po_state) ? "up" : "down", (pif_po_state) ? "up" : "down");

    if (lif_po_state == 1)
    {
        if (pif_po_state == 1)
        {
            /* both peer-pair link up, enable port-isolate*/
            ICCPD_LOG_DEBUG(__FUNCTION__, "Enable port-isolate from %s to %s",
                            csm->peer_link_if->name, lif->name);
            set_peerlink_mlag_port_isolate(csm, lif, 1);
        }
        else
        {
            /* peer link down, local link changes to up, disable port-isolate*/
            ICCPD_LOG_DEBUG(__FUNCTION__, " Disable port-isolate from %s to %s",
                            csm->peer_link_if->name, lif->name);
            set_peerlink_mlag_port_isolate(csm, lif, 0);
        }
    }
    else
    {
        ;/* local link down, do nothing*/
    }

    return;
}

static void update_l2_po_state(struct CSM *csm,
                               struct LocalInterface *lif,
                               int po_state)
{
    ROUTE_MANIPULATE_TYPE_E route_type = ROUTE_NONE;
    struct VLAN_ID *vlan = NULL;
    struct LocalInterface *set_l3_vlan_if = NULL;

    if (!csm || !lif)
        return;

    /*L2 po*/
    /*if (po_state != lif->po_active && po_state == 0)
       {
        mlacp_clean_fdb();
       }*/

    /*Is there any L3 vlan over L2 po?*/
    LIST_FOREACH(vlan, &(lif->vlan_list), port_next)
    {
        route_type = ROUTE_NONE;

        if (!vlan->vlan_itf)
            continue;

        /* If the po is under a vlan, update vlan state first*/
        update_vlan_if_info(csm, lif, vlan->vlan_itf, po_state);

        if (!local_if_is_l3_mode(vlan->vlan_itf))
            continue;

        /*NOTE
         * assume only one mlag per vlan
         * need to add rules for per mlag per vlan later (arp list?)
         */
        set_l3_vlan_if = vlan->vlan_itf;
        if (po_state != lif->po_active
            || MLACP(csm).current_state != set_l3_vlan_if->mlacp_state)
        {
            if (po_state == 1)
            {
                route_type = ROUTE_DEL;
            }
            else if (po_state == 0
                     && MLACP(csm).current_state == MLACP_STATE_EXCHANGE)
            {
                if (peer_po_is_alive(csm, lif->ifindex) == 1)
                    route_type = ROUTE_ADD;
            }
        }

        /*update_po_arp_list(csm, set_l3_vlan_if);*/
        set_l3_itf_state(csm, set_l3_vlan_if, route_type);
        update_l3_if_info(csm, lif, set_l3_vlan_if, po_state);
    }

    return;
}

static void update_l3_po_state(struct CSM *csm,
                               struct LocalInterface *lif,
                               int po_state)
{
    ROUTE_MANIPULATE_TYPE_E route_type = ROUTE_NONE;
    struct LocalInterface *set_l3_lif = NULL;

    /*L3 po*/
    set_l3_lif = lif;

    if (!csm || !lif)
        return;

    if (po_state != lif->po_active
        && po_state == 1)
    {
        /* po alive, clean static route & recover the ARP*/
        route_type = ROUTE_DEL;
    }
    else if (po_state != lif->po_active
             && po_state == 0
             && MLACP(csm).current_state == MLACP_STATE_EXCHANGE)
    {
        /* po is not alive & peer-link alive, set static route*/
        if (peer_po_is_alive(csm, lif->po_id) == 1)
            route_type = ROUTE_ADD;
    }
    else if (MLACP(csm).current_state != lif->mlacp_state
             && MLACP(csm).current_state == MLACP_STATE_EXCHANGE
             && po_state == 0)
    {
        /* when peer-pair link ready, set static route for broken po link*/
        if (peer_po_is_alive(csm, lif->po_id) == 1)
            route_type = ROUTE_ADD;
    }

    /*update_po_arp_list(csm, set_l3_lif);*/
    set_l3_itf_state(csm, set_l3_lif, route_type);
    update_l3_if_info(csm, lif, set_l3_lif, po_state);

    return;
}

int is_local_vlan_on(struct VLAN_ID* vlan_id_list)
{
    if (!vlan_id_list->vlan_itf)
        return 0;

    return 1;
}

void syn_arp_info_to_peer(struct CSM *csm, struct LocalInterface *local_if)
{
    struct Msg *msg = NULL;
    struct ARPMsg *arp_msg = NULL, *arp_info = NULL;
    struct Msg *msg_send = NULL;

    if (!csm || !local_if)
        return;

    if (!TAILQ_EMPTY(&(MLACP(csm).arp_list)))
    {
        TAILQ_FOREACH(msg, &MLACP(csm).arp_list, tail)
        {
            arp_info = (struct ARPMsg*)msg->buf;

            if (strcmp(arp_info->ifname, local_if->name) != 0)
                continue;

            arp_msg = (struct ARPMsg*)msg->buf;
            arp_msg->op_type = ARP_SYNC_ADD;

            if (iccp_csm_init_msg(&msg_send, (char*)arp_msg, sizeof(struct ARPMsg)) == 0)
            {
                TAILQ_INSERT_TAIL(&(MLACP(csm).arp_msg_list), msg_send, tail);
                /*ICCPD_LOG_DEBUG( __FUNCTION__, "Enqueue ARP[ADD] for %s",
                                 show_ip_str(htonl(arp_msg->ipv4_addr)));*/
            }
            else
                ICCPD_LOG_WARN(__FUNCTION__, "Failed to enqueue ARP[ADD] for %s",
                                show_ip_str(htonl(arp_msg->ipv4_addr)));
        }
    }

    return;
}

void update_stp_peer_link(struct CSM *csm,
                          struct PeerInterface *pif,
                          int po_state, int new_create)
{
    struct LocalInterface *lif = NULL;
    struct VLAN_ID *vlan = NULL;

    if (!csm || !pif)
        return;
    if (new_create == 0 && po_state == pif->po_active)
        return;

    LIST_FOREACH(lif, &(MLACP(csm).lif_list), mlacp_next)
    {
        if (strcmp(lif->name, pif->name) != 0)
            continue;

        /* update lif route if pif link status changes */
        if (local_if_is_l3_mode(lif))
        {
            if (po_state == 1 && lif->po_active == 0)
                set_l3_itf_state(csm, lif, ROUTE_ADD);
            else if (po_state == 0 && lif->po_active == 0)
                set_l3_itf_state(csm, lif, ROUTE_DEL);

            /*If pif change to active, and local is also active, syn arp to peer*/
            if (po_state == 1 && lif->po_active == 1)
            {
                syn_arp_info_to_peer(csm, lif);
            }
        }
        else
        {
            LIST_FOREACH(vlan, &(lif->vlan_list), port_next)
            {
                if (!is_local_vlan_on(vlan))
                    continue;
                if (!local_if_is_l3_mode(vlan->vlan_itf))
                    continue;

                /*NOTE
                 * assume only one mlag per bridge
                 * need to add rules for per mlag per bridge later (arp list?)
                 */
                if (po_state == 1 && lif->po_active == 0)
                    set_l3_itf_state(csm, vlan->vlan_itf, ROUTE_ADD);
                else if (po_state == 0 && lif->po_active == 0)
                    set_l3_itf_state(csm, vlan->vlan_itf, ROUTE_DEL);

                /*If pif change to active, and local is also active, syn arp to peer*/
                if (po_state == 1 && lif->po_active == 1)
                {
                    syn_arp_info_to_peer(csm, vlan->vlan_itf);
                }
            }
        }

        break;
    }

    return;
}

void iccp_get_fdb_change_from_syncd( void)
{
    struct IccpSyncdHDr * msg_hdr;
    char msg_buf[512];
    struct System *sys;

    sys = system_get_instance();
    if (sys == NULL)
        return;

    memset(msg_buf, 0, 512);

    msg_hdr = (struct IccpSyncdHDr *)msg_buf;
    msg_hdr->ver = 1;
    msg_hdr->type =  MCLAG_MSG_TYPE_GET_FDB_CHANGES;
    msg_hdr->len = sizeof(struct IccpSyncdHDr);

    ICCPD_LOG_DEBUG(__FUNCTION__, "Send get fdb change msg to mclagsyncd");

    /*send msg*/
    if (sys->sync_fd > 0)
        write(sys->sync_fd, msg_buf, msg_hdr->len);

    return;
}

void iccp_send_fdb_entry_to_syncd( struct MACMsg* mac_msg, uint8_t mac_type)
{
    struct IccpSyncdHDr * msg_hdr;
    char msg_buf[512];
    struct System *sys;
    struct mclag_fdb_info * mac_info;

    sys = system_get_instance();
    if (sys == NULL)
        return;

    memset(msg_buf, 0, 512);

    msg_hdr = (struct IccpSyncdHDr *)msg_buf;
    msg_hdr->ver = 1;
    msg_hdr->type = MCLAG_MSG_TYPE_SET_FDB;

    /*mac msg */
    mac_info = (struct mclag_fdb_info *)&msg_buf[sizeof(struct IccpSyncdHDr)];
    mac_info->vid = mac_msg->vid;
    memcpy(mac_info->port_name, mac_msg->ifname, MAX_L_PORT_NAME);
    memcpy(mac_info->mac, mac_msg->mac_str, ETHER_ADDR_STR_LEN);
    mac_info->type = mac_type;
    mac_info->op_type = mac_msg->op_type;
    msg_hdr->len = sizeof(struct IccpSyncdHDr) + sizeof(struct mclag_fdb_info);

    ICCPD_LOG_DEBUG(__FUNCTION__, "Send mac %s msg to mclagsyncd, vid %d ; ifname %s ; mac %s; type %s",
                    mac_info->op_type == MAC_SYNC_ADD ? "add" : "del", mac_info->vid, mac_info->port_name, mac_info->mac, mac_info->type == MAC_TYPE_STATIC ? "static" : "dynamic");

    /*send msg*/
    if (sys->sync_fd > 0 )
        write(sys->sync_fd, msg_buf, msg_hdr->len);

    return;
}

void add_mac_to_chip(struct MACMsg* mac_msg, uint8_t mac_type)
{
    mac_msg->op_type = MAC_SYNC_ADD;
    iccp_send_fdb_entry_to_syncd( mac_msg, mac_type);

    return;
}

void del_mac_from_chip(struct MACMsg* mac_msg)
{
    mac_msg->op_type = MAC_SYNC_DEL;
    iccp_send_fdb_entry_to_syncd(  mac_msg, mac_msg->fdb_type);

    return;
}

uint8_t set_mac_local_age_flag(struct CSM *csm, struct MACMsg* mac_msg, uint8_t set )
{
    uint8_t new_age_flag = 0;
    struct Msg *msg = NULL;

    new_age_flag = mac_msg->age_flag;

    if (set == 0)/*remove age flag*/
    {
        new_age_flag &= ~MAC_AGE_LOCAL;

        ICCPD_LOG_DEBUG(__FUNCTION__, "Remove local age flag: %d ifname  %s, add %s vlan-id %d, age_flag %d",
                            new_age_flag, mac_msg->ifname, mac_msg->mac_str, mac_msg->vid, mac_msg->age_flag);

        /*send mac MAC_SYNC_ADD message to peer*/
        if (MLACP(csm).current_state == MLACP_STATE_EXCHANGE)
        {
            mac_msg->op_type = MAC_SYNC_ADD;
            if (iccp_csm_init_msg(&msg, (char*)mac_msg, sizeof(struct MACMsg)) == 0)
            {
                TAILQ_INSERT_TAIL(&(MLACP(csm).mac_msg_list), msg, tail);
                /*ICCPD_LOG_DEBUG(__FUNCTION__, "MAC-msg-list enqueue: %s, add %s vlan-id %d, age_flag %d",
                               mac_msg->ifname, mac_msg->mac_str, mac_msg->vid, mac_msg->age_flag);*/
            }
            else
            {
                ICCPD_LOG_WARN(__FUNCTION__, "Failed to enqueue MAC-msg-list: %s, add %s vlan-id %d, age_flag %d",
                               mac_msg->ifname, mac_msg->mac_str, mac_msg->vid, mac_msg->age_flag);
                }
        }
    }
    else/*set age flag*/
    {
        new_age_flag |= MAC_AGE_LOCAL;

        ICCPD_LOG_DEBUG(__FUNCTION__, "Add local age flag: %s, add %s vlan-id %d, age_flag %d",
                            mac_msg->ifname, mac_msg->mac_str, mac_msg->vid, mac_msg->age_flag);

        /*send mac MAC_SYNC_DEL message to peer*/
        if (MLACP(csm).current_state == MLACP_STATE_EXCHANGE)
        {
            mac_msg->op_type = MAC_SYNC_DEL;
            if (iccp_csm_init_msg(&msg, (char*)mac_msg, sizeof(struct MACMsg)) == 0)
            {
                TAILQ_INSERT_TAIL(&(MLACP(csm).mac_msg_list), msg, tail);
                /*ICCPD_LOG_DEBUG(__FUNCTION__, "MAC-msg-list enqueue: %s, add %s vlan-id %d, age_flag %d",
                                mac_msg->ifname, mac_msg->mac_str, mac_msg->vid, mac_msg->age_flag);*/
            }
            else
            {
                ICCPD_LOG_WARN(__FUNCTION__, "Failed to enqueue MAC-msg-list: %s, del %s vlan-id %d, age_flag %d",
                               mac_msg->ifname, mac_msg->mac_str, mac_msg->vid, mac_msg->age_flag);
            }
        }
    }

    return new_age_flag;
}

uint8_t set_l2mc_local_del_flag(struct CSM *csm, struct L2MCMsg* l2mc_msg, uint8_t set, uint8_t update_peer )
{
    uint8_t new_del_flag = 0;

    new_del_flag = l2mc_msg->del_flag;

    if (set == 0)/*remove del flag*/
    {
        if (new_del_flag & L2MC_DEL_LOCAL)
        {
            new_del_flag &= ~L2MC_DEL_LOCAL;

            /*send L2MC_SYNC_ADD message to peer*/
            if ((MLACP(csm).current_state == MLACP_STATE_EXCHANGE) && update_peer)
            {
                l2mc_msg->op_type = L2MC_SYNC_ADD;
                ICCPD_LOG_DEBUG(__FUNCTION__, "saddr %s, gaddr %s, vlan %d ifname %s type %d",
                    l2mc_msg->saddr, l2mc_msg->gaddr, l2mc_msg->vid, l2mc_msg->ifname, l2mc_msg->op_type);
                if (!L2MC_IN_MSG_LIST(&(MLACP(csm).l2mc_msg_list), l2mc_msg, tail))
                {
                    TAILQ_INSERT_TAIL(&(MLACP(csm).l2mc_msg_list), l2mc_msg, tail);
                }
            }
        }
    }
    else/*set del flag*/
    {
        if (!(new_del_flag & L2MC_DEL_LOCAL))
        {
            new_del_flag |= L2MC_DEL_LOCAL;

            /*send L2MC_SYNC_DEL message to peer*/
            if ((MLACP(csm).current_state == MLACP_STATE_EXCHANGE) && update_peer)
            {
                l2mc_msg->op_type = L2MC_SYNC_DEL;
                ICCPD_LOG_DEBUG(__FUNCTION__, "saddr %s, gaddr %s, vlan %d ifname %s type %d",
                    l2mc_msg->saddr, l2mc_msg->gaddr, l2mc_msg->vid, l2mc_msg->ifname, l2mc_msg->op_type);
                if (!L2MC_IN_MSG_LIST(&(MLACP(csm).l2mc_msg_list), l2mc_msg, tail))
                {
                    TAILQ_INSERT_TAIL(&(MLACP(csm).l2mc_msg_list), l2mc_msg, tail);
                }
            }
        }
    }
    return new_del_flag;
}

/*l2mc mrouter*/
uint8_t set_l2mcmrtr_local_del_flag(struct CSM *csm, struct L2MCMsg* l2mc_msg, uint8_t set, uint8_t update_peer )
{
    uint8_t new_del_flag = 0;

    new_del_flag = l2mc_msg->del_flag;

    if (set == 0)/*remove del flag*/
    {
        if (new_del_flag & L2MC_DEL_LOCAL)
        {
            new_del_flag &= ~L2MC_DEL_LOCAL;

            /*send L2MC_SYNC_ADD message to peer*/
            if ((MLACP(csm).current_state == MLACP_STATE_EXCHANGE) && update_peer)
            {
                l2mc_msg->op_type = L2MC_SYNC_ADD;
                ICCPD_LOG_DEBUG(__FUNCTION__, "vlan %d ifname %s type %d",
                    l2mc_msg->vid, l2mc_msg->ifname, l2mc_msg->op_type);
                if (!L2MC_IN_MSG_LIST(&(MLACP(csm).l2mcmrtr_msg_list), l2mc_msg, tail))
                {
                    TAILQ_INSERT_TAIL(&(MLACP(csm).l2mcmrtr_msg_list), l2mc_msg, tail);
                }
            }
        }
    }
    else/*set del flag*/
    {
        if (!(new_del_flag & L2MC_DEL_LOCAL))
        {
            new_del_flag |= L2MC_DEL_LOCAL;

            /*send L2MC_SYNC_DEL message to peer*/
            if ((MLACP(csm).current_state == MLACP_STATE_EXCHANGE) && update_peer)
            {
                l2mc_msg->op_type = L2MC_SYNC_DEL;
                ICCPD_LOG_DEBUG(__FUNCTION__, "vlan %d ifname %s type %d",
                    l2mc_msg->vid, l2mc_msg->ifname, l2mc_msg->op_type);
                if (!L2MC_IN_MSG_LIST(&(MLACP(csm).l2mcmrtr_msg_list), l2mc_msg, tail))
                {
                    TAILQ_INSERT_TAIL(&(MLACP(csm).l2mcmrtr_msg_list), l2mc_msg, tail);
                }
            }
        }
    }
    return new_del_flag;
}


void iccp_send_l2mc_entry_to_syncd( struct L2MCMsg* l2mc_msg, uint8_t l2mc_type, uint8_t l2mc_mlag_type, uint8_t op_type)
{
    struct IccpSyncdHDr * msg_hdr;
    char *msg_buf = g_iccp_mlagsyncd_send_buf;
    struct System *sys;
    struct mclag_l2mc_info * l2mc_info;
    ssize_t rc;

    sys = system_get_instance();
    if (sys == NULL)
    {
        ICCPD_LOG_ERR(__FUNCTION__, "Invalid system instance");
        return;
    }

    memset(msg_buf, 0, ICCP_MLAGSYNCD_SEND_MSG_BUFFER_SIZE);

    msg_hdr = (struct IccpSyncdHDr *)msg_buf;
    msg_hdr->ver = ICCPD_TO_MCLAGSYNCD_HDR_VERSION;
    msg_hdr->type = l2mc_mlag_type;

    /*mac msg */
    l2mc_info = (struct mclag_l2mc_info *)&msg_buf[sizeof(struct IccpSyncdHDr)];
    l2mc_info->vid = l2mc_msg->vid;
    memcpy(l2mc_info->port_name, l2mc_msg->ifname, MAX_L_PORT_NAME);
    if (l2mc_mlag_type == MCLAG_MSG_TYPE_SET_L2MC)
    {
        memcpy(l2mc_info->saddr, l2mc_msg->saddr, INET_ADDRSTRLEN);
        memcpy(l2mc_info->gaddr, l2mc_msg->gaddr, INET_ADDRSTRLEN);
    }
    l2mc_info->type = l2mc_type;
    l2mc_info->op_type = op_type;
    msg_hdr->len = sizeof(struct IccpSyncdHDr) + sizeof(struct mclag_l2mc_info);

    if (l2mc_mlag_type == MCLAG_MSG_TYPE_SET_L2MC)
    {
        ICCPD_LOG_NOTICE(__FUNCTION__, "fd %d write l2mc msg vid : %d ; ifname %s ; "
            "saddr %s gaddr %s l2mc type %d ; op type %d  ", sys->sync_fd, l2mc_info->vid,
            l2mc_info->port_name, l2mc_info->saddr, l2mc_info->gaddr, l2mc_info->type, op_type);
    }
    else
    {
        ICCPD_LOG_NOTICE(__FUNCTION__, "fd %d write l2mc mrouter msg vid : %d ; ifname %s ; "
            "l2mc mrouter type %d ; op type %d  ", sys->sync_fd, l2mc_info->vid,
            l2mc_info->port_name, l2mc_info->type, op_type);
    }


    /*send msg*/
    if (sys->sync_fd > 0 )
    {
        rc = write(sys->sync_fd,msg_buf, msg_hdr->len);
        if ((rc <= 0) || (rc != msg_hdr->len))
        {
            ICCPD_LOG_ERR(__FUNCTION__, "Failed to write, rc %d", rc);
        }
    }
    else
    {
        ICCPD_LOG_ERR(__FUNCTION__, "Invalid sync_fd Failed to write, fd %d", sys->sync_fd);
    }

    return;
}

void add_l2mc_to_chip(struct L2MCMsg* l2mc_msg, uint8_t l2mc_type, uint8_t l2mc_mlag_type)
{
    iccp_send_l2mc_entry_to_syncd( l2mc_msg, l2mc_type, l2mc_mlag_type, L2MC_SYNC_ADD);

    return;
}

void del_l2mc_from_chip(struct L2MCMsg* l2mc_msg, uint8_t l2mc_mlag_type)
{
    iccp_send_l2mc_entry_to_syncd(  l2mc_msg, l2mc_msg->l2mc_type, l2mc_mlag_type, L2MC_SYNC_DEL);

    return;
}

/*Deal with mac add,del,move when portchannel up or down*/
static void update_l2_mac_state(struct CSM *csm,
                                struct LocalInterface *lif,
                                int po_state)
{
    struct Msg* msg = NULL;
    struct MACMsg* mac_msg = NULL;

    if (!csm || !lif)
        return;

    TAILQ_FOREACH(msg, &MLACP(csm).mac_list, tail)
    {
        mac_msg = (struct MACMsg*)msg->buf;

        /* find the MAC for this interface*/
        if (strcmp(lif->name, mac_msg->origin_ifname) != 0)
            continue;

        /*portchannel down*/
        if (po_state == 0)
        {
            ICCPD_LOG_DEBUG(__FUNCTION__, "Intf %s down, age local MAC %s vlan-id %d",
                            mac_msg->ifname, mac_msg->mac_str, mac_msg->vid);

            mac_msg->age_flag = set_mac_local_age_flag(csm, mac_msg, 1);

            if (mac_msg->age_flag == (MAC_AGE_LOCAL | MAC_AGE_PEER))
            {
                /*send mac del message to mclagsyncd.*/
                if (mac_msg->fdb_type != MAC_TYPE_STATIC)
                    del_mac_from_chip(mac_msg);

                ICCPD_LOG_DEBUG(__FUNCTION__, "Intf %s down, del MAC %s vlan-id %d",
                                mac_msg->ifname, mac_msg->mac_str, mac_msg->vid);

                /*If local and peer both aged, del the mac*/
                TAILQ_REMOVE(&(MLACP(csm).mac_list), msg, tail);
                free(msg->buf);
                free(msg);
            }
            else
            {
                /*If local is aged but peer is not aged, redirect the mac to peer-link*/
                if (strlen(csm->peer_itf_name) != 0)
                {
                    /*Send mac add message to mclagsyncd. fdb_type is not changed*/
                    /*Is need to delete the old item before add?(Old item probably is static)*/
                    if (csm->peer_link_if && csm->peer_link_if->state == PORT_STATE_UP)
                    {
                        memcpy(mac_msg->ifname, csm->peer_itf_name, IFNAMSIZ);
                        add_mac_to_chip(mac_msg, MAC_TYPE_DYNAMIC);
                    }
                    else
                    {
                        /*must redirect but peerlink is down, del mac from ASIC*/
                        /*if peerlink change to up, mac will add back to ASIC*/
                        del_mac_from_chip(mac_msg);
                        memcpy(mac_msg->ifname, csm->peer_itf_name, IFNAMSIZ);
                    }

                    ICCPD_LOG_DEBUG(__FUNCTION__, "Intf %s down, redirect MAC %s vlan-id %d to peer-link %s",
                                    mac_msg->ifname, mac_msg->mac_str, mac_msg->vid, csm->peer_itf_name);
                }
                else
                {
                    /*peer-link is not configured, del mac from ASIC, mac still in mac_list*/
                    del_mac_from_chip(mac_msg);

                    ICCPD_LOG_DEBUG(__FUNCTION__, "Intf %s down, peer-link is not configured: MAC %s vlan-id %d",
                                    mac_msg->ifname, mac_msg->mac_str, mac_msg->vid);
                }
            }
        }
        else /*portchannel up*/
        {
            /*the old item is redirect to peerlink for portchannel down*/
            /*when this portchannel up, recover the mac back*/
            if (strcmp(mac_msg->ifname, csm->peer_itf_name) == 0)
            {
                ICCPD_LOG_DEBUG(__FUNCTION__, "Intf %s up, redirect MAC %s vlan-id %d from peerlink to %s",
                                mac_msg->origin_ifname, mac_msg->mac_str, mac_msg->vid, mac_msg->origin_ifname);

                /*Remove MAC_AGE_LOCAL flag*/
                mac_msg->age_flag = set_mac_local_age_flag(csm, mac_msg, 0);

                /*Reverse interface from peer-link to the original portchannel*/
                memcpy(mac_msg->ifname, mac_msg->origin_ifname, MAX_L_PORT_NAME);

                /*Send dynamic or static mac add message to mclagsyncd*/
                add_mac_to_chip(mac_msg, mac_msg->fdb_type);
            }
            else
            {
                /*this may be peerlink is not configured and portchannel is down*/
                /*when this portchannel up, add the mac back to ASIC*/
                ICCPD_LOG_DEBUG(__FUNCTION__, "Intf %s up, add MAC %s vlan-id %d to ASIC",
                                mac_msg->ifname, mac_msg->mac_str, mac_msg->vid);

                /*Remove MAC_AGE_LOCAL flag*/
                mac_msg->age_flag = set_mac_local_age_flag(csm, mac_msg, 0);

                /*Send dynamic or static mac add message to mclagsyncd*/
                add_mac_to_chip(mac_msg, mac_msg->fdb_type);
            }
        }
    }

    return;
}

/*Deal with l2mc add,del,move when portchannel up or down*/
static void update_l2mc_state(struct CSM *csm,
                                struct LocalInterface *lif,
                                int po_state)
{
    struct L2MCMsg* l2mc_msg = NULL, *l2mc_temp = NULL;

    if (!csm || !lif)
        return;

    RB_FOREACH_SAFE (l2mc_msg, l2mc_rb_tree, &MLACP(csm).l2mc_rb, l2mc_temp)
    {
        /* find the L2MC for this interface*/
        if (strcmp(lif->name, l2mc_msg->origin_ifname) != 0)
            continue;

        /*portchannel down*/
        if (po_state == 0)
        {
            l2mc_msg->del_flag = set_l2mc_local_del_flag(csm, l2mc_msg, 1, 1);

            ICCPD_LOG_DEBUG(__FUNCTION__, "Intf down, del flag %d, saddr %s, gaddr %s "
                "vlan-id %d, Interface: %s", l2mc_msg->del_flag ,
                l2mc_msg->saddr, l2mc_msg->gaddr, l2mc_msg->vid, l2mc_msg->ifname);

            if (l2mc_msg->del_flag == (L2MC_DEL_LOCAL | L2MC_DEL_PEER))
            {
                /*send mac  message to mclagsyncd.*/
                del_l2mc_from_chip(l2mc_msg, MCLAG_MSG_TYPE_SET_L2MC);

                L2MC_RB_REMOVE(l2mc_rb_tree, &MLACP(csm).l2mc_rb, l2mc_msg);

                if (!L2MC_IN_MSG_LIST(&(MLACP(csm).l2mc_msg_list), l2mc_msg, tail))
                {
                    free(l2mc_msg);
                }
            }
            else
            {
                if (strlen(csm->peer_itf_name) != 0)
                {
                    if (csm->peer_link_if && csm->peer_link_if->state == PORT_STATE_UP)
                    {
                        del_l2mc_from_chip(l2mc_msg, MCLAG_MSG_TYPE_SET_L2MC);
                        memcpy(l2mc_msg->ifname, csm->peer_itf_name, MAX_L_PORT_NAME);
                        add_l2mc_to_chip(l2mc_msg, l2mc_msg->l2mc_type, MCLAG_MSG_TYPE_SET_L2MC);
                        ICCPD_LOG_DEBUG(__FUNCTION__, "Intf down, del flag %d, "
                           "redirect to peer-link: %s, saddr %s gaddr %s vlan-id %d",
                           l2mc_msg->del_flag, l2mc_msg->ifname,
                           l2mc_msg->saddr, l2mc_msg->gaddr, l2mc_msg->vid);
                    }
                    else
                    {
                        del_l2mc_from_chip(l2mc_msg, MCLAG_MSG_TYPE_SET_L2MC);
                        memcpy(l2mc_msg->ifname, csm->peer_itf_name, MAX_L_PORT_NAME);
                        ICCPD_LOG_DEBUG(__FUNCTION__, "Intf down, del flag %d, "
                           "can not redirect, del L2MC as peer-link: %s down, "
                           "saddr %s gaddr %s vlanid %d", l2mc_msg->del_flag, l2mc_msg->ifname,
                           l2mc_msg->saddr, l2mc_msg->gaddr, l2mc_msg->vid);
                    }
                }
                else
                {
                    del_l2mc_from_chip(l2mc_msg, MCLAG_MSG_TYPE_SET_L2MC);
                }
            }
        }
        else /*portchannel up*/
        {
            /*the old item is redirect to peerlink for portchannel down*/
            /*when this portchannel up, recover the mac back*/
            if (strcmp(l2mc_msg->ifname, csm->peer_itf_name) == 0)
            {
                ICCPD_LOG_DEBUG(__FUNCTION__, "Intf up, redirect L2MC to Interface: %s,"
                " saddr %s gaddr %s vlan-id %d", l2mc_msg->ifname,
                l2mc_msg->saddr, l2mc_msg->gaddr, l2mc_msg->vid);

                l2mc_msg->del_flag = set_l2mc_local_del_flag(csm, l2mc_msg, 0, 1);
                del_l2mc_from_chip(l2mc_msg, MCLAG_MSG_TYPE_SET_L2MC);

                /*Reverse interface from peer-link to the original portchannel*/
                memcpy(l2mc_msg->ifname, l2mc_msg->origin_ifname, MAX_L_PORT_NAME);

                add_l2mc_to_chip(l2mc_msg, l2mc_msg->l2mc_type, MCLAG_MSG_TYPE_SET_L2MC);
            }
            else
            {
                /*this may be peerlink is not configured and portchannel is down*/
                /*when this portchannel up, add the l2mc back to ASIC*/
                ICCPD_LOG_DEBUG(__FUNCTION__, "Intf up, redirect L2MC to Interface: %s,"
                " saddr %s gaddr %s vlan-id %d", l2mc_msg->ifname,
                l2mc_msg->saddr, l2mc_msg->gaddr, l2mc_msg->vid);

                l2mc_msg->del_flag = set_l2mc_local_del_flag(csm, l2mc_msg, 0, 1);

                add_l2mc_to_chip(l2mc_msg, l2mc_msg->l2mc_type, MCLAG_MSG_TYPE_SET_L2MC);
            }
        }
    }

    return;
}

/*Deal with l2mc mrouter add,del when portchannel up or down*/
static void update_l2mc_mrouter_state(struct CSM *csm,
                                struct LocalInterface *lif,
                                int po_state)
{
    struct L2MCMsg* l2mc_msg = NULL, *l2mc_temp = NULL;

    if (!csm || !lif)
        return;

    RB_FOREACH_SAFE (l2mc_msg, l2mc_mrouter_rb_tree, &MLACP(csm).l2mc_mrouter_rb, l2mc_temp)
    {
        /* find the L2MC for this interface*/
        if (strcmp(lif->name, l2mc_msg->origin_ifname) != 0)
            continue;

        /*portchannel down*/
        if (po_state == 0)
        {
            l2mc_msg->del_flag = set_l2mcmrtr_local_del_flag(csm, l2mc_msg, 1, 1);

            ICCPD_LOG_DEBUG(__FUNCTION__, "Intf down, del flag %d "
                "vlan-id %d, Interface: %s", l2mc_msg->del_flag ,
                l2mc_msg->vid, l2mc_msg->ifname);

            if (l2mc_msg->del_flag == (L2MC_DEL_LOCAL | L2MC_DEL_PEER))
            {
                /*send mac  message to mclagsyncd.*/
                del_l2mc_from_chip(l2mc_msg, MCLAG_MSG_TYPE_SET_L2MC_MROUTER);

                L2MC_RB_REMOVE(l2mc_mrouter_rb_tree, &MLACP(csm).l2mc_mrouter_rb, l2mc_msg);

                if (!L2MC_IN_MSG_LIST(&(MLACP(csm).l2mcmrtr_msg_list), l2mc_msg, tail))
                {
                    free(l2mc_msg);
                }
            }
            else
            {
                if (strlen(csm->peer_itf_name) != 0)
                {
                    if (csm->peer_link_if && csm->peer_link_if->state == PORT_STATE_UP)
                    {
                        del_l2mc_from_chip(l2mc_msg, MCLAG_MSG_TYPE_SET_L2MC_MROUTER);
                        memcpy(l2mc_msg->ifname, csm->peer_itf_name, MAX_L_PORT_NAME);
                        add_l2mc_to_chip(l2mc_msg, l2mc_msg->l2mc_type, MCLAG_MSG_TYPE_SET_L2MC_MROUTER);
                        ICCPD_LOG_DEBUG(__FUNCTION__, "Intf down, del flag %d, "
                           "redirect to peer-link: %s, vlan-id %d",
                           l2mc_msg->del_flag, l2mc_msg->ifname, l2mc_msg->vid);
                    }
                    else
                    {
                        del_l2mc_from_chip(l2mc_msg, MCLAG_MSG_TYPE_SET_L2MC_MROUTER);
                        memcpy(l2mc_msg->ifname, csm->peer_itf_name, MAX_L_PORT_NAME);
                        ICCPD_LOG_DEBUG(__FUNCTION__, "Intf down, del flag %d, "
                           "can not redirect, del L2MC as peer-link: %s down, "
                           "vlanid %d", l2mc_msg->del_flag, l2mc_msg->ifname, l2mc_msg->vid);
                    }
                }
                else
                {
                    del_l2mc_from_chip(l2mc_msg, MCLAG_MSG_TYPE_SET_L2MC_MROUTER);
                }
            }
        }
        else /*portchannel up*/
        {
            /*the old item is redirect to peerlink for portchannel down*/
            /*when this portchannel up, recover the mac back*/
            if (strcmp(l2mc_msg->ifname, csm->peer_itf_name) == 0)
            {
                ICCPD_LOG_DEBUG(__FUNCTION__, "Intf up, redirect L2MC Mrouter to Interface: %s,"
                "vlan-id %d", l2mc_msg->ifname, l2mc_msg->vid);

                l2mc_msg->del_flag = set_l2mcmrtr_local_del_flag(csm, l2mc_msg, 0, 1);
                del_l2mc_from_chip(l2mc_msg, MCLAG_MSG_TYPE_SET_L2MC_MROUTER);

                /*Reverse interface from peer-link to the original portchannel*/
                memcpy(l2mc_msg->ifname, l2mc_msg->origin_ifname, MAX_L_PORT_NAME);

                add_l2mc_to_chip(l2mc_msg, l2mc_msg->l2mc_type, MCLAG_MSG_TYPE_SET_L2MC_MROUTER);
            }
            else
            {
                /*this may be peerlink is not configured and portchannel is down*/
                /*when this portchannel up, add the l2mc back to ASIC*/
                ICCPD_LOG_DEBUG(__FUNCTION__, "Intf up, redirect L2MC Mrouter to Interface: %s,"
                "vlan-id %d", l2mc_msg->ifname, l2mc_msg->vid);

                l2mc_msg->del_flag = set_l2mcmrtr_local_del_flag(csm, l2mc_msg, 0, 1);

                add_l2mc_to_chip(l2mc_msg, l2mc_msg->l2mc_type, MCLAG_MSG_TYPE_SET_L2MC_MROUTER);
            }
        }
    }

    return;
}

void mlacp_portchannel_state_handler(struct CSM* csm,
                                     struct LocalInterface* local_if,
                                     int po_state)
{
    if (!csm || !local_if)
        return;

    update_peerlink_isolate_from_lif(csm, local_if, po_state);

    update_l2_mac_state(csm, local_if, po_state);
    update_l2mc_state(csm, local_if, po_state);

    if (!local_if_is_l3_mode(local_if))
        update_l2_po_state(csm, local_if, po_state);
    else
        update_l3_po_state(csm, local_if, po_state);

    update_po_if_info(csm, local_if, po_state);

    return;
}

static void mlacp_conn_handler_fdb(struct CSM* csm)
{
    struct Msg* msg = NULL;
    struct MACMsg* mac_msg = NULL;
    struct Msg *msg_send = NULL;

    if (!csm)
        return;

    if (!TAILQ_EMPTY(&(MLACP(csm).mac_list)))
    {
        TAILQ_FOREACH(msg, &MLACP(csm).mac_list, tail)
        {
            mac_msg = (struct MACMsg*)msg->buf;

            /*Wait the ACK from peer?*/
            /*mac_msg->age_flag &= ~MAC_AGE_PEER;*/

            /*If MAC with local age flag, dont sync to peer. Such MAC only exist when peer is warm-reboot.
              If peer is warm-reboot, peer age flag is not set when connection is lost. 
              When MAC is aged in local switch, this MAC is not deleted for no peer age flag.
              After warm-reboot, this MAC must be learnt by peer and sync to local switch*/
            if (!(mac_msg->age_flag & MAC_AGE_LOCAL))
            {
                /*Send mac add message to peer*/
                mac_msg->op_type = MAC_SYNC_ADD;
                if (iccp_csm_init_msg(&msg_send, (char*)mac_msg, sizeof(struct MACMsg)) == 0)
                {
                    mac_msg->age_flag &= ~MAC_AGE_PEER;
                    TAILQ_INSERT_TAIL(&(MLACP(csm).mac_msg_list), msg_send, tail);
                    ICCPD_LOG_DEBUG(__FUNCTION__, "MAC-msg-list enqueue: %s, add %s vlan-id %d",
                                    mac_msg->ifname, mac_msg->mac_str, mac_msg->vid);
                }
            }
            else
            {
                /*If MAC with local age flag and is point to MCLAG enabled port, reomove local age flag*/
                if (strcmp(mac_msg->ifname, csm->peer_itf_name) != 0)
                {
                    ICCPD_LOG_DEBUG(__FUNCTION__, "MAC-msg-list not enqueue for local age flag: %s, mac %s vlan-id %d, remove local age flag",
                                    mac_msg->ifname, mac_msg->mac_str, mac_msg->vid);
                    mac_msg->age_flag &= ~MAC_AGE_LOCAL;
                }
            }
        }
    }

    return;
}

static void mlacp_fix_bridge_mac(struct CSM* csm)
{
    char syscmd[128];
    int ret = 0;
    char macaddr[64];
    uint8_t null_mac[] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };

    if (memcmp(MLACP(csm).system_id, null_mac, ETHER_ADDR_LEN) != 0)
    {
        memset(macaddr, 0, 64);
        snprintf(macaddr, 64, "%02x:%02x:%02x:%02x:%02x:%02x",
             MLACP(csm).system_id[0], MLACP(csm).system_id[1], MLACP(csm).system_id[2],
             MLACP(csm).system_id[3], MLACP(csm).system_id[4], MLACP(csm).system_id[5]);

        /*When changing the mac of a vlan member port, the mac of Bridge will be changed.*/
        /*The Bridge mac can not be the same as peer system id, so fix the Bridge MAC address here.*/
        sprintf(syscmd, "ip link set dev Bridge address %s > /dev/null 2>&1", macaddr);
        ret = system(syscmd);
        ICCPD_LOG_DEBUG(__FUNCTION__, "  %s  ret = %d", syscmd, ret);
    }

    return;
}

/*****************************************
* Peer connect/disconnect handler
*
* ***************************************/
void mlacp_peer_conn_handler(struct CSM* csm)
{
    struct LocalInterface *lif = NULL;
    static int once_connected = 0;
    struct System* sys = NULL;

    if (!csm)
        return;

    if ((sys = system_get_instance()) == NULL)
        return;

    if (csm->warm_reboot_disconn_time != 0)
    {
        /*If peer reconnected, reset peer disconnect time*/
        csm->warm_reboot_disconn_time = 0;
        ICCPD_LOG_DEBUG(__FUNCTION__, "Peer warm reboot and reconnect, reset peer disconnect time!");
    }

    if (csm->peer_link_if)
    {
        set_peerlink_mlag_port_learn(csm->peer_link_if, 0);
    }

    /*If peer connect again, don't flush FDB*/
    if (once_connected == 0)
    {
        once_connected = 1;
        mlacp_fix_bridge_mac(csm);
        /*If warm reboot, don't flush FDB*/
        if (sys->warmboot_start != WARM_REBOOT)
            mlacp_clean_fdb();
    }

    iccp_get_fdb_change_from_syncd();
    sys->csm_trans_time = time(NULL);

    mlacp_conn_handler_fdb(csm);
    mlacp_sync_l2mc(csm);

#if 0
    // When peer-link ready, suppose all MLAG link are alive
    LIST_FOREACH(pif, &(MLACP(csm).pif_list), mlacp_next)
    {
        pif->po_active = 1;
    }
#endif
    LIST_FOREACH(lif, &(MLACP(csm).lif_list), mlacp_next)
    {
        if (lif->type == IF_T_PORT_CHANNEL)
        {
#if 0
            if (local_if_is_l3_mode(lif))
            {
                set_route_by_linux_route( csm,  lif,  1);
            }
            else
            {
                LIST_FOREACH(vlan, &(lif->vlan_list), port_next)
                {
                    if (!vlan->vlan_itf)
                        continue;
                    if (!local_if_is_l3_mode(vlan->vlan_itf))
                        continue;

                    set_route_by_linux_route(csm, vlan->vlan_itf, 1); /* add static route by linux route tool*/
                }
            }
#endif

            mlacp_portchannel_state_handler(csm, lif, (lif->state == PORT_STATE_UP) ? 1 : 0);
        }
    }

    return;
}

extern void recover_if_ipmac_on_standby(struct LocalInterface* lif_po);
void mlacp_peer_disconn_handler(struct CSM* csm)
{
    uint8_t null_mac[] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };
    struct LocalInterface* lif = NULL;
    struct Msg* msg = NULL;
    struct MACMsg* mac_msg = NULL;
    struct L2MCMsg* l2mc_msg = NULL, *l2mc_temp = NULL;
    struct System* sys = NULL;

    if (!csm)
        return;

    if ((sys = system_get_instance()) == NULL)
        return;

    /*If warm reboot, don't change FDB and MAC address*/
    if (sys->warmboot_exit == WARM_REBOOT)
        return;

    /*If peer is warm reboot, don't change FDB*/
    if (csm->peer_warm_reboot_time != 0)
    {
        /*If peer disconnected, recover peer to normal reboot for next time*/
        csm->peer_warm_reboot_time = 0;
        /*peer connection must be establised again within 90s
           from last disconnection for peer warm reboot*/
        time(&csm->warm_reboot_disconn_time);
        ICCPD_LOG_DEBUG(__FUNCTION__, "Peer warm reboot and disconnect, recover to normal reboot for next time!");
        return;
    }

    TAILQ_FOREACH(msg, &MLACP(csm).mac_list, tail)
    {
        mac_msg = (struct MACMsg*)msg->buf;

        mac_msg->age_flag |= MAC_AGE_PEER;
        ICCPD_LOG_DEBUG(__FUNCTION__, "Add peer age flag: %s, MAC %s vlan-id %d",
                        mac_msg->ifname, mac_msg->mac_str, mac_msg->vid);

        /* find the MAC that the port is peer-link or local and peer both aged, to be deleted*/
        if (strcmp(mac_msg->ifname, csm->peer_itf_name) != 0 && mac_msg->age_flag != (MAC_AGE_LOCAL | MAC_AGE_PEER))
            continue;

        ICCPD_LOG_DEBUG(__FUNCTION__, "Peer disconnect, del MAC for peer-link: %s, MAC %s vlan-id %d",
                        mac_msg->ifname, mac_msg->mac_str, mac_msg->vid);

        /*Send mac del message to mclagsyncd, may be already deleted*/
        del_mac_from_chip(mac_msg);

        TAILQ_REMOVE(&(MLACP(csm).mac_list), msg, tail);
        free(msg->buf);
        free(msg);
    }

    RB_FOREACH_SAFE (l2mc_msg, l2mc_rb_tree, &MLACP(csm).l2mc_rb, l2mc_temp)
    {
        l2mc_msg->del_flag |= L2MC_DEL_PEER;
        ICCPD_LOG_DEBUG(__FUNCTION__, "Add peer del flag %d interface %s, saddr  %s gaddr %s vlan-id %d,"
                " op_type %d", l2mc_msg->del_flag, l2mc_msg->ifname,
                l2mc_msg->saddr, l2mc_msg->gaddr, l2mc_msg->vid, l2mc_msg->op_type);

        /* find the entry that the port is peer-link or local and peer both deleted, to be deleted*/
        if (strcmp(l2mc_msg->ifname, csm->peer_itf_name) != 0 && l2mc_msg->del_flag != (L2MC_DEL_LOCAL | L2MC_DEL_PEER))
            continue;

        ICCPD_LOG_DEBUG(__FUNCTION__, "Peer disconnect, del L2MC entry for peer-link: %s, "
            "saddr %s gaddr %s vlan-id %d", l2mc_msg->ifname, l2mc_msg->saddr, l2mc_msg->gaddr, l2mc_msg->vid);

        /*Send del message to mclagsyncd, may be already deleted*/
        del_l2mc_from_chip(l2mc_msg, MCLAG_MSG_TYPE_SET_L2MC);

        L2MC_RB_REMOVE(l2mc_rb_tree, &MLACP(csm).l2mc_rb, l2mc_msg);
        // free only if not in change list to be send to peer node,
        // else free is taken care after sending the update to peer
        if (!L2MC_IN_MSG_LIST(&(MLACP(csm).l2mc_msg_list), l2mc_msg, tail))
        {
            free(l2mc_msg);
        }
    }

    /*mrouter info*/
    l2mc_msg=NULL;
    l2mc_temp=NULL;
    RB_FOREACH_SAFE (l2mc_msg, l2mc_mrouter_rb_tree, &MLACP(csm).l2mc_mrouter_rb, l2mc_temp)
    {
        l2mc_msg->del_flag |= L2MC_DEL_PEER;
        ICCPD_LOG_DEBUG(__FUNCTION__, "Add peer del flag %d interface %s, vlan-id %d,"
                " op_type %d", l2mc_msg->del_flag, l2mc_msg->ifname, l2mc_msg->vid, l2mc_msg->op_type);

        /* find the entry that the port is peer-link or local and peer both deleted, to be deleted*/
        if (strcmp(l2mc_msg->ifname, csm->peer_itf_name) != 0 && l2mc_msg->del_flag != (L2MC_DEL_LOCAL | L2MC_DEL_PEER))
            continue;

        ICCPD_LOG_DEBUG(__FUNCTION__, "Peer disconnect, del L2MC entry for peer-link: %s, "
            "vlan-id %d", l2mc_msg->ifname, l2mc_msg->vid);

        /*Send del message to mclagsyncd, may be already deleted*/
        del_l2mc_from_chip(l2mc_msg, MCLAG_MSG_TYPE_SET_L2MC_MROUTER);

        L2MC_RB_REMOVE(l2mc_rb_tree, &MLACP(csm).l2mc_rb, l2mc_msg);
        // free only if not in change list to be send to peer node,
        // else free is taken care after sending the update to peer
        if (!L2MC_IN_MSG_LIST(&(MLACP(csm).l2mcmrtr_msg_list), l2mc_msg, tail))
        {
            free(l2mc_msg);
        }
    }

    /* Clean all port block*/
    peerlink_port_isolate_cleanup(csm);

    memcpy(MLACP(csm).remote_system.system_id, null_mac, ETHER_ADDR_LEN);

    /*If peer is disconnected, recover the MAC address.*/
    if (csm->role_type == STP_ROLE_STANDBY)
    {
        LIST_FOREACH(lif, &(MLACP(csm).lif_list), mlacp_next)
        {
            recover_if_ipmac_on_standby(lif);
        }
    }

    return;
}

void mlacp_peerlink_up_handler(struct CSM* csm)
{
    struct Msg* msg = NULL;
    struct MACMsg* mac_msg = NULL;
    struct L2MCMsg* l2mc_msg = NULL;

    if (!csm)
        return;

    /*If peer link up, set all the mac that point to the peer-link in ASIC*/
    TAILQ_FOREACH(msg, &MLACP(csm).mac_list, tail)
    {
        mac_msg = (struct MACMsg*)msg->buf;

        /* Find the MAC that the port is peer-link to be added*/
        if (strcmp(mac_msg->ifname, csm->peer_itf_name) != 0)
            continue;

        ICCPD_LOG_DEBUG(__FUNCTION__, "Peer link up, add MAC to ASIC for peer-link: %s, MAC %s vlan-id %d",
                        mac_msg->ifname, mac_msg->mac_str, mac_msg->vid);

        /*Send mac add message to mclagsyncd, local age flag is already set*/
        add_mac_to_chip(mac_msg, MAC_TYPE_DYNAMIC);
    }

    RB_FOREACH (l2mc_msg, l2mc_rb_tree, &MLACP(csm).l2mc_rb)
    {
        if ((strcmp(l2mc_msg->ifname, csm->peer_itf_name) != 0) ||
            (!(l2mc_msg->del_flag & L2MC_DEL_LOCAL)))
              continue;

        ICCPD_LOG_DEBUG(__FUNCTION__, "Peer link up, add L2MC to STATE_DB for peer-link: %s, "
                "saddr %s gaddr %s vlan-id %d", l2mc_msg->ifname, l2mc_msg->saddr, l2mc_msg->gaddr, l2mc_msg->vid);

        add_l2mc_to_chip(l2mc_msg, l2mc_msg->l2mc_type, MCLAG_MSG_TYPE_SET_L2MC);
    }

    RB_FOREACH (l2mc_msg, l2mc_mrouter_rb_tree, &MLACP(csm).l2mc_mrouter_rb)
    {
        if ((strcmp(l2mc_msg->ifname, csm->peer_itf_name) != 0) ||
            (!(l2mc_msg->del_flag & L2MC_DEL_LOCAL)))
              continue;

        ICCPD_LOG_DEBUG(__FUNCTION__, "Peer link up, add L2MC mrouter to STATE_DB for peer-link: %s, "
                "vlan-id %d", l2mc_msg->ifname, l2mc_msg->vid);

        add_l2mc_to_chip(l2mc_msg, l2mc_msg->l2mc_type, MCLAG_MSG_TYPE_SET_L2MC_MROUTER);
    }

    return;
}

void mlacp_peerlink_down_handler(struct CSM* csm)
{
    struct Msg* msg = NULL;
    struct MACMsg* mac_msg = NULL;
    struct L2MCMsg* l2mc_msg = NULL, *l2mc_temp = NULL;

    if (!csm)
        return;

    /*If peer link down, remove all the mac that point to the peer-link*/
    TAILQ_FOREACH(msg, &MLACP(csm).mac_list, tail)
    {
        mac_msg = (struct MACMsg*)msg->buf;

        /* Find the MAC that the port is peer-link to be deleted*/
        if (strcmp(mac_msg->ifname, csm->peer_itf_name) != 0)
            continue;

        ICCPD_LOG_DEBUG(__FUNCTION__, "Peer link down, del MAC for peer-link: %s, MAC %s vlan-id %d",
                        mac_msg->ifname, mac_msg->mac_str, mac_msg->vid);

        mac_msg->age_flag = set_mac_local_age_flag(csm, mac_msg, 1);

        /*Send mac del message to mclagsyncd*/
        del_mac_from_chip(mac_msg);

        /*If peer is not age, keep the MAC in mac_list, but ASIC is deleted*/
        if (mac_msg->age_flag == (MAC_AGE_LOCAL | MAC_AGE_PEER))
        {
            /*If local and peer both aged, del the mac*/
            TAILQ_REMOVE(&(MLACP(csm).mac_list), msg, tail);
            free(msg->buf);
            free(msg);
        }
    }

    /*If peer link down, remove all the l2mc entries that point to the peer-link*/
    RB_FOREACH_SAFE (l2mc_msg, l2mc_rb_tree, &MLACP(csm).l2mc_rb, l2mc_temp)
    {
        /* Find the entry that the port is peer-link to be deleted*/
        if (strcmp(l2mc_msg->ifname, csm->peer_itf_name) != 0)
            continue;

       l2mc_msg->del_flag = set_l2mc_local_del_flag(csm, l2mc_msg, 1, 1);

        ICCPD_LOG_DEBUG(__FUNCTION__, "Peer link down, del L2MC for peer-link: %s,"
            " saddr %s gaddr %s vlan-id %d", l2mc_msg->ifname, l2mc_msg->saddr, l2mc_msg->gaddr, l2mc_msg->vid);

        /*Send del message to mclagsyncd*/
        del_l2mc_from_chip(l2mc_msg, MCLAG_MSG_TYPE_SET_L2MC);

        /*If peer is not del, keep the entry in l2mc_rb, but ASIC is deleted*/
        if (l2mc_msg->del_flag == (L2MC_DEL_LOCAL | L2MC_DEL_PEER))
        {
            L2MC_RB_REMOVE(l2mc_rb_tree, &MLACP(csm).l2mc_rb, l2mc_msg);

            if (!L2MC_IN_MSG_LIST(&(MLACP(csm).l2mc_msg_list), l2mc_msg, tail))
            {
                free(l2mc_msg);
            }
        }
    }

    /*L2mc mrouter If peer link down, remove all the mrouter entries that point to the peer-link*/
    l2mc_msg = NULL;
    l2mc_temp = NULL;
    RB_FOREACH_SAFE (l2mc_msg, l2mc_mrouter_rb_tree, &MLACP(csm).l2mc_mrouter_rb, l2mc_temp)
    {
        /* Find the entry that the port is peer-link to be deleted*/
        if (strcmp(l2mc_msg->ifname, csm->peer_itf_name) != 0)
            continue;

       l2mc_msg->del_flag = set_l2mcmrtr_local_del_flag(csm, l2mc_msg, 1, 1);

        ICCPD_LOG_DEBUG(__FUNCTION__, "Peer link down, del L2MC Mrouter for peer-link: %s,"
            "vlan-id %d", l2mc_msg->ifname, l2mc_msg->vid);

        /*Send del message to mclagsyncd*/
        del_l2mc_from_chip(l2mc_msg, MCLAG_MSG_TYPE_SET_L2MC_MROUTER);

        /*If peer is not del, keep the entry in l2mc_mrouter_rb, but ASIC is deleted*/
        if (l2mc_msg->del_flag == (L2MC_DEL_LOCAL | L2MC_DEL_PEER))
        {
            L2MC_RB_REMOVE(l2mc_mrouter_rb_tree, &MLACP(csm).l2mc_mrouter_rb, l2mc_msg);

            if (!L2MC_IN_MSG_LIST(&(MLACP(csm).l2mcmrtr_msg_list), l2mc_msg, tail))
            {
                free(l2mc_msg);
            }
        }
    }

    return;
}

/*****************************************
* Po add/remove handler
*
*****************************************/
void mlacp_mlag_link_add_handler(struct CSM *csm, struct LocalInterface *lif)
{
    if (!csm || !lif)
        return;
    if (MLACP(csm).current_state != MLACP_STATE_EXCHANGE)
        return;

    set_peerlink_mlag_port_isolate(csm, lif, 1);

    return;
}

void mlacp_mlag_link_del_handler(struct CSM *csm, struct LocalInterface *lif)
{
    if (!csm || !lif)
        return;

    if (MLACP(csm).current_state != MLACP_STATE_EXCHANGE)
        return;

    set_peerlink_mlag_port_isolate(csm, lif, 0);

    return;
}

int iccp_connect_syncd()
{
    struct System* sys = NULL;
    int ret = 0;
    int fd = 0;
    struct sockaddr_in serv;
    static int count = 0;
    struct epoll_event event;

    if ((sys = system_get_instance()) == NULL)
        goto conn_fail;

    if (sys->sync_fd >= 0)
        return 0;

    /*Print the fail log message every 60s*/
    if (count >= 600)
    {
        count = 0;
    }

    fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0)
    {
        if (count == 0)
            ICCPD_LOG_WARN(__FUNCTION__, "Failed to create unix socket: %s", strerror(errno));
        goto conn_fail;
    }

    /* Make server socket. */
    memset(&serv, 0, sizeof(serv));
    serv.sin_family = AF_INET;
    serv.sin_port = htons(2626);
#ifdef HAVE_STRUCT_SOCKADDR_IN_SIN_LEN
    serv.sin_len = sizeof(struct sockaddr_in);
#endif /* HAVE_STRUCT_SOCKADDR_IN_SIN_LEN */
    serv.sin_addr.s_addr = htonl(0x7f000006);

    ret = connect(fd, (struct sockaddr *)&serv, sizeof(serv));
    if (ret < 0)
    {
        if (count == 0)
            ICCPD_LOG_WARN(__FUNCTION__, "Failed to connect to mclag syncd: errno str %s", strerror(errno));
        close(fd);
        goto conn_fail;
    }

    ICCPD_LOG_NOTICE(__FUNCTION__, "Success to link syncd");
    sys->sync_fd = fd;

    event.data.fd = fd;
    event.events = EPOLLIN;
    ret = epoll_ctl(sys->epoll_fd, EPOLL_CTL_ADD, fd, &event);

    count = 0;
    return 0;

 conn_fail:
    if (count == 0)
        ICCPD_LOG_DEBUG(__FUNCTION__, "Mclag syncd socket connect fail");

    count++;

    return MCLAG_ERROR;
}

void syncd_info_close()
{
    struct System* sys = NULL;

    if ((sys = system_get_instance()) == NULL)
        return;

    if (sys->sync_fd > 0)
    {
        close(sys->sync_fd);
        sys->sync_fd = -1;
    }

    return;
}

int iccp_get_receive_fdb_sock_fd(struct System *sys)
{
    return sys->sync_fd;
}

/*When received MAC add and del packets from mclagsyncd, update mac information*/
void do_mac_update_from_syncd(char mac_str[ETHER_ADDR_STR_LEN], uint16_t vid, char *ifname, uint8_t fdb_type, uint8_t op_type)
{
    struct System *sys = NULL;
    struct CSM *csm = NULL;
    struct Msg *msg = NULL;
    struct MACMsg *mac_msg = NULL, *mac_info = NULL;
    uint8_t mac_exist = 0;
    char buf[MAX_BUFSIZE];
    size_t msg_len = 0;
    uint8_t from_mclag_intf = 0;/*0: orphan port, 1: MCLAG port*/
    struct CSM *first_csm = NULL;

    struct LocalInterface *lif_po = NULL, *mac_lif = NULL;

    if (!(sys = system_get_instance()))
        return;

    /* create MAC msg*/
    memset(buf, 0, MAX_BUFSIZE);
    msg_len = sizeof(struct MACMsg);
    mac_msg = (struct MACMsg*)buf;
    mac_msg->op_type = op_type;
    mac_msg->fdb_type = fdb_type;
    sprintf(mac_msg->mac_str, "%s", mac_str);
    mac_msg->vid = vid;

    mac_msg->age_flag = 0;

    ICCPD_LOG_DEBUG(__FUNCTION__, "Recv MAC msg from mclagsyncd, vid %d mac %s port %s optype %s ", vid, mac_str, ifname, op_type == MAC_SYNC_ADD ? "add" : "del");
    /*Debug*/
    #if 0
    /* dump receive MAC info*/
    fprintf(stderr, "\n======== MAC Update==========\n");
    fprintf(stderr, "  MAC    =  %s\n", mac_str);
    fprintf(stderr, "  vlan id = %d\n", vid);
    fprintf(stderr, "  fdb type = %s\n", fdb_type == MAC_TYPE_STATIC ? "static" : "dynamic");
    fprintf(stderr, "  op type = %s\n", op_type == MAC_SYNC_ADD ? "add" : "del");
    fprintf(stderr, "==============================\n");
    #endif

    /* Find MLACP itf, may be mclag enabled port-channel*/
    LIST_FOREACH(csm, &(sys->csm_list), next)
    {
        if (csm && !first_csm)
        {
            /*Record the first CSM, only one CSM in the system currently*/
            first_csm = csm;
        }

        /*If MAC is from peer-link, break; peer-link is not in MLACP(csm).lif_list*/
        if (strcmp(ifname, csm->peer_itf_name) == 0)
            break;

        LIST_FOREACH(lif_po, &(MLACP(csm).lif_list), mlacp_next)
        {
            if (lif_po->type != IF_T_PORT_CHANNEL)
                continue;

            if (strcmp(lif_po->name, ifname) == 0)
            {
                from_mclag_intf = 1;
                break;
            }
        }

        if (from_mclag_intf == 1)
            break;
    }

    if (!first_csm)
        return;

    /*If support multiple CSM, the MAC list of orphan port must be moved to sys->mac_list*/
    csm = first_csm;

    /* find lif MAC+vid*/
    TAILQ_FOREACH(msg, &MLACP(csm).mac_list, tail)
    {
        mac_info = (struct MACMsg*)msg->buf;

        /*MAC and vid are equal*/
        if (strcmp(mac_info->mac_str, mac_str) == 0 && mac_info->vid == vid)
        {
            mac_exist = 1;
            break;
        }
    }

    /*handle mac add*/
    if (op_type == MAC_SYNC_ADD)
    {
        /* Find local itf*/
        if (!(mac_lif = local_if_find_by_name(ifname)))
            return;

        sprintf(mac_msg->ifname, "%s", ifname);
        sprintf(mac_msg->origin_ifname, "%s", ifname);

        /*same MAC exist*/
        if (mac_exist)
        {
            /*If the recv mac port is peer-link, that is add from iccpd, no need to handle*/
            if (strcmp(csm->peer_itf_name, mac_msg->ifname) == 0)
            {
                return;
            }

            /*If the current mac port is peer-link, it will handle by port up event*/
            /*if(strcmp(csm->peer_itf_name, mac_info->ifname) == 0)
               {
                return;
               }*/

            /* update MAC*/
            if (mac_info->fdb_type != mac_msg->fdb_type
                || strcmp(mac_info->ifname, mac_msg->ifname) != 0
                || strcmp(mac_info->origin_ifname, mac_msg->ifname) != 0)
            {
                mac_info->fdb_type = mac_msg->fdb_type;
                sprintf(mac_info->ifname, "%s", mac_msg->ifname);
                sprintf(mac_info->origin_ifname, "%s", mac_msg->ifname);

                /*Remove MAC_AGE_LOCAL flag*/
                mac_info->age_flag = set_mac_local_age_flag(csm, mac_info, 0);

                ICCPD_LOG_DEBUG(__FUNCTION__, "Update MAC for %s, ifname %s", mac_msg->mac_str, mac_msg->ifname);
            }
            else
            {
                /*All info are the same, Remove MAC_AGE_LOCAL flag, then return*/
                /*In theory, this will be happened that mac age and then learn*/
                mac_info->age_flag = set_mac_local_age_flag(csm, mac_info, 0);

                return;
            }
        }
        else/*same MAC not exist*/
        {
            /*If the port the mac learn is change to down before the mac
               sync to iccp, this mac must be deleted */
            if (mac_lif->state == PORT_STATE_DOWN)
            {
                del_mac_from_chip(mac_msg);

                return;
            }

            /*set MAC_AGE_PEER flag before send this item to peer*/
            mac_msg->age_flag |= MAC_AGE_PEER;
            /*ICCPD_LOG_DEBUG(__FUNCTION__, "Add peer age flag: %s, add %s vlan-id %d, age_flag %d",
                            mac_msg->ifname, mac_msg->mac_str, mac_msg->vid, mac_msg->age_flag);*/
            mac_msg->op_type = MAC_SYNC_ADD;

            if (MLACP(csm).current_state == MLACP_STATE_EXCHANGE)
            {
                struct Msg *msg_send = NULL;
                if (iccp_csm_init_msg(&msg_send, (char*)mac_msg, msg_len) == 0)
                {
                    mac_msg->age_flag &= ~MAC_AGE_PEER;
                    TAILQ_INSERT_TAIL(&(MLACP(csm).mac_msg_list), msg_send, tail);

                    /*ICCPD_LOG_DEBUG(__FUNCTION__, "MAC-msg-list enqueue: %s, add %s vlan-id %d, age_flag %d",
                                    mac_msg->ifname, mac_msg->mac_str, mac_msg->vid, mac_msg->age_flag);*/
                }
                else
                {
                    ICCPD_LOG_WARN(__FUNCTION__, "Failed to enqueue MAC-msg-list: %s, MAC %s vlan-id %d",
                                    mac_msg->ifname, mac_msg->mac_str, mac_msg->vid);
                }
            }

            /*enqueue mac to mac-list*/
            if (iccp_csm_init_msg(&msg, (char*)mac_msg, msg_len) == 0)
            {
                TAILQ_INSERT_TAIL(&(MLACP(csm).mac_list), msg, tail);

                /*ICCPD_LOG_DEBUG(__FUNCTION__, "MAC-list enqueue: %s, add %s vlan-id %d",
                                mac_msg->ifname, mac_msg->mac_str, mac_msg->vid);*/
            }
            else
                ICCPD_LOG_DEBUG(__FUNCTION__, "Failed to enqueue MAC %s, MAC %s vlan-id %d",
                                mac_msg->ifname, mac_msg->mac_str, mac_msg->vid);
        }
    }
    else/*handle mac del*/
    {
        /*same MAC exist*/
        if (mac_exist)
        {
            /*orphan port mac or origin from_mclag_intf but state is down*/
            if (strcmp(mac_info->ifname, csm->peer_itf_name) == 0)
            {
                /*Set MAC_AGE_LOCAL flag*/
                mac_info->age_flag = set_mac_local_age_flag(csm, mac_info, 1);

                if (mac_info->age_flag == (MAC_AGE_LOCAL | MAC_AGE_PEER))
                {
                    ICCPD_LOG_DEBUG(__FUNCTION__, "Recv MAC del msg: %s(peer-link), del %s vlan-id %d",
                                    mac_info->ifname, mac_info->mac_str, mac_info->vid);

                    /*If peer link is down, del the mac*/
                    TAILQ_REMOVE(&(MLACP(csm).mac_list), msg, tail);
                    free(msg->buf);
                    free(msg);
                }
                else if (csm->peer_link_if && csm->peer_link_if->state != PORT_STATE_DOWN)
                {
                    /*peer-link learn mac is control by iccpd, ignore the chip del info*/
                    add_mac_to_chip(mac_info, MAC_TYPE_DYNAMIC);

                    ICCPD_LOG_DEBUG(__FUNCTION__, "Recv MAC del msg: %s(peer-link is up), add back %s vlan-id %d",
                                    mac_info->ifname, mac_info->mac_str, mac_info->vid);
                }

                return;
            }

            /*Add MAC_AGE_LOCAL flag*/
            mac_info->age_flag = set_mac_local_age_flag(csm, mac_info, 1);

            if (mac_info->age_flag == (MAC_AGE_LOCAL | MAC_AGE_PEER))
            {
                ICCPD_LOG_DEBUG(__FUNCTION__, "Recv MAC del msg: %s, del %s vlan-id %d",
                                mac_info->ifname, mac_info->mac_str, mac_info->vid);

                /*If local and peer both aged, del the mac (local orphan mac is here)*/
                TAILQ_REMOVE(&(MLACP(csm).mac_list), msg, tail);
                free(msg->buf);
                free(msg);
            }
            else
            {
                ICCPD_LOG_DEBUG(__FUNCTION__, "Recv MAC del msg: %s, del %s vlan-id %d, peer is not age, add back to chip",
                                mac_info->ifname, mac_info->mac_str, mac_info->vid);

                mac_info->fdb_type = MAC_TYPE_DYNAMIC;

                if (from_mclag_intf && lif_po && lif_po->state == PORT_STATE_DOWN)
                {
                    /*If local if is down, redirect the mac to peer-link*/
                    if (strlen(csm->peer_itf_name) != 0)
                    {
                        memcpy(&mac_info->ifname, csm->peer_itf_name, IFNAMSIZ);

                        if (csm->peer_link_if && csm->peer_link_if->state == PORT_STATE_UP)
                        {
                            add_mac_to_chip(mac_info, MAC_TYPE_DYNAMIC);
                            ICCPD_LOG_DEBUG(__FUNCTION__, "Recv MAC del msg: %s(down), del %s vlan-id %d, redirect to peer-link",
                                            mac_info->ifname, mac_info->mac_str, mac_info->vid);
                        }
                    }

                    return;
                }

                /*If local is aged but peer is not aged, Send mac add message to mclagsyncd*/
                /*it is from_mclag_intf and port state is up, local orphan mac can not be here*/
                /* Find local itf*/
                if (!(mac_lif = local_if_find_by_name(mac_info->ifname)))
                    return;
                if (mac_lif->state == PORT_STATE_UP)
                    add_mac_to_chip(mac_info, MAC_TYPE_DYNAMIC);
            }
        }
    }

    return;
}

/* Received L2MC add and del packets from mclagsyncd */
void do_update_from_l2mc(uint8_t saddr[16], uint16_t vid, uint8_t gaddr[16], char *ifname, uint8_t l2mc_type, uint8_t op_type, int leave)
{
    struct System *sys = NULL;
    struct CSM *csm = NULL;
    struct Msg *msg = NULL;
    struct L2MCMsg *l2mc_msg = NULL, *l2mc_info = NULL, *new_l2mc_msg = NULL;
    struct L2MCMsg l2mc_find;
    uint8_t l2mc_exist = 0;
    char buf[MAX_BUFSIZE];
    size_t msg_len = 0;
    uint8_t from_mclag_intf = 0;/*0: orphan port, 1: MCLAG port*/
    struct CSM *first_csm = NULL;

    struct LocalInterface *lif_po = NULL, *l2mc_lif = NULL;

    if (!(sys = system_get_instance()))
    {
        ICCPD_LOG_ERR(__FUNCTION__, "Invalid system instance");
        return;
    }

    /* create L2MC msg*/
    memset(buf, 0, MAX_BUFSIZE);
    msg_len = sizeof(struct L2MCMsg);
    l2mc_msg = (struct L2MCMsg*)buf;
    l2mc_msg->op_type = op_type;
    l2mc_msg->l2mc_type = l2mc_type;
    l2mc_msg->l2mc_msg_type = MSG_TYPE_L2MC_ENTRY;
    memcpy(l2mc_msg->saddr, saddr, INET_ADDRSTRLEN);
    memcpy(l2mc_msg->gaddr, gaddr, INET_ADDRSTRLEN);
    l2mc_msg->vid = vid;

    /*Debug*/
    #if 1
    /* dump receive L2MC info*/
    fprintf(stderr, "\n======== L2MC entry Update==========\n");
    fprintf(stderr, "  SADDR    =  %s \n", saddr);
    fprintf(stderr, "  GADDR    =  %s \n", gaddr);
    fprintf(stderr, "  vlan id = %d\n", vid);
    fprintf(stderr, "  ifname    =  %s \n", ifname);
    fprintf(stderr, "  l2mc type = %s\n", l2mc_type == L2MC_TYPE_STATIC ? "static" : "dynamic");
    fprintf(stderr, "  op type = %s\n", op_type == L2MC_SYNC_ADD ? "add" : "del");
    fprintf(stderr, "==============================\n");
    #endif

    /* Find MLACP itf, may be mclag enabled port-channel*/
    LIST_FOREACH(csm, &(sys->csm_list), next)
    {
        if (csm && !first_csm)
        {
            /*Record the first CSM, only one CSM in the system currently*/
            first_csm = csm;
        }

        /*If L2MC is from peer-link, break; peer-link is not in MLACP(csm).lif_list*/
        if (strcmp(ifname, csm->peer_itf_name) == 0)
            break;

        LIST_FOREACH(lif_po, &(MLACP(csm).lif_list), mlacp_next)
        {
            if (lif_po->type != IF_T_PORT_CHANNEL)
                continue;

            if (strcmp(lif_po->name, ifname) == 0)
            {
                from_mclag_intf = 1;
                break;
            }
        }

        if (from_mclag_intf == 1)
            break;
    }

    if (!first_csm)
    {
        ICCPD_LOG_NOTICE(__FUNCTION__, "CSM not ready...");
        return;
    }

    /*If support multiple CSM, the L2MC list of orphan port must be moved to sys->l2mc_rb*/
    csm = first_csm;

    l2mc_find.vid = vid;
    memcpy(l2mc_find.saddr,saddr, INET_ADDRSTRLEN);
    memcpy(l2mc_find.gaddr,gaddr, INET_ADDRSTRLEN);
    memcpy(l2mc_find.ifname, ifname, MAX_L_PORT_NAME);

    l2mc_info = RB_FIND(l2mc_rb_tree, &MLACP(csm).l2mc_rb ,&l2mc_find);
    if(l2mc_info)
    {
        l2mc_exist = 1;
        ICCPD_LOG_DEBUG(__FUNCTION__, " RB_FIND success for the L2MC entry : %s, %s, "
            " vid: %d , ifname %s l2mc_msg_type:%d ", saddr, gaddr,
            l2mc_info->vid, l2mc_info->ifname, l2mc_info->l2mc_msg_type);
    }

    /*handle l2mc add*/
    if (op_type == L2MC_SYNC_ADD)
    {
        /* Find local itf*/
        if (!(l2mc_lif = local_if_find_by_name(ifname)))
        {
            ICCPD_LOG_NOTICE(__FUNCTION__, "local if for %s not found", ifname);
            return;
        }

        sprintf(l2mc_msg->ifname, "%s", ifname);
        sprintf(l2mc_msg->origin_ifname, "%s", ifname);

        if (l2mc_exist)
        {
            if (strcmp(csm->peer_itf_name, l2mc_msg->ifname) == 0)
            {
                return;
            }

            if (l2mc_lif->state == PORT_STATE_DOWN)
            {
                ICCPD_LOG_DEBUG(__FUNCTION__, "Ignore L2MC add received, "
                    "entry exists interface %s down, saddr %s gaddr %s, vlan %d ",
                    l2mc_msg->ifname, l2mc_msg->saddr, l2mc_msg->gaddr, l2mc_msg->vid);
                return;
            }

            l2mc_info->del_flag = set_l2mc_local_del_flag(csm, l2mc_info, 0, 1);
            ICCPD_LOG_DEBUG(__FUNCTION__, "Duplicate update saddr %s, gaddr %s, vlan %d ifname %s",
                    l2mc_msg->saddr, l2mc_msg->gaddr, l2mc_msg->vid, l2mc_msg->ifname);
            return;
        }
        else
        {
            struct PeerInterface* pif=NULL;
            if (from_mclag_intf) {
                pif = peer_if_find_by_name(csm, lif_po->name);
            }

            /*If the port change to down before the entry
               sync to iccp, this entry must be deleted */
            if (l2mc_lif->state == PORT_STATE_DOWN)
            {
                del_l2mc_from_chip(l2mc_msg, MCLAG_MSG_TYPE_SET_L2MC);
                return;
            }
            if (!from_mclag_intf ||
              (pif && !peer_po_is_alive(csm, pif->ifindex))) {
                l2mc_msg->del_flag |= L2MC_DEL_PEER;
            }
            ICCPD_LOG_DEBUG(__FUNCTION__, "Add peer del flag,del %d interface %s, "
                "saddr %s gaddr %s vlan-id %d ", l2mc_msg->del_flag, l2mc_msg->ifname,
                l2mc_msg->saddr, l2mc_msg->gaddr, l2mc_msg->vid);
            l2mc_msg->op_type = L2MC_SYNC_ADD;

            struct L2MCMsg *new_l2mc_msg = NULL;
            /*enqueue to l2mc-list*/
            if (iccp_csm_init_l2mc_msg(&new_l2mc_msg, (char*)l2mc_msg, msg_len) == 0)
            {
                RB_INSERT(l2mc_rb_tree, &MLACP(csm).l2mc_rb, new_l2mc_msg);

                ICCPD_LOG_DEBUG(__FUNCTION__, "L2MC-list enqueue: %s, add %s %s vlan-id %d",
                    l2mc_msg->ifname, l2mc_msg->saddr, l2mc_msg->gaddr, l2mc_msg->vid);
                if (MLACP(csm).current_state == MLACP_STATE_EXCHANGE)
                {
                    TAILQ_INSERT_TAIL(&(MLACP(csm).l2mc_msg_list), new_l2mc_msg, tail);

                    ICCPD_LOG_DEBUG(__FUNCTION__, "L2MC-msg-list enqueue: %s, %s, "
                        "add %s vlan-id %d", l2mc_msg->ifname,
                        l2mc_msg->saddr, l2mc_msg->gaddr, l2mc_msg->vid);
                }
            }
            else
                ICCPD_LOG_DEBUG(__FUNCTION__, "Failed to enqueue: %s, add %s %s vlan-id %d",
                        l2mc_msg->ifname, l2mc_msg->saddr, l2mc_msg->gaddr, l2mc_msg->vid);
        }
    }
    else/*handle l2mc del*/
    {
        if (l2mc_exist)
        {
           /* entry delete due to igmp leave
              delete from both local and remote */
           if (leave)
           {
               /*send L2MC_SYNC_LEAVE message to peer*/
                if (MLACP(csm).current_state == MLACP_STATE_EXCHANGE)
                {
                    l2mc_info->op_type = L2MC_SYNC_LEAVE;
                    if (!L2MC_IN_MSG_LIST(&(MLACP(csm).l2mc_msg_list), l2mc_info, tail))
                    {
                        TAILQ_INSERT_TAIL(&(MLACP(csm).l2mc_msg_list), l2mc_info, tail);
                    }
                }
                RB_REMOVE(l2mc_rb_tree, &MLACP(csm).l2mc_rb, l2mc_info);
                if (!L2MC_IN_MSG_LIST(&(MLACP(csm).l2mc_msg_list), l2mc_info, tail))
                {
                    free(l2mc_info);
                }
            }
            else
            {
                /* entry delete is due to link down
                   send delete to peer and re-add entry
                   if remote has not deleted */

                if ((strcmp(l2mc_info->ifname, csm->peer_itf_name) == 0) ||
                    from_mclag_intf)
                {
                    ICCPD_LOG_NOTICE(__FUNCTION__, "Recv Del due to link down on peer link or mlag interface");
                    return;
                }

                if (l2mc_info->del_flag & L2MC_DEL_PEER)
                {
                    /*Add L2MC_DEL_LOCAL flag*/
                    l2mc_info->del_flag = set_l2mc_local_del_flag(csm, l2mc_info, 1, 1);

                    ICCPD_LOG_DEBUG(__FUNCTION__, "Recv L2MC del interface %s, "
                        "saddr %s gaddr %s vlan-id %d", l2mc_info->ifname,
                        l2mc_info->saddr, l2mc_info->gaddr, l2mc_info->vid);

                    L2MC_RB_REMOVE(l2mc_rb_tree, &MLACP(csm).l2mc_rb, l2mc_info);

                    // free only if not in change list to be send to peer node,
                    // else free is taken care after sending the update to peer
                    if (!L2MC_IN_MSG_LIST(&(MLACP(csm).l2mc_msg_list), l2mc_info, tail))
                    {
                        free(l2mc_info);
                    }
                }
                else
                {
                    ICCPD_LOG_DEBUG(__FUNCTION__, "Recv L2MC del interface %s, "
                        "saddr %s gaddr %s vlan-id %d, peer is not deleted, add back to chip",
                        l2mc_info->ifname, l2mc_info->saddr, l2mc_info->gaddr, l2mc_info->vid);

                    if (!(l2mc_lif = local_if_find_by_name(l2mc_info->ifname)))
                        return;
                    if (l2mc_lif->state == PORT_STATE_UP) {
                        add_l2mc_to_chip(l2mc_info, l2mc_info->l2mc_type, MCLAG_MSG_TYPE_SET_L2MC);
                    }
                }
            }
        }
    }
    return;
}

/* Received L2MC mrouter add and del from mclagsyncd */
void do_update_from_l2mc_mrouter(uint16_t vid, char *ifname, uint8_t l2mc_type, uint8_t op_type, int leave)
{
    struct System *sys = NULL;
    struct CSM *csm = NULL;
    struct Msg *msg = NULL;
    struct L2MCMsg *l2mc_msg = NULL, *l2mc_info = NULL, *new_l2mc_msg = NULL;
    struct L2MCMsg l2mc_find;
    uint8_t l2mc_exist = 0;
    char buf[MAX_BUFSIZE];
    size_t msg_len = 0;
    uint8_t from_mclag_intf = 0;/*0: orphan port, 1: MCLAG port*/
    struct CSM *first_csm = NULL;

    struct LocalInterface *lif_po = NULL, *l2mc_lif = NULL;

    if (!(sys = system_get_instance()))
    {
        ICCPD_LOG_ERR(__FUNCTION__, "Invalid system instance");
        return;
    }

    /* create L2MC msg*/
    memset(buf, 0, MAX_BUFSIZE);
    msg_len = sizeof(struct L2MCMsg);
    l2mc_msg = (struct L2MCMsg*)buf;
    l2mc_msg->op_type = op_type;
    l2mc_msg->l2mc_msg_type = MSG_TYPE_L2MC_MROUTER;
    l2mc_msg->l2mc_type = l2mc_type;
    l2mc_msg->vid = vid;

    /*Debug*/
    #if 1
    /* dump receive L2MC info*/
    fprintf(stderr, "\n======== L2MC Mrouter Update==========\n");
    fprintf(stderr, "  vlan id = %d\n", vid);
    fprintf(stderr, "  ifname    =  %s \n", ifname);
    fprintf(stderr, "  l2mc type = %s\n", l2mc_type == L2MC_TYPE_STATIC ? "static" : "dynamic");
    fprintf(stderr, "  op type = %s\n", op_type == L2MC_SYNC_ADD ? "add" : "del");
    fprintf(stderr, "==============================\n");
    #endif

    /* Find MLACP itf, may be mclag enabled port-channel*/
    LIST_FOREACH(csm, &(sys->csm_list), next)
    {
        if (csm && !first_csm)
        {
            /*Record the first CSM, only one CSM in the system currently*/
            first_csm = csm;
        }

        /*If L2MC is from peer-link, break; peer-link is not in MLACP(csm).lif_list*/
        if (strcmp(ifname, csm->peer_itf_name) == 0)
            break;

        LIST_FOREACH(lif_po, &(MLACP(csm).lif_list), mlacp_next)
        {
            if (lif_po->type != IF_T_PORT_CHANNEL)
                continue;

            if (strcmp(lif_po->name, ifname) == 0)
            {
                from_mclag_intf = 1;
                break;
            }
        }

        if (from_mclag_intf == 1)
            break;
    }

    if (!first_csm)
    {
        ICCPD_LOG_NOTICE(__FUNCTION__, "CSM not ready...");
        return;
    }

    /*If support multiple CSM, the L2MC list of orphan port must be moved to sys->l2mc_rb*/
    csm = first_csm;

    l2mc_find.vid = vid;
    memcpy(l2mc_find.ifname, ifname, MAX_L_PORT_NAME);

    l2mc_info = RB_FIND(l2mc_mrouter_rb_tree, &MLACP(csm).l2mc_mrouter_rb ,&l2mc_find);
    if(l2mc_info)
    {
        l2mc_exist = 1;
        ICCPD_LOG_DEBUG(__FUNCTION__, " RB_FIND success for the L2MC Mrouter entry"
            " vid: %d , ifname %s", l2mc_info->vid, l2mc_info->ifname );
    }

    /*handle l2mc add*/
    if (op_type == L2MC_SYNC_ADD)
    {
        /* Find local itf*/
        if (!(l2mc_lif = local_if_find_by_name(ifname)))
        {
            ICCPD_LOG_NOTICE(__FUNCTION__, "local if for %s not found", ifname);
            return;
        }

        sprintf(l2mc_msg->ifname, "%s", ifname);
        sprintf(l2mc_msg->origin_ifname, "%s", ifname);

        if (l2mc_exist)
        {
            if (strcmp(csm->peer_itf_name, l2mc_msg->ifname) == 0)
            {
                return;
            }

            if (l2mc_lif->state == PORT_STATE_DOWN)
            {
                ICCPD_LOG_DEBUG(__FUNCTION__, "Ignore L2MC Mrouter add received, "
                    "entry exists interface %s down, vlan %d ",
                    l2mc_msg->ifname, l2mc_msg->vid);
                return;
            }

            l2mc_info->del_flag = set_l2mcmrtr_local_del_flag(csm, l2mc_info, 0, 1);
            ICCPD_LOG_DEBUG(__FUNCTION__, "Duplicate update for Mrouter vlan %d ifname %s",
                    l2mc_msg->vid, l2mc_msg->ifname);
            return;
        }
        else
        {
            struct PeerInterface* pif=NULL;
            if (from_mclag_intf) {
                pif = peer_if_find_by_name(csm, lif_po->name);
            }

            /*If the port change to down before the entry
               sync to iccp, this entry must be deleted */
            if (l2mc_lif->state == PORT_STATE_DOWN)
            {
                del_l2mc_from_chip(l2mc_msg, MCLAG_MSG_TYPE_SET_L2MC_MROUTER);
                return;
            }
            if (!from_mclag_intf ||
              (pif && !peer_po_is_alive(csm, pif->ifindex))) {
                l2mc_msg->del_flag |= L2MC_DEL_PEER;
            }
            ICCPD_LOG_DEBUG(__FUNCTION__, "Add peer del flag,del %d interface %s, "
                "vlan-id %d ", l2mc_msg->del_flag, l2mc_msg->ifname, l2mc_msg->vid);
            l2mc_msg->op_type = L2MC_SYNC_ADD;

            struct L2MCMsg *new_l2mc_msg = NULL;
            /*enqueue to l2mc-list*/
            if (iccp_csm_init_l2mc_msg(&new_l2mc_msg, (char*)l2mc_msg, msg_len) == 0)
            {
                RB_INSERT(l2mc_mrouter_rb_tree, &MLACP(csm).l2mc_mrouter_rb, new_l2mc_msg);

                ICCPD_LOG_DEBUG(__FUNCTION__, "L2MC-list Mrouter enqueue: %s, vlan-id %d",
                    l2mc_msg->ifname, l2mc_msg->vid);
                if (MLACP(csm).current_state == MLACP_STATE_EXCHANGE)
                {
                    TAILQ_INSERT_TAIL(&(MLACP(csm).l2mcmrtr_msg_list), new_l2mc_msg, tail);

                    ICCPD_LOG_DEBUG(__FUNCTION__, "L2MC-msg-list Mrouter enqueue: "
                        "add %s vlan-id %d", l2mc_msg->ifname,l2mc_msg->vid);
                }
            }
            else
                ICCPD_LOG_DEBUG(__FUNCTION__, "Failed to enqueue: %s, add %s %s vlan-id %d",
                        l2mc_msg->ifname, l2mc_msg->vid);
        }
    }
    else/*handle l2mc del*/
    {
        if (l2mc_exist)
        {
           /* entry delete due to igmp leave
              delete from both local and remote */
           if (leave)
           {
               /*send L2MC_SYNC_LEAVE message to peer*/
                if (MLACP(csm).current_state == MLACP_STATE_EXCHANGE)
                {
                    l2mc_info->op_type = L2MC_SYNC_LEAVE;
                    if (!L2MC_IN_MSG_LIST(&(MLACP(csm).l2mcmrtr_msg_list), l2mc_info, tail))
                    {
                        TAILQ_INSERT_TAIL(&(MLACP(csm).l2mcmrtr_msg_list), l2mc_info, tail);
                    }
                }
                RB_REMOVE(l2mc_mrouter_rb_tree, &MLACP(csm).l2mc_mrouter_rb, l2mc_info);
                if (!L2MC_IN_MSG_LIST(&(MLACP(csm).l2mcmrtr_msg_list), l2mc_info, tail))
                {
                    free(l2mc_info);
                }
            }
            else
            {
                /* entry delete is due to link down
                   send delete to peer and re-add entry
                   if remote has not deleted */

                if ((strcmp(l2mc_info->ifname, csm->peer_itf_name) == 0) ||
                    from_mclag_intf)
                {
                    ICCPD_LOG_NOTICE(__FUNCTION__, "Recv Del due to link down on peer link or mlag interface");
                    return;
                }

                if (l2mc_info->del_flag & L2MC_DEL_PEER)
                {
                    /*Add L2MC_DEL_LOCAL flag*/
                    l2mc_info->del_flag = set_l2mcmrtr_local_del_flag(csm, l2mc_info, 1, 1);

                    ICCPD_LOG_DEBUG(__FUNCTION__, "Recv L2MC del interface %s, "
                        "saddr %s gaddr %s vlan-id %d", l2mc_info->ifname,
                        l2mc_info->saddr, l2mc_info->gaddr, l2mc_info->vid);

                    L2MC_RB_REMOVE(l2mc_mrouter_rb_tree, &MLACP(csm).l2mc_mrouter_rb, l2mc_info);

                    // free only if not in change list to be send to peer node,
                    // else free is taken care after sending the update to peer
                    if (!L2MC_IN_MSG_LIST(&(MLACP(csm).l2mcmrtr_msg_list), l2mc_info, tail))
                    {
                        free(l2mc_info);
                    }
                }
                else
                {
                    ICCPD_LOG_DEBUG(__FUNCTION__, "Recv L2MC del interface %s, "
                        "saddr %s gaddr %s vlan-id %d, peer is not deleted, add back to chip",
                        l2mc_info->ifname, l2mc_info->saddr, l2mc_info->gaddr, l2mc_info->vid);

                    if (!(l2mc_lif = local_if_find_by_name(l2mc_info->ifname)))
                        return;
                    if (l2mc_lif->state == PORT_STATE_UP) {
                        add_l2mc_to_chip(l2mc_info, l2mc_info->l2mc_type, MCLAG_MSG_TYPE_SET_L2MC_MROUTER);
                    }
                }
            }
        }
    }
    return;
}

int iccp_receive_fdb_handler_from_syncd(struct System *sys, char *msg_buf)
{
    int count = 0;
    int i = 0;
    struct IccpSyncdHDr * msg_hdr;
    struct mclag_fdb_info * mac_info;

    msg_hdr = (struct IccpSyncdHDr *)msg_buf;

    count = (msg_hdr->len- sizeof(struct IccpSyncdHDr))/sizeof(struct mclag_fdb_info);
    ICCPD_LOG_DEBUG(__FUNCTION__, "recv msg fdb count %d   ",count );

    for (i =0; i<count;i++)
    {
        mac_info = (struct mclag_fdb_info *)&msg_buf[sizeof(struct IccpSyncdHDr )+ i * sizeof(struct mclag_fdb_info)];

        do_mac_update_from_syncd(mac_info->mac, mac_info->vid, mac_info->port_name, mac_info->type, mac_info->op_type);
    }
    return 0;
}

int iccp_receive_l2mc_handler_from_syncd(struct System *sys, char *msg_buf)
{
    int count = 0;
    int i = 0;
    struct IccpSyncdHDr * msg_hdr;
    struct mclag_l2mc_info * l2mc_info;

    msg_hdr = (struct IccpSyncdHDr *)msg_buf;

    count = (msg_hdr->len- sizeof(struct IccpSyncdHDr))/sizeof(struct mclag_l2mc_info);
    ICCPD_LOG_DEBUG(__FUNCTION__, "recv msg l2mc len %d size1 %d size2 %d count %d   ",
                    msg_hdr->len, sizeof(struct IccpSyncdHDr), sizeof(struct mclag_l2mc_info), count );

    for (i =0; i<count;i++)
    {
        l2mc_info = (struct mclag_l2mc_info *)&msg_buf[sizeof(struct IccpSyncdHDr )+ i * sizeof(struct mclag_l2mc_info)];
        ICCPD_LOG_DEBUG(__FUNCTION__, "recv msg l2mc count %d vid %d saddr %s gaddr %s port %s  optype  %d leave %d",i, l2mc_info->vid, l2mc_info->saddr, l2mc_info->gaddr, l2mc_info->port_name, l2mc_info->op_type, l2mc_info->leave);

        do_update_from_l2mc(l2mc_info->saddr, l2mc_info->vid, l2mc_info->gaddr, l2mc_info->port_name, l2mc_info->type, l2mc_info->op_type, l2mc_info->leave);
    }
    return 0;
}

int iccp_receive_l2mc_mrouter_handler_from_syncd(struct System *sys, char *msg_buf)
{
    int count = 0;
    int i = 0;
    struct IccpSyncdHDr * msg_hdr;
    struct mclag_l2mc_info * l2mc_info;

    msg_hdr = (struct IccpSyncdHDr *)msg_buf;

    count = (msg_hdr->len- sizeof(struct IccpSyncdHDr))/sizeof(struct mclag_l2mc_info);
    ICCPD_LOG_DEBUG(__FUNCTION__, "recv msg l2mc mrouter len %d size1 %d size2 %d count %d   ",
                    msg_hdr->len, sizeof(struct IccpSyncdHDr), sizeof(struct mclag_l2mc_info), count );

    for (i =0; i<count;i++)
    {
        l2mc_info = (struct mclag_l2mc_info *)&msg_buf[sizeof(struct IccpSyncdHDr )+ i * sizeof(struct mclag_l2mc_info)];
        ICCPD_LOG_DEBUG(__FUNCTION__, "recv msg l2mc mrouter count %d vid %d port %s  optype  %d leave %d",i, l2mc_info->vid, l2mc_info->port_name, l2mc_info->op_type, l2mc_info->leave);

        do_update_from_l2mc_mrouter(l2mc_info->vid, l2mc_info->port_name, l2mc_info->type, l2mc_info->op_type, l2mc_info->leave);
    }
    return 0;
}

int iccp_mclagsyncd_msg_handler(struct System *sys)
{
    int num_bytes_rxed = 0;
    char *msg_buf = g_iccp_mlagsyncd_recv_buf;
    struct IccpSyncdHDr * msg_hdr;
    int pos = 0;

    if (sys == NULL)
        return MCLAG_ERROR;
    memset(msg_buf, 0, ICCP_MLAGSYNCD_RECV_MSG_BUFFER_SIZE);

    /* read (max_size - msg_size) so that we have space to
       accomodate anything remaining in the last message */
    num_bytes_rxed = read(sys->sync_fd, msg_buf, ICCP_MLAGSYNCD_RECV_MSG_BUFFER_SIZE - MCLAG_MAX_MSG_LEN);

    if (num_bytes_rxed <= 0)
    {
        ICCPD_LOG_ERR(__FUNCTION__, "fd %d read error ret = %d  errno = %d "
            ,sys->sync_fd, num_bytes_rxed, errno);  
        return MCLAG_ERROR;
    }	

    while (pos < num_bytes_rxed) //iterate through all msgs
    {
        if ((num_bytes_rxed - pos) < sizeof(struct IccpSyncdHDr))
        {
            int recv_len = 0, len = 0;
            int pending_len = sizeof(struct IccpSyncdHDr) - (num_bytes_rxed - pos);

            ICCPD_LOG_NOTICE(__FUNCTION__, "recv msg header less than expected, trying to retrieve %d bytes more ", pending_len);

            while (recv_len < pending_len)
            {
                int remaining_len = pending_len-recv_len;
                len = read(sys->sync_fd, msg_buf+num_bytes_rxed+recv_len, remaining_len);
                if (len <= 0)
                {
                    ICCPD_LOG_ERR(__FUNCTION__, "fd %d read error ret = %d  errno = %d "
                        ,sys->sync_fd, len, errno);
                    return MCLAG_ERROR;
                }
                ICCPD_LOG_NOTICE(__FUNCTION__, "received %d pending bytes",
                    len);
                recv_len += len;
            }
        }

        msg_hdr = (struct IccpSyncdHDr *)(&msg_buf[pos]);
        ICCPD_LOG_DEBUG(__FUNCTION__, "rcv msg version %d type %d len %d pos:%d num_bytes_rxed:%d ",
                msg_hdr->ver , msg_hdr->type, msg_hdr->len, pos, num_bytes_rxed);

        if (!msg_hdr->len)
        {
            ICCPD_LOG_ERR(__FUNCTION__, "msg length zero!!!!! ");  
            return MCLAG_ERROR; 
        }
        if (msg_hdr->ver != 1)
        {
            ICCPD_LOG_ERR(__FUNCTION__, "msg version %d wrong!!!!! ", msg_hdr->ver);  
            pos += msg_hdr->len;
            continue;
        }
        if ((pos + msg_hdr->len) > num_bytes_rxed)
        {
            int recv_len = 0, len = 0;
            int pending_len = pos + msg_hdr->len - num_bytes_rxed;

            ICCPD_LOG_NOTICE(__FUNCTION__, "recv msg less than expected, trying to retrieve %d bytes more ",
                pending_len);

            while (recv_len < pending_len)
            {
                int remaining_len = pending_len-recv_len;
                len = read(sys->sync_fd, msg_buf+num_bytes_rxed+recv_len, remaining_len);
                if (len <= 0)
                {
                    ICCPD_LOG_ERR(__FUNCTION__, "fd %d read error ret = %d  errno = %d "
                        ,sys->sync_fd, len, errno);  
                    return MCLAG_ERROR;
                }	
                ICCPD_LOG_NOTICE(__FUNCTION__, "received %d pending bytes",
                    len);
                recv_len += len;
            }
        }

        if (msg_hdr->type == MCLAG_SYNCD_MSG_TYPE_FDB_OPERATION)
        {
            iccp_receive_fdb_handler_from_syncd(sys, &msg_buf[pos]);
        }
        else if (msg_hdr->type == MCLAG_SYNCD_MSG_TYPE_L2MC_OPERATION)
        {
            iccp_receive_l2mc_handler_from_syncd(sys, &msg_buf[pos]);
        }
        else if (msg_hdr->type == MCLAG_SYNCD_MSG_TYPE_L2MC_MROUTER_OPERATION)
        {
            iccp_receive_l2mc_mrouter_handler_from_syncd(sys, &msg_buf[pos]);
        }
        else 
        {
            ICCPD_LOG_ERR(__FUNCTION__, "recv unknown msg type %d ", msg_hdr->type);          
            pos += msg_hdr->len;
            continue;
        }
        pos += msg_hdr->len;
    }
    return 0;
}

char * mclagd_ctl_cmd_str(int req_type)
{
    switch (req_type)
    {
        case INFO_TYPE_DUMP_STATE:
            return "dump config";

        case INFO_TYPE_DUMP_ARP:
            return "dump arp";

        case INFO_TYPE_DUMP_MAC:
            return "dump mac";
        
        case INFO_TYPE_DUMP_L2MC:
            return "dump l2mc";

        case INFO_TYPE_DUMP_L2MC_MROUTER:
            return "dump l2mc_mrouter";

        case INFO_TYPE_DUMP_LOCAL_PORTLIST:
            return "dump local portlist";

        case INFO_TYPE_DUMP_PEER_PORTLIST:
            return "dump peer portlist";

        case INFO_TYPE_CONFIG_LOGLEVEL:
            return "config loglevel";
        default:
            break;
    }

    return "error req type";
}

int mclagd_ctl_sock_create()
{
    struct sockaddr_un addr;
    struct System* sys = NULL;
    struct epoll_event event;
    int addr_len;
    int ret = 0;

    if ((sys = system_get_instance()) == NULL)
        return MCLAG_ERROR;

    if (sys->sync_ctrl_fd > 0)
        return sys->sync_ctrl_fd;

    sys->sync_ctrl_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (sys->sync_ctrl_fd < 0)
    {
        ICCPD_LOG_WARN(__FUNCTION__, "Failed to create mclagd ctl sock");
        return sys->sync_ctrl_fd;
    }

    unlink(sys->mclagdctl_file_path);

    memset((void*)&addr, 0, sizeof(struct sockaddr_un));
    addr.sun_family = AF_UNIX;
    snprintf(addr.sun_path, 107, "%s", sys->mclagdctl_file_path);
    addr_len = sizeof(addr.sun_family) + strlen(sys->mclagdctl_file_path);

    if ((ret = bind(sys->sync_ctrl_fd, (struct sockaddr*)&addr, addr_len)) < 0)
    {
        ICCPD_LOG_WARN(__FUNCTION__, "Failed to bind mclagd ctl socket %s:%s", sys->mclagdctl_file_path, strerror(errno));
        close(sys->sync_ctrl_fd);
        return MCLAG_ERROR;
    }

    if (listen(sys->sync_ctrl_fd, 5) < 0)
    {
        ICCPD_LOG_WARN(__FUNCTION__, "Failed to listen unix mclagd ctl socket%s:%s", sys->mclagdctl_file_path, strerror(errno));
        close(sys->sync_ctrl_fd);
        return MCLAG_ERROR;
    }

    event.data.fd = sys->sync_ctrl_fd;
    event.events = EPOLLIN;
    epoll_ctl(sys->epoll_fd, EPOLL_CTL_ADD, sys->sync_ctrl_fd, &event);
    FD_SET(sys->sync_ctrl_fd, &(sys->readfd));
    sys->readfd_count++;

    return sys->sync_ctrl_fd;
}

int mclagd_ctl_sock_accept(int fd)
{
    struct sockaddr_in client_addr;
    int client_fd = 0;
    unsigned int addr_len = 0;

    client_fd = accept(fd, (struct sockaddr*)&client_addr, &addr_len);
    if (client_fd < 0)
    {
        ICCPD_LOG_WARN(__FUNCTION__, "Failed to accept a client from mclagdctl");
        return MCLAG_ERROR;
    }

    return client_fd;
}

int mclagd_ctl_sock_read(int fd, char *r_buf, int total_len)
{
    int read_len = 0;
    int ret = 0;
    struct timeval tv = { 0 };
    fd_set read_fd;

    while (read_len < total_len)
    {
        FD_ZERO(&read_fd);
        FD_SET(fd, &read_fd);
        tv.tv_sec = 5;
        tv.tv_usec = 0;

        switch ((ret = select(fd + 1, &read_fd, NULL, NULL, &tv)))
        {
            case -1:
            /* error*/
            case 0:
                /* timeout*/
                return MCLAG_ERROR;

            default:
                break;
        }

        if (FD_ISSET(fd, &read_fd))
            ret = read(fd, r_buf + read_len, total_len - read_len);
        if (ret <= 0)
        {
            return MCLAG_ERROR;
        }
        read_len += ret;
    }

    return read_len;
}

int mclagd_ctl_sock_write(int fd, char *w_buf, int total_len)
{
    int write_len = 0;
    int ret = 0;

    while (write_len < total_len)
    {
        ret = write(fd, w_buf + write_len, total_len - write_len);
        if (ret <= 0)
        {
            return 0;
        }
        write_len += ret;
    }

    return write_len;
}

void mclagd_ctl_handle_dump_state(int client_fd, int mclag_id)
{
    char * Pbuf = NULL;
    char buf[512] = { 0 };
    int state_num = 0;
    int ret = 0;
    struct mclagd_reply_hdr *hd = NULL;
    int len_tmp = 0;

    ret = iccp_mclag_config_dump(&Pbuf, &state_num, mclag_id);
    if (ret != EXEC_TYPE_SUCCESS)
    {
        len_tmp = sizeof(struct mclagd_reply_hdr);
        memcpy(buf, &len_tmp, sizeof(int));
        hd = (struct mclagd_reply_hdr *)(buf + sizeof(int));
        hd->exec_result = ret;
        hd->info_type = INFO_TYPE_DUMP_STATE;
        hd->data_len = 0;
        mclagd_ctl_sock_write(client_fd, buf, MCLAGD_REPLY_INFO_HDR);

        if (Pbuf)
            free(Pbuf);

        return;
    }
    hd = (struct mclagd_reply_hdr *)(Pbuf + sizeof(int));
    hd->exec_result = EXEC_TYPE_SUCCESS;
    hd->info_type = INFO_TYPE_DUMP_STATE;
    hd->data_len = state_num * sizeof(struct mclagd_state);

    len_tmp = (hd->data_len + sizeof(struct mclagd_reply_hdr));
    memcpy(Pbuf, &len_tmp, sizeof(int));
    mclagd_ctl_sock_write(client_fd, Pbuf, MCLAGD_REPLY_INFO_HDR + hd->data_len);

    if (Pbuf)
        free(Pbuf);

    return;
}

void mclagd_ctl_handle_dump_arp(int client_fd, int mclag_id)
{
    char * Pbuf = NULL;
    char buf[512] = { 0 };
    int arp_num = 0;
    int ret = 0;
    struct mclagd_reply_hdr *hd = NULL;
    int len_tmp = 0;

    ret = iccp_arp_dump(&Pbuf, &arp_num, mclag_id);
    if (ret != EXEC_TYPE_SUCCESS)
    {
        len_tmp = sizeof(struct mclagd_reply_hdr);
        memcpy(buf, &len_tmp, sizeof(int));
        hd = (struct mclagd_reply_hdr *)(buf + sizeof(int));
        hd->exec_result = ret;
        hd->info_type = INFO_TYPE_DUMP_ARP;
        hd->data_len = 0;
        mclagd_ctl_sock_write(client_fd, buf, MCLAGD_REPLY_INFO_HDR);

        if (Pbuf)
            free(Pbuf);

        return;
    }

    hd = (struct mclagd_reply_hdr *)(Pbuf + sizeof(int));
    hd->exec_result = EXEC_TYPE_SUCCESS;
    hd->info_type = INFO_TYPE_DUMP_ARP;
    hd->data_len = arp_num * sizeof(struct mclagd_arp_msg);
    len_tmp = (hd->data_len + sizeof(struct mclagd_reply_hdr));
    memcpy(Pbuf, &len_tmp, sizeof(int));
    mclagd_ctl_sock_write(client_fd, Pbuf, MCLAGD_REPLY_INFO_HDR + hd->data_len);

    if (Pbuf)
        free(Pbuf);

    return;
}

void mclagd_ctl_handle_dump_mac(int client_fd, int mclag_id)
{
    char * Pbuf = NULL;
    char buf[512] = { 0 };
    int mac_num = 0;
    int ret = 0;
    struct mclagd_reply_hdr *hd = NULL;
    int len_tmp = 0;

    ret = iccp_mac_dump(&Pbuf, &mac_num, mclag_id);
    if (ret != EXEC_TYPE_SUCCESS)
    {
        len_tmp = sizeof(struct mclagd_reply_hdr);
        memcpy(buf, &len_tmp, sizeof(int));
        hd = (struct mclagd_reply_hdr *)(buf + sizeof(int));
        hd->exec_result = ret;
        hd->info_type = INFO_TYPE_DUMP_MAC;
        hd->data_len = 0;
        mclagd_ctl_sock_write(client_fd, buf, MCLAGD_REPLY_INFO_HDR);

        if (Pbuf)
            free(Pbuf);

        return;
    }

    hd = (struct mclagd_reply_hdr *)(Pbuf + sizeof(int));
    hd->exec_result = EXEC_TYPE_SUCCESS;
    hd->info_type = INFO_TYPE_DUMP_MAC;
    hd->data_len = mac_num * sizeof(struct mclagd_mac_msg);

    len_tmp = (hd->data_len + sizeof(struct mclagd_reply_hdr));
    memcpy(Pbuf, &len_tmp, sizeof(int));

    mclagd_ctl_sock_write(client_fd, Pbuf, MCLAGD_REPLY_INFO_HDR + hd->data_len);

    if (Pbuf)
        free(Pbuf);

    return;
}

void mclagd_ctl_handle_dump_l2mc(int client_fd, int mclag_id)
{
    char * Pbuf = NULL;
    char buf[512] = { 0 };
    int l2mc_num = 0;
    int ret = 0;
    struct mclagd_reply_hdr *hd = NULL;
    int len_tmp = 0;

    ret = iccp_l2mc_dump(&Pbuf, &l2mc_num, mclag_id);
    if (ret != EXEC_TYPE_SUCCESS)
    {
        len_tmp = sizeof(struct mclagd_reply_hdr);
        memcpy(buf, &len_tmp, sizeof(int));
        hd = (struct mclagd_reply_hdr *)(buf + sizeof(int));
        hd->exec_result = ret;
        hd->info_type = INFO_TYPE_DUMP_L2MC;
        hd->data_len = 0;
        mclagd_ctl_sock_write(client_fd, buf, MCLAGD_REPLY_INFO_HDR);

        if (Pbuf)
            free(Pbuf);

        return;
    }

    hd = (struct mclagd_reply_hdr *)(Pbuf + sizeof(int));
    hd->exec_result = EXEC_TYPE_SUCCESS;
    hd->info_type = INFO_TYPE_DUMP_L2MC;
    hd->data_len = l2mc_num * sizeof(struct mclagd_l2mc_msg);

    len_tmp = (hd->data_len + sizeof(struct mclagd_reply_hdr));
    memcpy(Pbuf, &len_tmp, sizeof(int));

    mclagd_ctl_sock_write(client_fd, Pbuf, MCLAGD_REPLY_INFO_HDR + hd->data_len);

    if (Pbuf)
        free(Pbuf);

    return;
}

void mclagd_ctl_handle_dump_l2mc_mrouter(int client_fd, int mclag_id)
{
    char * Pbuf = NULL;
    char buf[512] = { 0 };
    int l2mc_num = 0;
    int ret = 0;
    struct mclagd_reply_hdr *hd = NULL;
    int len_tmp = 0;

    ret = iccp_l2mc_mrouter_dump(&Pbuf, &l2mc_num, mclag_id);
    if (ret != EXEC_TYPE_SUCCESS)
    {
        len_tmp = sizeof(struct mclagd_reply_hdr);
        memcpy(buf, &len_tmp, sizeof(int));
        hd = (struct mclagd_reply_hdr *)(buf + sizeof(int));
        hd->exec_result = ret;
        hd->info_type = INFO_TYPE_DUMP_L2MC_MROUTER;
        hd->data_len = 0;
        mclagd_ctl_sock_write(client_fd, buf, MCLAGD_REPLY_INFO_HDR);

        if (Pbuf)
            free(Pbuf);

        return;
    }

    hd = (struct mclagd_reply_hdr *)(Pbuf + sizeof(int));
    hd->exec_result = EXEC_TYPE_SUCCESS;
    hd->info_type = INFO_TYPE_DUMP_L2MC_MROUTER;
    hd->data_len = l2mc_num * sizeof(struct mclagd_l2mc_msg);

    len_tmp = (hd->data_len + sizeof(struct mclagd_reply_hdr));
    memcpy(Pbuf, &len_tmp, sizeof(int));

    mclagd_ctl_sock_write(client_fd, Pbuf, MCLAGD_REPLY_INFO_HDR + hd->data_len);

    if (Pbuf)
        free(Pbuf);

    return;
}

void mclagd_ctl_handle_dump_local_portlist(int client_fd, int mclag_id)
{
    char * Pbuf = NULL;
    char buf[512] = { 0 };
    int lif_num = 0;;
    int ret = 0;
    struct mclagd_reply_hdr *hd = NULL;
    int len_tmp = 0;

    ret = iccp_local_if_dump(&Pbuf, &lif_num, mclag_id);
    if (ret != EXEC_TYPE_SUCCESS)
    {
        len_tmp = sizeof(struct mclagd_reply_hdr);
        memcpy(buf, &len_tmp, sizeof(int));
        hd = (struct mclagd_reply_hdr *)(buf + sizeof(int));
        hd->exec_result = ret;
        hd->info_type = INFO_TYPE_DUMP_LOCAL_PORTLIST;
        hd->data_len = 0;
        mclagd_ctl_sock_write(client_fd, buf, MCLAGD_REPLY_INFO_HDR);

        if (Pbuf)
            free(Pbuf);

        return;
    }

    hd = (struct mclagd_reply_hdr *)(Pbuf + sizeof(int));
    hd->exec_result = EXEC_TYPE_SUCCESS;
    hd->info_type = INFO_TYPE_DUMP_LOCAL_PORTLIST;
    hd->data_len = lif_num * sizeof(struct mclagd_local_if);
    len_tmp = (hd->data_len + sizeof(struct mclagd_reply_hdr));
    memcpy(Pbuf, &len_tmp, sizeof(int));
    mclagd_ctl_sock_write(client_fd, Pbuf, MCLAGD_REPLY_INFO_HDR + hd->data_len);

    if (Pbuf)
        free(Pbuf);

    return;
}

void mclagd_ctl_handle_dump_peer_portlist(int client_fd, int mclag_id)
{
    char * Pbuf = NULL;
    char buf[512] = { 0 };
    int pif_num = 0;
    int ret = 0;
    struct mclagd_reply_hdr *hd = NULL;
    int len_tmp = 0;

    ret = iccp_peer_if_dump(&Pbuf, &pif_num, mclag_id);
    if (ret != EXEC_TYPE_SUCCESS)
    {
        len_tmp = sizeof(struct mclagd_reply_hdr);
        memcpy(buf, &len_tmp, sizeof(int));
        hd = (struct mclagd_reply_hdr *)(buf + sizeof(int));
        hd->exec_result = ret;
        hd->info_type = INFO_TYPE_DUMP_PEER_PORTLIST;
        hd->data_len = 0;
        mclagd_ctl_sock_write(client_fd, buf, MCLAGD_REPLY_INFO_HDR);

        if (Pbuf)
            free(Pbuf);

        return;
    }

    hd = (struct mclagd_reply_hdr *)(Pbuf + sizeof(int));
    hd->exec_result = EXEC_TYPE_SUCCESS;
    hd->info_type = INFO_TYPE_DUMP_PEER_PORTLIST;
    hd->data_len = pif_num * sizeof(struct mclagd_peer_if);
    len_tmp = (hd->data_len + sizeof(struct mclagd_reply_hdr));
    memcpy(Pbuf, &len_tmp, sizeof(int));
    mclagd_ctl_sock_write(client_fd, Pbuf, MCLAGD_REPLY_INFO_HDR + hd->data_len);

    if (Pbuf)
        free(Pbuf);

    return;
}

void mclagd_ctl_handle_config_loglevel(int client_fd, int log_level)
{
    char buf[sizeof(struct mclagd_reply_hdr)+sizeof(int)];
    struct mclagd_reply_hdr *hd = NULL;
    int len_tmp = 0;

    logger_set_configuration(log_level);

    len_tmp = sizeof(struct mclagd_reply_hdr);
    memcpy(buf, &len_tmp, sizeof(int));
    hd = (struct mclagd_reply_hdr *)(buf + sizeof(int));
    hd->exec_result = EXEC_TYPE_SUCCESS;
    hd->info_type = INFO_TYPE_CONFIG_LOGLEVEL;
    hd->data_len = 0;
    mclagd_ctl_sock_write(client_fd, buf, MCLAGD_REPLY_INFO_HDR);

    return;
}

int mclagd_ctl_interactive_process(int client_fd)
{
    char buf[512] = { 0 };
    int ret = 0;

    struct mclagdctl_req_hdr* req = NULL;

    if (client_fd < 0)
        return MCLAG_ERROR;

    ret = mclagd_ctl_sock_read(client_fd, buf, sizeof(struct mclagdctl_req_hdr));

    if (ret < 0)
        return MCLAG_ERROR;

    req = (struct mclagdctl_req_hdr*)buf;

    ICCPD_LOG_DEBUG(__FUNCTION__, "Receive request %s from mclagdctl", mclagd_ctl_cmd_str(req->info_type));

    switch (req->info_type)
    {
        case INFO_TYPE_DUMP_STATE:
            mclagd_ctl_handle_dump_state(client_fd, req->mclag_id);
            break;

        case INFO_TYPE_DUMP_ARP:
            mclagd_ctl_handle_dump_arp(client_fd, req->mclag_id);
            break;

        case INFO_TYPE_DUMP_MAC:
            mclagd_ctl_handle_dump_mac(client_fd, req->mclag_id);
            break;

        case INFO_TYPE_DUMP_L2MC:
            mclagd_ctl_handle_dump_l2mc(client_fd, req->mclag_id);
            break;

        case INFO_TYPE_DUMP_L2MC_MROUTER:
            mclagd_ctl_handle_dump_l2mc_mrouter(client_fd, req->mclag_id);
            break;

        case INFO_TYPE_DUMP_LOCAL_PORTLIST:
            mclagd_ctl_handle_dump_local_portlist(client_fd, req->mclag_id);
            break;

        case INFO_TYPE_DUMP_PEER_PORTLIST:
            mclagd_ctl_handle_dump_peer_portlist(client_fd, req->mclag_id);
            break;

        case INFO_TYPE_CONFIG_LOGLEVEL:
            mclagd_ctl_handle_config_loglevel(client_fd, req->mclag_id);
            break;
			
        default:
            return MCLAG_ERROR;
    }

    return 0;
}


