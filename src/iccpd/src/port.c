/*
 * port.c
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

#include <linux/ethtool.h>
#include <linux/sockios.h>

#include "../include/logger.h"
#include "../include/port.h"
#include "../include/system.h"
#include "../include/iccp_csm.h"
#include "../include/iccp_netlink.h"
#include "../include/scheduler.h"
#include "../include/mlacp_link_handler.h"

static int vlan_node_compare(const struct VLAN_ID *p_vlan_node1, const struct VLAN_ID *p_vlan_node2)
{
    if (p_vlan_node1->vid < p_vlan_node2->vid)
        return -1;

    if (p_vlan_node1->vid > p_vlan_node2->vid)
        return 1;

    return 0;
}
RB_GENERATE(vlan_rb_tree, VLAN_ID, vlan_entry, vlan_node_compare);

static int lif_node_compare(const struct LocalInterface *p_lif_node1, const struct LocalInterface *p_lif_node2)
{
    if (p_lif_node1->ifindex < p_lif_node2->ifindex)
        return -1;

    if (p_lif_node1->ifindex > p_lif_node2->ifindex)
        return 1;

    return 0;
}
RB_GENERATE(lif_rb_tree, LocalInterface, lif_entry, lif_node_compare);

void local_if_init(struct LocalInterface* local_if)
{
    if (local_if == NULL)
        return;

    memset(local_if, 0, sizeof(struct LocalInterface));
    local_if->po_id = -1;
    local_if->po_active = 1; //always guess the po is active
    local_if->mlacp_state = MLACP_STATE_INIT;
    local_if->type = IF_T_UNKNOW;
    local_if->changed = 1;
    local_if->port_config_sync = 0;
    local_if->is_peer_link = 0;
    local_if->is_arp_accept = 0;
    local_if->l3_mode = 0;
    local_if->state = PORT_STATE_DOWN;
    local_if->prefixlen = 32;
    local_if->csm = NULL;
    local_if->isolate_to_peer_link = 0;
    local_if->portchannel_member_count = 0;
    LIST_INIT(&local_if->member_list);
    RB_INIT(vlan_rb_tree, &local_if->vlan_tree);

    return;
}

void vlan_info_init(struct VLAN_ID* vlan)
{
    vlan->vid = -1;
    vlan->vlan_removed = 0;
    vlan->vlan_itf = NULL;

    return;
}

struct LocalInterface* local_if_create(int ifindex, char* ifname, int type)
{
    struct System* sys = NULL;
    struct LocalInterface* local_if = NULL;
    struct CSM* csm;
    struct If_info * cif = NULL;

    if (!ifname)
        return NULL;

    if (!(sys = system_get_instance()))
        return NULL;

    if (ifindex < 0)
        return NULL;

    if ((local_if = local_if_find_by_ifindex(ifindex)))
        return local_if;

    if (!(local_if = (struct LocalInterface*)malloc(sizeof(struct LocalInterface))))
    {
        ICCPD_LOG_WARN(__FUNCTION__, "Port ifindex = %d, malloc failed", ifindex);
        return NULL;
    }

    local_if_init(local_if);
    local_if->ifindex = ifindex;
    local_if->type = type;

    if (local_if->type == IF_T_PORT_CHANNEL)
    {
        int i;
        int len;
        len = strlen(ifname);

        for (i = 0; i < len; ++i)
            if (ifname[i] >= '0' && ifname[i] <= '9')
                break;

        if (i >= len)
            return NULL;

        local_if->po_id =  atoi(&ifname[i]);
    }

    if (ifname)
        snprintf(local_if->name, MAX_L_PORT_NAME, "%s", ifname);

    switch (type)
    {
        case IF_T_PORT_CHANNEL:
            break;

        case IF_T_PORT:
            break;

        case IF_T_VLAN:
            /* do nothing currently. */
            break;

        case IF_T_VXLAN:
            /* do nothing currently. */
            break;

        default:
            ICCPD_LOG_WARN(__FUNCTION__, "The type of local interface (%s) is not acceptable", ifname);
            if (local_if)
                free(local_if);
            return NULL;
    }

    ICCPD_LOG_NOTICE(__FUNCTION__,
                   "Create a local_if = %s ifindex = %d MAC = %02x:%02x:%02x:%02x:%02x:%02x, state = %s",
                   ifname, local_if->ifindex, local_if->mac_addr[0], local_if->mac_addr[1], local_if->mac_addr[2],
                   local_if->mac_addr[3], local_if->mac_addr[4], local_if->mac_addr[5], local_if->state ? "down" : "up");

    RB_INSERT(lif_rb_tree, &(sys->lif_tree), local_if);

    /*Check the intf is peer-link? Only support PortChannel and Ethernet currently*/
    /*When set peer-link, the local-if is probably not created*/
    LIST_FOREACH(csm, &(sys->csm_list), next)
    {
        if (strcmp(local_if->name, csm->peer_itf_name) == 0)
        {
            local_if->is_peer_link = 1;
            csm->peer_link_if = local_if;
            break;
        }
        /*check the intf is bind with csm*/
        LIST_FOREACH(cif, &(csm->if_bind_list), csm_next)
        {
            if (strcmp(ifname, cif->name) == 0)
            {
                mlacp_bind_port_channel_to_csm(csm, ifname);
            }
        }
    }

    return local_if;
}

