/**
 * Copyright(C) 2010 Ruijie Network. All rights reserved.
 */
/*
 * hw_misc.h
 * Original Author : liangeb@ruijie.com.cn, 2012-07-26
 *
 * MISC HardWare test definitions
 *
 * History
 *    v1.0    enbo liang(liangeb@ruijie.com.cn)  2012-07-26  Initial version.
 */
#ifndef _HW_MISC_H
#define _HW_MISC_H

typedef unsigned long long  u64;
#define MAX_DATA_SIZE      16

extern int reload_main(int argc, char **argv);
extern int sys_info_main(int argc, char **argv);
extern int mem_dump_main(int argc, char **argv);
extern int cache_flush_main(int argc, char **argv);
extern int reg_wr64_main(int argc, char **argv);
extern int reg_rd64_main(int argc, char **argv);
extern int reg_wr32_main(int argc, char **argv);
extern int reg_rd32_main(int argc, char **argv);
extern int reg_wr16_main(int argc, char **argv);
extern int reg_rd16_main(int argc, char **argv);
extern int reg_wr8_main(int argc, char **argv);
extern int reg_rd8_main(int argc, char **argv);
extern int mdio_rd_main(int argc, char **argv);
extern int mdio_wr_main(int argc, char **argv);
extern int lpc_cpld_wr8_main(int argc, char **argv);
extern int lpc_cpld_rd8_main(int argc, char **argv);

#endif /* _HW_MISC_H */

