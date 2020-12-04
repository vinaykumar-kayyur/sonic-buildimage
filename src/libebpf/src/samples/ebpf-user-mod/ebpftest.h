#ifndef __EBPFTEST_H__
#define __EBPFTEST_H__

#pragma pack(push,1)
typedef struct {
	int ifidx;
	int pad;
}KEY;



#define MAX_PHYS_ITEM_ID_LEN 32

/* This structure holds a unique identifier to identify some
 *  * physical item (port for example) used by a netdevice.
 *   */
#if 0
struct netdev_phys_item_id {
	unsigned char id[MAX_PHYS_ITEM_ID_LEN];
	unsigned char id_len;
};
#endif

#define KEY_VALUE_FORMAT "K:%d, V:(S[%x] M[%x] F[%x] MC[%x:%x:%x:%x:%x:%x] P[%x:%x:%x:%x:%x:%x])"
typedef struct {
	// i think name can never change for a given kernel ifindex 
	// not sure why teamd code checks for this as well.
	// To reduce complexity of filter logic i'm commenting this out for now.
	/*char		ifname[IFNAMSIZ];*/
	int slave_info;
	int	master;
	int	flags;
	char mac_addr[6];
	struct netdev_phys_item_id ppid;
}TEAMD_INFO;

typedef struct {
	int count;
	int accept;
	TEAMD_INFO team_info;
}VALUE;
#pragma pack(pop)

/* compiler workaround */
#define _htonl __builtin_bswap32

#define DEBUG_MODE_ON
#define ACCEPT_PKT 0xFFFF
#define DROP_PKT 0
#define INVALID_IFINDEX 0

#define ETH_ASCII 0x45746865 // Ascii equivalent for "Ethe" to filter out Ethernet nl-msgs
#define PO_ASCII 0x506F7274  // Ascii equivalent for "Port" to filter out Portchannel nl-msgs
#define TEAM_ASCII 0x7465616d // Ascii equivalent for "team" to filter out Ethernet nl-msgs

#ifdef DEBUG_MODE_ON
#define BPF_TR(_fmt,...) \
{ \
	char fmt[]=_fmt; \
	bpf_trace_printk(fmt, sizeof(fmt), ##__VA_ARGS__); \
}
#else
#define BPF_TR(_fmt,...) {};
#endif



/*if(drop_counter_val->count %100 == 0) BPF_TR("DROP COUNT: %d\n",drop_counter_val->count); */
#define  BPF_MAP_DROP_PKT(map)  \
{ \
	KEY counter_key = {0, 50000}; \
	VALUE *counter_val = (VALUE*)bpf_map_lookup_elem(map, &counter_key); \
	if ( counter_val ){        \
		counter_val->count++;  \
		BPF_TR("TEAMD: [%d] >> DROP [ %d ] \n\n", 0, counter_val->count); \
	}else{ \
		VALUE init_counter_val ={0}; \
		bpf_map_update_elem(map, &counter_key, &init_counter_val, BPF_NOEXIST); \
		BPF_TR("TEAMD: [%d] >> INIT DROP [ %d ] \n\n", 0,  init_counter_val.count); \
	}                \
	return DROP_PKT; \
}\



#define  BPF_MAP_ACCEPT_PKT(map)  \
{ \
	KEY counter_key = {0, 50000}; \
	VALUE *counter_val = (VALUE*)bpf_map_lookup_elem(map, &counter_key); \
	if ( counter_val ){        \
		counter_val->accept++;  \
		BPF_TR("TEAMD: [%d] >> ACCEPT [ %d ] \n\n", 0, counter_val->accept); \
	}else{ \
		VALUE init_counter_val ={0}; \
		bpf_map_update_elem(map, &counter_key, &init_counter_val, BPF_NOEXIST); \
		BPF_TR("TEAMD: [%d] >> INIT ACCEPT [ %d ] \n\n", 0,  init_counter_val.accept); \
	}                \
	return ACCEPT_PKT; \
}\

#endif