#define IFINDEX_STR_LEN 32
struct LocalInterface* local_if_find_by_name(const char* ifname)
{
    struct LocalInterface* local_if = NULL;
    FILE *fp = NULL;
    char ifindex[IFINDEX_STR_LEN] = {0};
    char file_name[128] = "/sys/class/net/";
    char end_prefix[10] = "/ifindex";

    if (!ifname)
        return NULL;

    strcat(file_name, ifname);
    strcat(file_name, end_prefix);

    fp = fopen(file_name, "r");
    if (fp == NULL)
    {
        ICCPD_LOG_WARN(__FUNCTION__, "Can not get ifindex of local interface (%s)", ifname);
        return NULL;
    }

    fread(ifindex, IFINDEX_STR_LEN, 1, fp);
    (void)fclose(fp);

    local_if = local_if_find_by_ifindex(atoi(ifindex));

    return local_if;
}

struct LocalInterface* local_if_find_by_ifindex(int ifindex)
{
    struct System* sys = NULL;
    struct LocalInterface* local_if = NULL;
    struct LocalInterface lif_key = { 0 };

    memset(&lif_key, 0, sizeof(struct LocalInterface));
    lif_key.ifindex = ifindex;

    if ((sys = system_get_instance()) == NULL)
        return NULL;

    local_if = RB_FIND(lif_rb_tree, &(sys->lif_tree), &lif_key);

    return local_if;
}

/*struct LocalInterface* local_if_find_by_po_id(int po_id)
{
    struct System* sys = NULL;
    struct LocalInterface* local_if = NULL;

    if ((sys = system_get_instance()) == NULL)
        return NULL;

    LIST_FOREACH(local_if, &(sys->lif_list), system_next)
    {
        if (local_if->type == IF_T_PORT_CHANNEL && local_if->po_id == po_id)
            return local_if;
    }

    return NULL;
}*/

static void local_if_vlan_remove(struct LocalInterface *lif_vlan)
{
    struct System *sys = NULL;
    struct LocalInterface *lif = NULL;
    struct VLAN_ID *vlan = NULL;
    int vid = 0;
    struct VLAN_ID vlan_key = { 0 };
    char ifname[MAX_L_PORT_NAME];
    int i;
    int len;

    if (lif_vlan->type != IF_T_VLAN)
        return;

    /* Get vlan id from vlan name*/
    sprintf(ifname, "%s", lif_vlan->name);
    len = strlen(ifname);

    for (i = 0; i < len; ++i)
        if (ifname[i] >= '0' && ifname[i] <= '9')
            break;
    if (i >= len)
        return;

    memset(&vlan_key, 0, sizeof(struct VLAN_ID));
    vlan_key.vid = atoi(&ifname[i]);

    if ((sys = system_get_instance()) != NULL)
    {
        RB_FOREACH (lif, lif_rb_tree, &(sys->lif_tree))
        {
            if (lif->type == IF_T_VLAN)
                continue;

            vlan = RB_FIND(vlan_rb_tree, &(lif->vlan_tree), &vlan_key);
            if (vlan)
            {
                ICCPD_LOG_DEBUG(__FUNCTION__, "%s is member of Vlan (%d)", lif_vlan->name, vlan->vid);
                vlan->vlan_itf = NULL;
            }
        }
    }

    return;
}

