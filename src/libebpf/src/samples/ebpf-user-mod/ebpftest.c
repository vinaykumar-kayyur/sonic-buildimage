#include <linux/kconfig.h>
#include <linux/socket.h>
#include <linux/if_ether.h>
#include <linux/if_packet.h>
#include <linux/ip.h>
#include <linux/if.h>
#include <linux/if_link.h>
#include <linux/rtnetlink.h>
#include <linux/byteorder/generic.h>
#include <net/netlink.h>
#include "ebpf/bpf_helpers.h"
#include "ebpf/bpf_helpers.h"
#include "ebpftest.h"
#include <linux/bpf.h>


struct bpf_map_def SEC("maps") my_map = {
	.type = BPF_MAP_TYPE_HASH,
	.key_size = sizeof(KEY),
	.value_size = sizeof(VALUE),
	.max_entries = 256,
};

SEC("socket")
int bpf_prog1(struct __sk_buff *skb)
{

	uint16_t nlmsg_flags = load_half(skb, offsetof(struct  nlmsghdr, nlmsg_flags));
	nlmsg_flags = htons(nlmsg_flags);

	// accept all pkts with NLM_F_MULTI flag set
	if ( nlmsg_flags & NLM_F_MULTI)
		BPF_MAP_ACCEPT_PKT(&my_map);

	uint16_t nlmsg_type = load_half(skb, offsetof(struct nlmsghdr, nlmsg_type));
	nlmsg_type = htons(nlmsg_type);

	//accept pkt for end of Multi msg
	if (nlmsg_type == NLMSG_DONE)
		BPF_MAP_ACCEPT_PKT(&my_map);

	if ( (nlmsg_type != RTM_NEWLINK)
		&& (nlmsg_type != RTM_DELLINK))
	{
		BPF_TR(" TEAMD : [%d] >> Unknown Type : pkt: %d\n", INVALID_IFINDEX, nlmsg_type);
		BPF_MAP_DROP_PKT(&my_map);
	}

	uint8_t ifi_family = load_byte(skb, sizeof(struct nlmsghdr) + offsetof(struct  ifinfomsg, ifi_family)); 
	if (ifi_family != AF_UNSPEC)
	{
		BPF_TR(" TEAMD : [%d] >> Invalid family : %d\n", INVALID_IFINDEX, ifi_family);
		BPF_MAP_DROP_PKT(&my_map);
	}

	int ifname_hex = 0;
	KEY m_key = {0, 0}; 
	VALUE new_val = {0};

	int kif_index = load_word(skb, sizeof(struct nlmsghdr) + offsetof(struct  ifinfomsg, ifi_index));
	kif_index = _htonl(kif_index);
	m_key.ifidx = kif_index;

	int tlv_off_st = (sizeof(struct nlmsghdr) + sizeof(struct  ifinfomsg));
	int tlv_off = bpf_find_nlattr(skb, tlv_off_st, IFLA_IFNAME);
	if(tlv_off != 0)
	{
		BPF_TR(" TEAMD : [%d] >> found IFLA_IFNAME @ off : %d\n", m_key.ifidx, tlv_off);
		ifname_hex = load_word(skb, tlv_off+sizeof(struct nlattr));
	}

	if ( (ifname_hex != ETH_ASCII)
		 && (ifname_hex != PO_ASCII) )
	{
		BPF_TR(" TEAMD : [%d] >> Not of Ethernet or PortChannel, ifname : %x\n", m_key.ifidx, ifname_hex);
		BPF_MAP_DROP_PKT(&my_map);
	}


	BPF_TR(" TEAMD : [%d] >> Recv Pkt : %d\n", m_key.ifidx, nlmsg_type);

	if (nlmsg_type == RTM_DELLINK)
	{
		bpf_map_delete_elem(&my_map, &m_key);
		BPF_MAP_ACCEPT_PKT(&my_map);
	}

	int t_flags = load_word(skb, sizeof(struct nlmsghdr) + offsetof(struct  ifinfomsg, ifi_flags));
	new_val.team_info.flags |= (t_flags & _htonl(IFF_RUNNING));
	new_val.team_info.flags |= (t_flags & _htonl(IFF_UP));

	tlv_off = bpf_find_nlattr(skb, tlv_off_st, IFLA_MASTER);
	if(tlv_off != 0)
	{
		BPF_TR(" TEAMD : [%d] >> found IFLA_MASTER @ off : %d\n", m_key.ifidx, tlv_off);
		new_val.team_info.master = load_word(skb, tlv_off+sizeof(struct nlattr));
	}

	tlv_off = bpf_find_nlattr(skb, tlv_off_st, IFLA_ADDRESS);
	if(tlv_off != 0)
	{
		BPF_TR(" TEAMD : [%d] >> found IFLA_ADDRESS @ off : %d\n", m_key.ifidx, tlv_off);
		new_val.team_info.mac_addr[0] = load_byte(skb, 0+tlv_off+sizeof(struct nlattr));
		new_val.team_info.mac_addr[1] = load_byte(skb, 1+tlv_off+sizeof(struct nlattr));
		new_val.team_info.mac_addr[2] = load_byte(skb, 2+tlv_off+sizeof(struct nlattr));
		new_val.team_info.mac_addr[3] = load_byte(skb, 3+tlv_off+sizeof(struct nlattr));
		new_val.team_info.mac_addr[4] = load_byte(skb, 4+tlv_off+sizeof(struct nlattr));
		new_val.team_info.mac_addr[5] = load_byte(skb, 5+tlv_off+sizeof(struct nlattr));
	}

	tlv_off = bpf_find_nlattr(skb, tlv_off_st, IFLA_PHYS_PORT_ID);
	if(tlv_off != 0)
	{
		BPF_TR(" TEAMD : [%d] >> found IFLA_PHYS_PORT_ID @ off : %d\n", m_key.ifidx, tlv_off);
		new_val.team_info.ppid.id[0] = load_byte(skb, 0+tlv_off+sizeof(struct nlattr));
		new_val.team_info.ppid.id[1] = load_byte(skb, 1+tlv_off+sizeof(struct nlattr));
		new_val.team_info.ppid.id[2] = load_byte(skb, 2+tlv_off+sizeof(struct nlattr));
		new_val.team_info.ppid.id[3] = load_byte(skb, 3+tlv_off+sizeof(struct nlattr));
		new_val.team_info.ppid.id[4] = load_byte(skb, 4+tlv_off+sizeof(struct nlattr));
		new_val.team_info.ppid.id[5] = load_byte(skb, 5+tlv_off+sizeof(struct nlattr));
	}


	tlv_off = bpf_find_nlattr(skb, tlv_off_st, IFLA_LINKINFO);
	if(tlv_off != 0)
	{
		BPF_TR(" TEAMD : [%d] >> found IFLA_LINKINFO @ off : %d\n", m_key.ifidx,tlv_off);
		tlv_off = bpf_find_nlattr_nest(skb, tlv_off, IFLA_INFO_SLAVE_KIND);
		if(tlv_off != 0)
		{
			new_val.team_info.slave_info = load_word(skb, tlv_off+sizeof(struct nlattr));
			BPF_TR(" TEAMD : [%d] >> found IFLA_INFO_SLAVE @ off : %d\n slave-info : %x",tlv_off, new_val.team_info.slave_info);
		}
		else
			BPF_TR(" TEAMD : [%d] >> NOT found SLAVE_IFLA_LINKINFO @ off : %d\n", m_key.ifidx,tlv_off);
	}
	else
		BPF_TR(" TEAMD : [%d] >> NOT found IFLA_LINKINFO @ off : %d\n", m_key.ifidx,tlv_off);


	VALUE *old_val = 0;
	uint8_t update_flag = 0;

	old_val = bpf_map_lookup_elem(&my_map, &m_key);
	if (old_val)
	{

		/*if (memcmp(&old_val->team_info, &new_val.team_info, sizeof(TEAMD_INFO)) != 0)*/
		if (	   (old_val->team_info.slave_info != new_val.team_info.slave_info)
				|| (old_val->team_info.master != new_val.team_info.master)
				|| (old_val->team_info.flags != new_val.team_info.flags)
				|| (*((uint32_t *)&old_val->team_info.mac_addr[0]) != *((uint32_t *)&new_val.team_info.mac_addr[0]))
				|| (*((uint16_t *)&old_val->team_info.mac_addr[4]) != *((uint16_t *)&new_val.team_info.mac_addr[4]))
				|| (*((uint32_t *)&old_val->team_info.ppid.id[0])  != *((uint32_t *)&new_val.team_info.ppid.id[0]))
				|| (*((uint16_t *)&old_val->team_info.ppid.id[4])  != *((uint16_t *)&new_val.team_info.ppid.id[4]))
		   )
		{
			new_val.count = old_val->count + 1;
			bpf_map_update_elem(&my_map, &m_key, &new_val, BPF_EXIST);
		}
		else
		{
			BPF_TR(" TEAMD : [%d] >> No Change Drop pkt\n", m_key.ifidx);
			BPF_MAP_DROP_PKT(&my_map);
		}
	} 
	else {
		bpf_map_update_elem(&my_map, &m_key, &new_val, BPF_NOEXIST);
	}

	BPF_TR("TEAMD: [%d] >> ACCEPT\n\n", m_key.ifidx);
	BPF_MAP_ACCEPT_PKT(&my_map);
}
char _license[] SEC("license") = "GPL";
