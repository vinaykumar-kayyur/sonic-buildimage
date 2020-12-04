#ifndef __LIBEBPF_H__
#define __LIBEBPF_H__

/* compiler workaround */
#define _htonl __builtin_bswap32

#define DEBUG_MODE_ON
#define ACCEPT_PKT 0xFFFF
#define DROP_PKT 0


#ifdef DEBUG_MODE_ON
#define BPF_TR(_fmt,...) \
{ \
	char fmt[]=_fmt; \
	bpf_trace_printk(fmt, sizeof(fmt), ##__VA_ARGS__); \
}
#else
#define BPF_TR(_fmt,...) {};
#endif

#ifdef __cplusplus
extern "C" {
#endif

 int attach_ebpf_filter(int nl_fd, char *);

#ifdef __cplusplus
}
#endif


#endif