static void local_if_po_remove(struct LocalInterface *lif_po)
{
    struct System *sys = NULL;
    struct CSM *csm = NULL;
    struct LocalInterface *lif = NULL;

    if (lif_po->type != IF_T_PORT_CHANNEL)
        return;

    /* remove all po member*/
    if ((sys = system_get_instance()) != NULL)
    {
        csm = lif_po->csm;
        if (csm)
        {
            LIST_FOREACH(lif, &(MLACP(csm).lif_list), mlacp_next)
            {
                if (lif->type != IF_T_PORT)
                    continue;
                if (lif->po_id != lif_po->po_id)
                    continue;

                mlacp_unbind_local_if(lif);
            }
        }
    }

    return;
}

static void local_if_remove(struct LocalInterface *lif)
{
    mlacp_unbind_local_if(lif);
    lif->po_id = -1;

    return;
}

void local_if_destroy(struct LocalInterface *lif)
{
    struct CSM *csm = NULL;
    struct System *sys = NULL;

    if (!(sys = system_get_instance()))
        return;

    ICCPD_LOG_WARN(__FUNCTION__, "Destroy interface %s, %d\n", lif->name, lif->ifindex);

    if (lif->type == IF_T_VLAN)
        local_if_vlan_remove(lif);
    else if (lif->type == IF_T_PORT_CHANNEL)
        local_if_po_remove(lif);
    else
        local_if_remove(lif);

    csm = lif->csm;
    if (csm && csm->peer_link_if && strcmp(csm->peer_link_if->name, lif->name) == 0)
    {
        /*if the peerlink interface is not created, peer connection can not establish*/
        scheduler_session_disconnect_handler(csm);
        csm->peer_link_if->is_peer_link = 0;
        csm->peer_link_if = NULL;
    }

    if (csm && MLACP(csm).current_state == MLACP_STATE_EXCHANGE)
        goto to_mlacp_purge;
    else
        goto to_sys_purge;

 to_sys_purge:
    /* sys purge */
    LIF_RB_REMOVE(lif_rb_tree, &(sys->lif_tree), lif);
    if (lif->csm)
        LIST_REMOVE(lif, mlacp_next);
    LIST_INSERT_HEAD(&(sys->lif_purge_list), lif, system_purge_next);
    return;

 to_mlacp_purge:
    /* sys & mlacp purge */
    LIF_RB_REMOVE(lif_rb_tree, &(sys->lif_tree), lif);
    LIST_REMOVE(lif, mlacp_next);
    LIST_INSERT_HEAD(&(sys->lif_purge_list), lif, system_purge_next);
    LIST_INSERT_HEAD(&(MLACP(csm).lif_purge_list), lif, mlacp_purge_next);
    return;
}

int local_if_is_l3_mode(struct LocalInterface* local_if)
{
    int ret = 0;
    char addr_null[16] = { 0 };

    if (local_if == NULL)
        return 0;

    if (local_if->ipv4_addr != 0 || memcmp(local_if->ipv6_addr, addr_null, 16) != 0)
        ret = 1;

    return ret;
}

void local_if_change_flag_clear(void)
{
    struct System* sys = NULL;
    struct LocalInterface* lif = NULL;

    if ((sys = system_get_instance()) == NULL)
        return;

    RB_FOREACH (lif, lif_rb_tree, &(sys->lif_tree))
    {
        if (lif->changed == 1)
        {
            lif->changed = 0;
        }
    }

    return;
}

