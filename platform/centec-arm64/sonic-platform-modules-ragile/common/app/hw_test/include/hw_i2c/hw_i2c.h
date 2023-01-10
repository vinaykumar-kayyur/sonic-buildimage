/**
 * Copyright(C) 2010 Ragile Network. All rights reserved.
 */
/*
 * hw_i2c.h
 * Original Author : support@ragilenetworks.com, 2012-07-26
 *
 * i2c HardWare test definitions
 *
 * History
 *    v1.0    enbo liang(support@ragilenetworks.com)  2012-07-26  Initial version.
 */
#ifndef _HW_I2C_H
#define _HW_I2C_H

struct i2c_dev_priv {
    int i2cbus;
    int save_addr;
    int offset;
    int offset_len;
    unsigned char data;
    int data_len;
    int times;
    unsigned int check_test_errors;
    unsigned char *buffer;
};

#define I2C_MAX_NAME_SIZE          128

extern int i2c_wr_main(int argc, char **argv);
extern int i2c_rd_main(int argc, char **argv);
extern int i2c_chk_main(int argc, char **argv);
extern int i2c_reset_main(int argc, char **argv);
extern int pca9548_rd_main(int argc, char **argv);
extern int pca9548_wr_main(int argc, char **argv);
extern int rtc_rd_main(int argc, char **argv);
extern int rtc_wr_main(int argc, char **argv);

#endif /* _HW_I2C_H */

