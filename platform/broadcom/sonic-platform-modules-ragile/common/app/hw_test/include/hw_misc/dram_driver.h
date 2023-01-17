/**
 * Copyright(C) 2010 Ruijie Network. All rights reserved.
 */
/*
 * octeon_cpld_drv.h
 * Original Author : liangeb@ruijie.com.cn, 2012-07-06
 *
 * octeon Dram Driver header file
 *
 * History
 *    v1.0    enbo liang(liangeb@ruijie.com.cn)  2012-07-06  Initial version.
 */

#ifndef _LINUX_DRAM_DRIVER_H
#define _LINUX_DRAM_DRIVER_H

#include <linux/types.h>
typedef unsigned int u32;

struct mdio_user_info {
    u32  c45;
    u32  bus_id;
    u32  phy_addr;
    u32  device;
    u32  location;
    u32  value;
};

#define MDIO_READ                        _IOR('D', 1, struct mdio_user_info)
#define MDIO_WRITE                       _IOR('D', 2, struct mdio_user_info)

#endif