void local_if_purge_clear(void)
{
    struct System* sys = NULL;
    struct LocalInterface* lif = NULL;

    if ((sys = system_get_instance()) == NULL)
        return;

    /* destroy purge if*/
    while (!LIST_EMPTY(&(sys->lif_purge_list)))
    {
        lif = LIST_FIRST(&(sys->lif_purge_list));
        ICCPD_LOG_DEBUG(__FUNCTION__, "Purge %s", lif->name);
        LIST_REMOVE(lif, system_purge_next);
        if (lif->mlacp_purge_next.le_next != 0 && lif->mlacp_purge_next.le_prev != 0)
            LIST_REMOVE(lif, mlacp_purge_next);
        local_if_del_all_vlan(lif);
        local_if_del_all_portchannel_member(lif);
        free(lif);
    }

    LIST_INIT(&(sys->lif_purge_list));

    return;
}

void local_if_finalize(struct LocalInterface* lif)
{
    if (lif == NULL)
        return;

    local_if_del_all_vlan(lif);
    local_if_del_all_portchannel_member(lif);

    free(lif);

    return;
}

struct PeerInterface* peer_if_create(struct CSM* csm,
                                     int peer_if_number, int type)
{
    struct PeerInterface* peer_if = NULL;

    /* check csm*/
    if (csm == NULL)
        return NULL;

    /* check id*/
    if (peer_if_number < 0)
    {
        ICCPD_LOG_WARN(__FUNCTION__, "peer interface id < 0");
        return NULL;
    }

    /* check type*/
    if (type != IF_T_PORT && type != IF_T_PORT_CHANNEL)
    {
        ICCPD_LOG_WARN(__FUNCTION__,
                       "The type(%) of peer interface(%d) is not acceptable",
                       type, peer_if_number);
        return NULL;
    }

    /* create a new peer if*/
    if ((peer_if = (struct PeerInterface*)malloc(sizeof(struct PeerInterface))) == NULL)
    {
        ICCPD_LOG_WARN(__FUNCTION__, "Peer port id = %d, malloc failed", peer_if_number);
        return NULL;
    }
    memset(peer_if, 0, sizeof(struct PeerInterface));

    if (type == IF_T_PORT)
    {
        peer_if->ifindex = peer_if_number;
        peer_if->type = IF_T_PORT;
        peer_if->csm = csm;
    }
    else if (type == IF_T_PORT_CHANNEL)
    {
        peer_if->ifindex = peer_if_number;
        peer_if->type = IF_T_PORT_CHANNEL;
    }

    LIST_INSERT_HEAD(&(MLACP(csm).pif_list), peer_if, mlacp_next);

    return peer_if;
}

struct PeerInterface* peer_if_find_by_name(struct CSM* csm, char* name)
{
    struct System* sys = NULL;
    struct PeerInterface* peer_if = NULL;

    if ((sys = system_get_instance()) == NULL)
        return NULL;

    if (csm == NULL)
        return NULL;

    LIST_FOREACH(peer_if, &(csm->app_csm.mlacp.pif_list), mlacp_next)
    {
        if (strcmp(peer_if->name, name) == 0)
            return peer_if;
    }

    return NULL;
}

void peer_if_del_all_vlan(struct PeerInterface* pif)
{
    struct VLAN_ID *vlan = NULL;
    struct VLAN_ID* vlan_temp = NULL;

    ICCPD_LOG_NOTICE(__FUNCTION__, "Remove all VLANs from peer intf %s", pif->name);
    RB_FOREACH_SAFE(vlan, vlan_rb_tree, &(pif->vlan_tree), vlan_temp)
    {
        VLAN_RB_REMOVE(vlan_rb_tree, &(pif->vlan_tree), vlan);
        free(vlan);
    }

    return;
}

void peer_if_destroy(struct PeerInterface* pif)
{
    ICCPD_LOG_WARN(__FUNCTION__, "Destroy peer's interface %s, %d",
                   pif->name, pif->ifindex);

    /* destroy if*/
    LIST_REMOVE(pif, mlacp_next);
    peer_if_del_all_vlan(pif);

    free(pif);
    return;
}

