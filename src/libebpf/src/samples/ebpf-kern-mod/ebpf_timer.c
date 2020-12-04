#include <uapi/linux/bpf.h>
#include <uapi/linux/if_ether.h>
#include <uapi/linux/if_packet.h>
#include <uapi/linux/ip.h>
#include <uapi/linux/if.h>
#include <uapi/linux/if_link.h>
#include <uapi/linux/rtnetlink.h>
#include <linux/byteorder/generic.h>
#include <net/netlink.h>
#include "ebpf/bpf_helpers.h"
#include "ebpf/bpf_helpers.h"
#include "ebpftest.h"
#include <linux/ptrace.h>
/*#include <linux/bpf.h>*/
/*#include "ebpf/bpf_helpers.h"*/
/*#define SEC(NAME) __attribute__((section(NAME), used))*/

#define __uint(name, val) int (*name)[val]
#define __type(name, val) val *name


struct {
    __uint(type, BPF_MAP_TYPE_PERF_EVENT_ARRAY);
    __uint(key_size, sizeof(int));
    __uint(value_size, sizeof(int));
} perf_buf_map SEC(".maps");

SEC("kprobe/sys_nanosleep")
int nanosec_timer(struct pt_regs *ctx)
{
    int cpu = bpf_get_smp_processor_id();

    bpf_perf_event_output(ctx, &perf_buf_map, BPF_F_CURRENT_CPU,
            &cpu, sizeof(cpu));
    bpf_printk("%s\n","RDX");
    return 0;
}

char _license[] SEC("license") = "GPL";
__u32 _version SEC("version") = 1;
