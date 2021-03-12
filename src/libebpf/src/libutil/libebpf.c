/*
 * Copyright 2019 Broadcom. All rights reserved. 
 * The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.
 *
 * Author: Kalimuthu Velappan
 * Email : kalimuthu.velappan@broadcom.com
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 */

#include <stdio.h>
#include <assert.h>
#include <linux/bpf.h>
#include <string.h>
#include <stdlib.h>
#include <stddef.h>
#include <errno.h>
#include <syslog.h>
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


void open_syslog(char *filename)
{ 
	char filectl[128]="";
	sprintf(filectl, "libebpf#%s",filename);

	setlogmask (LOG_UPTO (LOG_NOTICE));
	openlog (filectl, LOG_CONS | LOG_PID | LOG_NDELAY, LOG_LOCAL1);
}
void close_syslog()
{
	closelog();
}


__attribute__ ((visibility("default"))) int attach_ebpf_filter(int nl_fd, char *filename)
{
	char filectl[128]="";
	

	sprintf(filectl, "%s.enable",filename);
	if( access( filectl, F_OK ) == -1 )
	{
		syslog(LOG_INFO, "Filter %s is disabled\n", filename);
		return 0;
	}

	if (load_bpf_file(filename)) {
		syslog(LOG_ERR, "%s", bpf_log_buf);
		syslog(LOG_ERR, "Filter load is failed for %s socket \n", filename);
		return 0;
	}

	if(setsockopt(nl_fd, SOL_SOCKET, SO_ATTACH_BPF, prog_fd, sizeof(prog_fd[0])) != 0)
	{
		perror("Filter attach failed: ");
		syslog(LOG_ERR, "Filter attach is failed for %s socket \n", filename);
		return 0;
	}
	syslog(LOG_INFO, "Filter is attached successfully for %s socket \n", filename);
	return 0;
}

#ifdef MAIN
int main(int argc, char *argv[])
{
	printf("\n");
	return 0;
}
#endif