int local_if_add_vlan(struct LocalInterface* local_if, uint16_t vid)
{
    struct VLAN_ID *vlan = NULL;
    struct VLAN_ID vlan_key = { 0 };
    char vlan_name[16] = "";

    sprintf(vlan_name, "Vlan%d", vid);

    memset(&vlan_key, 0, sizeof(struct VLAN_ID));
    vlan_key.vid = vid;

    vlan = RB_FIND(vlan_rb_tree, &(local_if->vlan_tree), &vlan_key);
    if (!vlan)
    {
        vlan = (struct VLAN_ID*)malloc(sizeof(struct VLAN_ID));
        if (!vlan)
            return MCLAG_ERROR;

        vlan_info_init(vlan);
        vlan->vid = vid;
        vlan->vlan_itf = local_if_find_by_name(vlan_name);

        ICCPD_LOG_DEBUG(__FUNCTION__, "Add %s to VLAN %d", local_if->name, vid);
        local_if->port_config_sync = 1;
        RB_INSERT(vlan_rb_tree, &(local_if->vlan_tree), vlan);

        /* If peer-link add to vlan, check the MAC list that redirected to the peer-link */
        if (local_if->is_peer_link)
        {
            struct CSM* csm;
            struct System* sys = NULL;
            struct Msg* msg = NULL;
            struct MACMsg* mac_msg = NULL;

            sys = system_get_instance();
            if (sys == NULL)
            {
                ICCPD_LOG_ERR(__FUNCTION__, "Sys get failure");
                return 0;
            }

            LIST_FOREACH(csm, &(sys->csm_list), next)
            {
                if (csm->peer_link_if == local_if)
                {
                    break;
                }
            }

            if (csm != NULL)
            {
                /* Check the MAC list that redirected to the peer-link, if the vlan of MAC is */
                /* the same as the vlan currently added, install the MAC to ASIC*/
                TAILQ_FOREACH(msg, &MLACP(csm).mac_list, tail)
                {
                    mac_msg = (struct MACMsg*)msg->buf;

                    if (strlen(csm->peer_itf_name) != 0 && strcmp(mac_msg->ifname, csm->peer_itf_name) == 0 
                        && mac_msg->vid == vid)
                    {
                        add_mac_to_chip(csm, mac_msg, MAC_TYPE_DYNAMIC);
                    }
                }
            }
            else
            {
                ICCPD_LOG_ERR(__FUNCTION__, "CSM get failure for add %s to VLAN %d", local_if->name, vid);
            }
        }
    }

    vlan->vlan_removed = 0;

    update_if_ipmac_on_standby(local_if);

    return 0;
}

void local_if_del_vlan(struct LocalInterface* local_if, uint16_t vid)
{
    if (local_if == NULL)
    {
        return;
    }

    /* If peer-link remove from vlan, check the MAC list that redirected to the peer-link */
    if (local_if->is_peer_link)
    {
        struct CSM* csm;
        struct System* sys = NULL;
        struct Msg* msg = NULL;
        struct MACMsg* mac_msg = NULL;

        sys = system_get_instance();
        if (sys == NULL)
        {
            return;
        }

        LIST_FOREACH(csm, &(sys->csm_list), next)
        {
            if (csm->peer_link_if == local_if )
            {
                break;
            }
        }

        if (csm == NULL)
        {
            return;
        }

        /* Check the MAC list that redirected to the peer-link, if the vlan of MAC is */
        /* the same as the vlan currently added, delete the MAC from ASIC*/
        TAILQ_FOREACH(msg, &MLACP(csm).mac_list, tail)
        {
            mac_msg = (struct MACMsg*)msg->buf;

            if (strlen(csm->peer_itf_name) != 0 && strcmp(mac_msg->ifname, csm->peer_itf_name) == 0 
                && mac_msg->vid == vid)
            {
                del_mac_from_chip(mac_msg);
            }
        }
    }

    local_if->port_config_sync = 1;

    return;
}

void local_if_del_all_portchannel_member(struct LocalInterface* lif)
{
    struct PortChannel_member *member = NULL;

    ICCPD_LOG_NOTICE(__FUNCTION__, "Remove all portchannel_member from %s", lif->name);
    while (!LIST_EMPTY(&(lif->member_list)))
    {
        member = LIST_FIRST(&(lif->member_list));
        LIST_REMOVE(member, member_next);
        free(member);
    }

    LIST_INIT(&(lif->member_list));
    return;
}

