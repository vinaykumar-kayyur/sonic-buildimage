#include <stdio.h>
#include <assert.h>
#include <linux/bpf.h>
#include <string.h>
#include <stdlib.h>
#include <stddef.h>
#include <errno.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <linux/if_ether.h>
#include <stddef.h>
#include <linux/if_link.h>
#include <linux/bpf.h>
#include <linux/filter.h>
#include <linux/if_link.h>
#include <linux/rtnetlink.h>
#include <stdbool.h>
#include <unistd.h>
#include <stdint.h>
#include <linux/if_arp.h>
#include <linux/bpf_common.h>
#include "ebpf/libebpf.h"
#include "ebpf/libbpf.h"
#include "ebpf/bpf_load.h"


extern char bpf_log_buf[65536];

char bpf_log_buf[65536];
int socket_create()
{
	/*int sock = socket(AF_UNIX, SOCK_DGRAM, 0);*/
	int sock = socket(AF_NETLINK, SOCK_RAW, NETLINK_ROUTE);
    return sock;
}

int create_netlink_socket()
{
    int nl_fd = 0;

    struct sockaddr_nl sa = {
        .nl_family = AF_NETLINK,
        .nl_pad    = 0,
        .nl_pid    = 0,
        .nl_groups = RTMGRP_LINK
    };


    nl_fd = socket(AF_NETLINK, SOCK_RAW, NETLINK_ROUTE);
    if (nl_fd == -1)
    {
        printf("nl_fd CREATE Failed : %s", strerror(errno));
        return -1;
    }

    if(bind(nl_fd, (struct sockaddr *) &sa, sizeof(sa)) == -1)
    {
        printf("nl_fd BIND Failed : %s", strerror(errno));
        return -1;
    }

    return nl_fd;
}



int timer_test()
{

    int sock_fd = -1;
    char filename[256];
    sock_fd = socket_create();

    snprintf(filename, sizeof(filename), "ebpd_timer.bpf");

    if (load_bpf_file(filename)) {
        printf("%s", bpf_log_buf);
        return 1;
    }

    assert(setsockopt(sock_fd, SOL_SOCKET, SO_ATTACH_BPF, prog_fd,
              sizeof(prog_fd[0])) == 0);

    return 0;
}
int main(int argc, char *argv[])
{
	if(argc <2){
		printf("Usage: %s <ebpf filter object>\n",argv[0] );
		exit(0);
	}

	int sd=create_netlink_socket();
	if (sd == -1)
	{
		printf("sock CREATE Failed : %s", strerror(errno));
		return -1;
	}
	attach_ebpf_filter(sd,argv[1]);
}
