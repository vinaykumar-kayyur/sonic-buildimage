/**
 * Copyright(C) 2010 Ragile Network. All rights reserved.
 */
/*
 * hw_misc.c
 * Original Author : support@ragilenetworks.com, 2012-07-26
 *
 * MISC HardWare test
 *
 * History
 *    v1.0    enbo liang(support@ragilenetworks.com)  2012-07-26  Initial version.
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <termios.h>
#include <fcntl.h>
#include <errno.h>
#include <string.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <hw_misc/hw_misc.h>
#include <hw_misc/dram_driver.h>


static void dram_help(char *name)
{
    fprintf(stderr,
            "Usage: %s  reg_addr [reg_data]                                         \r\n"
            "  reg_addr                                                             \r\n"
            "  reg_data                                                             \r\n",
            name);
    exit(1);
}


static void mdio_help(char *name)
{
    fprintf(stderr,
            "Usage: %s  is_c45 bus_id phy_id device reg_addr [reg_data]               \r\n"
            "  is_c45        use c45 mode                                             \r\n"
            "  bus_id        mdio bus number                                          \r\n"
            "  phy_id        phy address                                              \r\n"
            "  device        device                                                   \r\n"
            "  reg_addr      phy register offset                                      \r\n"
            "  reg_data      phy value                                                \r\n",
            name);
    exit(1);
}


static int dram_arg_parse(int argc, char **argv,
                          u64 *reg_addr, u64 *reg_data,
                          int min_arg)
{
    u64 reg_addr_tmp, reg_data_tmp = 0;
    char *end;
    int flags = 0;

    if (argc < min_arg) {
        return -EINVAL;
    }

    reg_addr_tmp = strtoul(argv[flags + 1], &end, 0);
    if (*end) {
        fprintf(stderr, "Error: reg addr invalid!\n");
        return -EINVAL;
    }

    if (argc > 2) {
        reg_data_tmp = strtoul(argv[flags + 2], &end, 0);
        if (*end) {
            fprintf(stderr, "Error: reg data invalid!\n");
            return -EINVAL;
        }
    }

    *reg_addr = reg_addr_tmp;
    *reg_data = reg_data_tmp;

    return 0;
}


static int mdio_arg_parse(int argc, char **argv,
                          u32 *isc45, u32 *busid, u32 *phyid,
                          u32 *deviceid, u32 *regoffset, u32 *regvalue,
                          int min_arg)
{
    int is_c45, bus_id, phy_id, device_id, reg_offset, value;
    char *end;
    int flags = 0;

    if (argc < min_arg) {
        return -EINVAL;
    }

    is_c45 = strtoul(argv[flags + 1], &end, 0);
    if (*end || is_c45 < 0 || is_c45 > 0xff) {
        fprintf(stderr, "Error: is_c45 id invalid!\n");
        return -EINVAL;
    }

    bus_id = strtoul(argv[flags + 2], &end, 0);
    if (*end || bus_id < 0 || bus_id > 0xff) {
        fprintf(stderr, "Error: bus id invalid!\n");
        return -EINVAL;
    }

    phy_id = strtoul(argv[flags + 3], &end, 0);
    if (*end || phy_id < 0 || phy_id > 0xffff) {
        fprintf(stderr, "Error: phy id invalid!\n");
        return -EINVAL;
    }

    device_id = strtoul(argv[flags + 4], &end, 0);
    if (*end || device_id < 0 || device_id > 0xffff) {
        fprintf(stderr, "Error: device id invalid!\n");
        return -EINVAL;
    }

    reg_offset = strtoul(argv[flags + 5], &end, 0);
    if (*end || reg_offset < 0 || reg_offset > 0xffff) {
        fprintf(stderr, "Error: reg location invalid!\n");
        return -EINVAL;
    }

    if (argc > 6) {
        value = strtoul(argv[flags + 6], &end, 0);
        if (*end) {
            fprintf(stderr, "Error: reg data invalid!\n");
            return -EINVAL;
        }
        *regvalue = value;
    }

    *isc45         =  is_c45;
    *busid         =  bus_id;
    *phyid         =  phy_id;
    *deviceid      =  device_id;
    *regoffset     =  reg_offset;

    return 0;
}

int reload_main(int argc, char **argv)
{
    char tmp[128];

    snprintf(tmp, sizeof(tmp), "%s", argv[0]);
    printf("%s, %d, %d, %s\r\n", __FUNCTION__, __LINE__, argc, tmp);
    return 0;
}


int sys_info_main(int argc, char **argv)
{
    char tmp[128];

    snprintf(tmp, sizeof(tmp), "%s", argv[0]);
    printf("%s, %d, %d, %s\r\n", __FUNCTION__, __LINE__, argc, tmp);
    return 0;
}


int mem_dump_main(int argc, char **argv)
{
    char tmp[128];

    snprintf(tmp, sizeof(tmp), "%s", argv[0]);
    printf("%s, %d, %d, %s\r\n", __FUNCTION__, __LINE__, argc, tmp);
    return 0;
}


int cache_flush_main(int argc, char **argv)
{
    char tmp[128];

    snprintf(tmp, sizeof(tmp), "%s", argv[0]);
    printf("%s, %d, %d, %s\r\n", __FUNCTION__, __LINE__, argc, tmp);
    return 0;
}


int reg_wr64_main(int argc, char **argv)
{
    u64 reg_addr, reg_data;
    unsigned int reg_data1, reg_data2;
    int fd;
    long int ret;
    unsigned char buf[MAX_DATA_SIZE];

    ret = dram_arg_parse(argc, argv, &reg_addr, &reg_data, 3);
    if (ret < 0) {
        dram_help("reg_wr64");
        return -1;
    }

    if ((fd = open("/dev/dram_test", O_RDWR, S_IRWXU | S_IRWXG | S_IRWXO)) < 0) {
        fprintf(stderr, "Error: Could not open file "
                "/dev/dram: %s\n", strerror(errno));
        return -1;
    }

    if ((ret = lseek(fd, reg_addr, SEEK_SET)) < 0) {
        fprintf(stderr, "Error: Could not llseek :%s\n", strerror(errno));
        close(fd);
        return  -1;
    }
    reg_data2 = (unsigned int)(((u64)reg_data) >> 32) & 0xFFFFFFFF;
    reg_data1 = (unsigned int)reg_data & 0xFFFFFFFF;
    buf[0] = (reg_data1 >> 0) & 0xFF;
    buf[1] = (reg_data1 >> 8) & 0xFF;
    buf[2] = (reg_data1 >> 16) & 0xFF;
    buf[3] = (reg_data1 >> 24) & 0xFF;

    buf[4] = (reg_data2 >> 0) & 0xFF;
    buf[5] = (reg_data2 >> 8) & 0xFF;
    buf[6] = (reg_data2 >> 16) & 0xFF;
    buf[7] = (reg_data2 >> 24) & 0xFF;

    if ((ret = write(fd, buf, 8)) < 0) {
        fprintf(stderr, "Error: Could not write file : %s\n", strerror(errno));
        close(fd);
        return  -1;
    }

    close(fd);

    printf("Write quad-word 0x%16llX to address 0x%16llX.\n\n", reg_data, reg_addr);
    return 0;
}


int reg_rd64_main(int argc, char **argv)
{
    u64 reg_addr, reg_data;
    unsigned int reg_data1, reg_data2;
    int fd;
    long int ret;
    unsigned char buf[MAX_DATA_SIZE];

    ret = dram_arg_parse(argc, argv, &reg_addr, &reg_data, 2);
    if (ret < 0) {
        dram_help("reg_rd64");
        return -1;
    }

    if ((fd = open("/dev/dram_test", O_RDWR, S_IRWXU | S_IRWXG | S_IRWXO)) < 0) {
        fprintf(stderr, "Error: Could not open file "
                "/dev/dram: %s\n", strerror(errno));
        return -1;
    }

    if ((ret = lseek(fd, reg_addr, SEEK_SET)) < 0) {
        fprintf(stderr, "Error: Could not llseek : %s\n", strerror(errno));
        close(fd);
        return  -1;
    }

    if ((ret = read(fd, buf, 8)) < 0) {
        fprintf(stderr, "Error: Could not read file : %s\n", strerror(errno));
        close(fd);
        return  -1;
    }

    close(fd);
    reg_data1 = (buf[0] | (buf[1] << 8) | (buf[2] << 16) | (buf[3] << 24));
    reg_data2 = (buf[4] | (buf[5] << 8) | (buf[6] << 16) | (buf[7] << 24));

    printf("Read quad-word from address 0x%16llX: 0x%08X%08X\n\n", reg_addr, reg_data2, reg_data1);
    return 0;
}


int reg_wr32_main(int argc, char **argv)
{
    u64 reg_addr, reg_data;
    unsigned int reg_data1, reg_data2;
    int fd;
    long int ret;
    unsigned char buf[MAX_DATA_SIZE];

    ret = dram_arg_parse(argc, argv, &reg_addr, &reg_data, 3);
    if (ret < 0) {
        dram_help("reg_wr32");
        return -1;
    }

    if ((fd = open("/dev/dram_test", O_RDWR, S_IRWXU | S_IRWXG | S_IRWXO)) < 0) {
        fprintf(stderr, "Error: Could not open file "
                "/dev/dram: %s\n", strerror(errno));
        return -1;
    }

    if ((ret = lseek(fd, reg_addr, SEEK_SET)) < 0) {
        fprintf(stderr, "Error: Could not llseek :%s\n", strerror(errno));
        close(fd);
        return  -1;
    }
    reg_data2 = (unsigned int)(((u64)reg_data) >> 32) & 0xFFFFFFFF;
    reg_data1 = (unsigned int)reg_data & 0xFFFFFFFF;
    buf[0] = (reg_data1 >> 0) & 0xFF;
    buf[1] = (reg_data1 >> 8) & 0xFF;
    buf[2] = (reg_data1 >> 16) & 0xFF;
    buf[3] = (reg_data1 >> 24) & 0xFF;

    buf[4] = (reg_data2 >> 0) & 0xFF;
    buf[5] = (reg_data2 >> 8) & 0xFF;
    buf[6] = (reg_data2 >> 16) & 0xFF;
    buf[7] = (reg_data2 >> 24) & 0xFF;

    if ((ret = write(fd, buf, 4)) < 0) {
        fprintf(stderr, "Error: Could not write file : %s\n", strerror(errno));
        close(fd);
        return  -1;
    }

    close(fd);

    printf("Write word 0x%08X to address 0x%16llX.\n\n", reg_data1, reg_addr);
    return 0;
}


int reg_rd32_main(int argc, char **argv)
{
    u64 reg_addr, reg_data;
    unsigned int reg_data1;
    int fd;
    long int ret;
    unsigned char buf[MAX_DATA_SIZE];

    ret = dram_arg_parse(argc, argv, &reg_addr, &reg_data, 2);
    if (ret < 0) {
        dram_help("reg_rd32");
        return -1;
    }

    if ((fd = open("/dev/dram_test", O_RDWR, S_IRWXU | S_IRWXG | S_IRWXO)) < 0) {
        fprintf(stderr, "Error: Could not open file "
                "/dev/dram: %s\n", strerror(errno));
        return -1;
    }

    if ((ret = lseek(fd, reg_addr, SEEK_SET)) < 0) {
        fprintf(stderr, "Error: Could not llseek : %s\n", strerror(errno));
        close(fd);
        return  -1;
    }

    if ((ret = read(fd, buf, 4)) < 0) {
        fprintf(stderr, "Error: Could not read file : %s\n", strerror(errno));
        close(fd);
        return  -1;
    }

    close(fd);
    reg_data1 = (buf[0] | (buf[1] << 8) | (buf[2] << 16) | (buf[3] << 24));

    printf("Read word from address 0x%16llX: 0x%08X\n\n", reg_addr, reg_data1);
    return 0;
}


int reg_wr16_main(int argc, char **argv)
{
    u64 reg_addr, reg_data;
    unsigned int reg_data1, reg_data2;
    int fd;
    long int ret;
    unsigned char buf[MAX_DATA_SIZE];

    ret = dram_arg_parse(argc, argv, &reg_addr, &reg_data, 3);
    if (ret < 0) {
        dram_help("reg_wr16");
        return -1;
    }

    if ((fd = open("/dev/dram_test", O_RDWR, S_IRWXU | S_IRWXG | S_IRWXO)) < 0) {
        fprintf(stderr, "Error: Could not open file "
                "/dev/dram: %s\n", strerror(errno));
        return -1;
    }

    if ((ret = lseek(fd, reg_addr, SEEK_SET)) < 0) {
        fprintf(stderr, "Error: Could not llseek :%s\n", strerror(errno));
        close(fd);
        return  -1;
    }
    reg_data2 = (unsigned int)(((u64)reg_data) >> 32) & 0xFFFFFFFF;
    reg_data1 = (unsigned int)reg_data & 0xFFFFFFFF;
    buf[0] = (reg_data1 >> 0) & 0xFF;
    buf[1] = (reg_data1 >> 8) & 0xFF;
    buf[2] = (reg_data1 >> 16) & 0xFF;
    buf[3] = (reg_data1 >> 24) & 0xFF;

    buf[4] = (reg_data2 >> 0) & 0xFF;
    buf[5] = (reg_data2 >> 8) & 0xFF;
    buf[6] = (reg_data2 >> 16) & 0xFF;
    buf[7] = (reg_data2 >> 24) & 0xFF;

    if ((ret = write(fd, buf, 2)) < 0) {
        fprintf(stderr, "Error: Could not write file : %s\n", strerror(errno));
        close(fd);
        return  -1;
    }

    close(fd);

    printf("Write half-word 0x%02X%02X to address 0x%16llX.\n\n", buf[1], buf[0], reg_addr);
    return 0;
}

int reg_rd16_main(int argc, char **argv)
{
    u64 reg_addr, reg_data;
    int fd;
    long int ret;
    unsigned char buf[MAX_DATA_SIZE];

    ret = dram_arg_parse(argc, argv, &reg_addr, &reg_data, 2);
    if (ret < 0) {
        dram_help("reg_rd16");
        return -1;
    }

    if ((fd = open("/dev/dram_test", O_RDWR, S_IRWXU | S_IRWXG | S_IRWXO)) < 0) {
        fprintf(stderr, "Error: Could not open file "
                "/dev/dram: %s\n", strerror(errno));
        return -1;
    }

    if ((ret = lseek(fd, reg_addr, SEEK_SET)) < 0) {
        fprintf(stderr, "Error: Could not llseek : %s\n", strerror(errno));
        close(fd);
        return  -1;
    }

    if ((ret = read(fd, buf, 2)) < 0) {
        fprintf(stderr, "Error: Could not read file : %s\n", strerror(errno));
        close(fd);
        return  -1;
    }

    close(fd);

    printf("Read half-word from address 0x%16llX: 0x%02X%02X\n\n", reg_addr, buf[1], buf[0]);
    return 0;
}


int reg_wr8_main(int argc, char **argv)
{
    u64 reg_addr, reg_data;
    unsigned int reg_data1, reg_data2;
    int fd;
    long int ret;
    unsigned char buf[MAX_DATA_SIZE];

    ret = dram_arg_parse(argc, argv, &reg_addr, &reg_data, 3);
    if (ret < 0) {
        dram_help("reg_wr8");
        return -1;
    }

    if ((fd = open("/dev/dram_test", O_RDWR, S_IRWXU | S_IRWXG | S_IRWXO)) < 0) {
        fprintf(stderr, "Error: Could not open file "
                "/dev/dram: %s\n", strerror(errno));
        return -1;
    }

    if ((ret = lseek(fd, reg_addr, SEEK_SET)) < 0) {
        fprintf(stderr, "Error: Could not llseek :%s\n", strerror(errno));
        close(fd);
        return  -1;
    }
    reg_data2 = (unsigned int)(((u64)reg_data) >> 32) & 0xFFFFFFFF;
    reg_data1 = (unsigned int)reg_data & 0xFFFFFFFF;
    buf[0] = (reg_data1 >> 0) & 0xFF;
    buf[1] = (reg_data1 >> 8) & 0xFF;
    buf[2] = (reg_data1 >> 16) & 0xFF;
    buf[3] = (reg_data1 >> 24) & 0xFF;

    buf[4] = (reg_data2 >> 0) & 0xFF;
    buf[5] = (reg_data2 >> 8) & 0xFF;
    buf[6] = (reg_data2 >> 16) & 0xFF;
    buf[7] = (reg_data2 >> 24) & 0xFF;

    if ((ret = write(fd, buf, 1)) < 0) {
        fprintf(stderr, "Error: Could not write file : %s\n", strerror(errno));
        close(fd);
        return  -1;
    }

    close(fd);

    printf("Write byte 0x%02X to address 0x%16llX.\n\n", buf[0], reg_addr);
    return 0;
}


int reg_rd8_main(int argc, char **argv)
{
    u64 reg_addr, reg_data;
    int fd;
    long int ret;
    unsigned char buf[MAX_DATA_SIZE];

    ret = dram_arg_parse(argc, argv, &reg_addr, &reg_data, 2);
    if (ret < 0) {
        dram_help("reg_rd8");
        return -1;
    }

    if ((fd = open("/dev/dram_test", O_RDWR, S_IRWXU | S_IRWXG | S_IRWXO)) < 0) {
        fprintf(stderr, "Error: Could not open file "
                "/dev/dram: %s\n", strerror(errno));
        return -1;
    }

    if ((ret = lseek(fd, reg_addr, SEEK_SET)) < 0) {
        fprintf(stderr, "Error: Could not llseek : %s\n", strerror(errno));
        close(fd);
        return  -1;
    }

    if ((ret = read(fd, buf, 1)) < 0) {
        fprintf(stderr, "Error: Could not read file : %s\n", strerror(errno));
        close(fd);
        return  -1;
    }

    close(fd);

    printf("Read byte from address 0x%16llX: 0x%02X\n\n", reg_addr, buf[0]);
    return 0;
}


int mdio_rd_main(int argc, char **argv)
{
    struct mdio_user_info  mdio_info;
    int fd;
    long int ret;

    ret = mdio_arg_parse(argc, argv,
                         &mdio_info.c45,
                         &mdio_info.bus_id,
                         &mdio_info.phy_addr,
                         &mdio_info.device,
                         &mdio_info.location,
                         &mdio_info.value,
                         6);
    if (ret < 0) {
        mdio_help("mdio_rd");
        return -1;
    }

    if ((fd = open("/dev/dram_test", O_RDWR, S_IRWXU | S_IRWXG | S_IRWXO)) < 0) {
        fprintf(stderr, "Error: Could not open file "
                "/dev/dram: %s\n", strerror(errno));
        return -1;
    }



    if ((ret = ioctl(fd, MDIO_READ, &mdio_info)) < 0) {
        fprintf(stderr, "Error: mdio read error : %s\n", strerror(errno));
        close(fd);
        return  -1;
    }

    close(fd);

    printf("Read mdio from [bus:%d, phy:0x%x, device:0x%x, reg:0x%x]: 0x%08x\r\n",
           mdio_info.bus_id, mdio_info.phy_addr, mdio_info.device, mdio_info.location, mdio_info.value);

    return 0;
}


int mdio_wr_main(int argc, char **argv)
{
    struct mdio_user_info  mdio_info;
    int fd;
    long int ret;

    ret = mdio_arg_parse(argc, argv,
                         &mdio_info.c45,
                         &mdio_info.bus_id,
                         &mdio_info.phy_addr,
                         &mdio_info.device,
                         &mdio_info.location,
                         &mdio_info.value,
                         6);

    if (ret < 0) {
        mdio_help("mdio_wr");
        return -1;
    }

    if ((fd = open("/dev/dram_test", O_RDWR, S_IRWXU | S_IRWXG | S_IRWXO)) < 0) {
        fprintf(stderr, "Error: Could not open file "
                "/dev/dram: %s\n", strerror(errno));
        return -1;
    }



    if ((ret = ioctl(fd, MDIO_WRITE, &mdio_info)) < 0) {
        fprintf(stderr, "Error: mdio read error : %s\n", strerror(errno));
        close(fd);
        return  -1;
    }

    close(fd);

    printf("Write 0x%08X to address [bus:%d, phy:0x%x, device:0x%x, reg:0x%x].\n\n",
           mdio_info.value, mdio_info.bus_id, mdio_info.phy_addr, mdio_info.device, mdio_info.location);

    return 0;
}

#define LPC_CPLD_DEV_NAME           "/dev/lpc_cpld"

int lpc_cpld_wr8_main(int argc, char **argv)
{
    u64 reg_addr, reg_data;
    unsigned int reg_data1, reg_data2;
    int fd;
    long int ret;
    unsigned char buf[MAX_DATA_SIZE];

    ret = dram_arg_parse(argc, argv, &reg_addr, &reg_data, 3);
    if (ret < 0) {
        dram_help("reg_wr8");
        return -1;
    }

    if ((fd = open(LPC_CPLD_DEV_NAME, O_RDWR, S_IRWXU | S_IRWXG | S_IRWXO)) < 0) {
        fprintf(stderr, "Error: Could not open file "
                "/dev/dram: %s\n", strerror(errno));
        return -1;
    }

    if ((ret = lseek(fd, reg_addr, SEEK_SET)) < 0) {
        fprintf(stderr, "Error: Could not llseek :%s\n", strerror(errno));
        close(fd);
        return  -1;
    }
    reg_data2 = (unsigned int)(((u64)reg_data) >> 32) & 0xFFFFFFFF;
    reg_data1 = (unsigned int)reg_data & 0xFFFFFFFF;
    buf[0] = (reg_data1 >> 0) & 0xFF;
    buf[1] = (reg_data1 >> 8) & 0xFF;
    buf[2] = (reg_data1 >> 16) & 0xFF;
    buf[3] = (reg_data1 >> 24) & 0xFF;

    buf[4] = (reg_data2 >> 0) & 0xFF;
    buf[5] = (reg_data2 >> 8) & 0xFF;
    buf[6] = (reg_data2 >> 16) & 0xFF;
    buf[7] = (reg_data2 >> 24) & 0xFF;

    if ((ret = write(fd, buf, 1)) < 0) {
        fprintf(stderr, "Error: Could not write file : %s\n", strerror(errno));
        close(fd);
        return  -1;
    }

    close(fd);

    /*printf("Write byte 0x%02X to address 0x%16llX.\n\n", buf[0], reg_addr);*/
    return 0;
}