void local_if_del_all_vlan(struct LocalInterface* lif)
{
    struct VLAN_ID* vlan = NULL;
    struct VLAN_ID* vlan_temp = NULL;

    ICCPD_LOG_NOTICE(__FUNCTION__, "Remove all VLANs from %s", lif->name);
    RB_FOREACH_SAFE(vlan, vlan_rb_tree, &(lif->vlan_tree), vlan_temp)
    {
        VLAN_RB_REMOVE(vlan_rb_tree, &(lif->vlan_tree), vlan);
        free(vlan);
    }

    return;
}

/* Add VLAN from peer-link*/
int peer_if_add_vlan(struct PeerInterface* peer_if, uint16_t vlan_id)
{
    struct VLAN_ID *peer_vlan = NULL;
    struct VLAN_ID vlan_key = { 0 };
    char vlan_name[16] = "";

    sprintf(vlan_name, "Vlan%d", vlan_id);

    memset(&vlan_key, 0, sizeof(struct VLAN_ID));
    vlan_key.vid = vlan_id;

    peer_vlan = RB_FIND(vlan_rb_tree, &(peer_if->vlan_tree), &vlan_key);

    if (!peer_vlan)
    {
        peer_vlan = (struct VLAN_ID*)malloc(sizeof(struct VLAN_ID));
        if (!peer_vlan)
            return MCLAG_ERROR;

        vlan_info_init(peer_vlan);
        peer_vlan->vid = vlan_id;

        ICCPD_LOG_DEBUG(__FUNCTION__, "Add peer intf %s to VLAN %d", peer_if->name, vlan_id);
        RB_INSERT(vlan_rb_tree, &(peer_if->vlan_tree), peer_vlan);
    }

    peer_vlan->vlan_removed = 0;

    return 0;
}

/* Used by sync update*/
int peer_if_clean_unused_vlan(struct PeerInterface* peer_if)
{
    struct VLAN_ID *peer_vlan = NULL;
    struct VLAN_ID *peer_vlan_next = NULL;
    struct VLAN_ID *vlan_temp = NULL;

    /* traverse 1 time */
    RB_FOREACH_SAFE(peer_vlan_next, vlan_rb_tree, &(peer_if->vlan_tree), vlan_temp)
    {
        if (peer_vlan != NULL)
        {
            ICCPD_LOG_DEBUG(__FUNCTION__, "Remove peer intf %s from VLAN %d", peer_if->name, peer_vlan->vid);
            VLAN_RB_REMOVE(vlan_rb_tree, &(peer_if->vlan_tree), peer_vlan);
            free(peer_vlan);
            peer_vlan = NULL;

        }
        if (peer_vlan_next->vlan_removed == 1)
            peer_vlan = peer_vlan_next;
    }

    if (peer_vlan != NULL)
    {
        ICCPD_LOG_DEBUG(__FUNCTION__, "Remove peer intf %s from VLAN %d", peer_if->name, peer_vlan->vid);
        VLAN_RB_REMOVE(vlan_rb_tree, &(peer_if->vlan_tree), peer_vlan);
        free(peer_vlan);
    }

    return 0;
}

int set_sys_arp_accept_flag(char* ifname, int flag)
{
    FILE *file_ptr = NULL;
    char cmd[64];
    char arp_file[64];
    char buf[2];
    int result = MCLAG_ERROR;

    memset(arp_file, 0, 64);
    snprintf(arp_file, 63, "/proc/sys/net/ipv4/conf/%s/arp_accept", ifname);
    if (!(file_ptr = fopen(arp_file, "r")))
    {
        ICCPD_LOG_WARN(__func__, "Failed to find device %s from %s", ifname, arp_file);
        return result;
    }

    fgets(buf, sizeof(buf), file_ptr);
    if (atoi(buf) == flag)
        result = 0;
    else
    {
        memset(cmd, 0, 64);
        snprintf(cmd, 63, "echo %d > /proc/sys/net/ipv4/conf/%s/arp_accept", flag, ifname);
        if (system(cmd))
            ICCPD_LOG_WARN(__func__, "Failed to execute cmd = %s", flag, cmd);
    }

    fclose(file_ptr);
    return result;
}