#define MAX_LPC_SIZE      256
int lpc_cpld_rd8_main(int argc, char **argv)
{
    u64 reg_addr, reg_data, size, i;
    int fd;
    long int ret;
    unsigned char buf[MAX_LPC_SIZE];

    ret = dram_arg_parse(argc, argv, &reg_addr, &reg_data, 2);
    if (ret < 0) {
        dram_help("reg_rd8");
        return -1;
    }

    if ((fd = open(LPC_CPLD_DEV_NAME, O_RDWR, S_IRWXU | S_IRWXG | S_IRWXO)) < 0) {
        fprintf(stderr, "Error: Could not open file "
                "/dev/dram: %s\n", strerror(errno));
        return -1;
    }

    if ((ret = lseek(fd, reg_addr, SEEK_SET)) < 0) {
        fprintf(stderr, "Error: Could not llseek : %s\n", strerror(errno));
        close(fd);
        return  -1;
    }

    size = (reg_data ? (reg_data) : (1));
    if (size > MAX_LPC_SIZE) {
        printf("size %llu exceed max %d.\n", size, MAX_LPC_SIZE);
        close(fd);
        return -1;
    }

    if ((ret = read(fd, buf, size)) < 0) {
        fprintf(stderr, "Error: Could not read file : %s\n", strerror(errno));
        close(fd);
        return  -1;
    }

    close(fd);

    /* dump data */
    for (i = 0; i < size; i++) {
        printf("%02X ", buf[i]);
        if ((i + 1) % 16 == 0) {
            printf("\r\n");
        }
    }

    printf("\r\n");

    return 0;
}
