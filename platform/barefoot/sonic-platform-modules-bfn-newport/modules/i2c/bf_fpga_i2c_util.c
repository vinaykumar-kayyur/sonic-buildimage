/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * Implementation for exporting FPGA I2C utilities
 */

#include <linux/types.h>
#include <linux/slab.h>
#include <bf_fpga_ioctl.h>
#include "bf_fpga_i2c.h"
#include "bf_fpga_i2c_util.h"

#define BF_FPGA_MAX_CNT 1

static void populate_i2c_inst_ctrl_fields(bf_fpga_i2c_t *i2c_op,
                                          int inst_id,
                                          bool preemt,
                                          bool en,
                                          unsigned char i2c_addr,
                                          unsigned char i2c_type,
                                          unsigned char delay,
                                          unsigned char wr_cnt,
                                          unsigned char rd_cnt) {
  i2c_op->i2c_inst[inst_id].preemt = preemt;
  i2c_op->i2c_inst[inst_id].en = en;
  i2c_op->i2c_inst[inst_id].i2c_addr = i2c_addr;
  i2c_op->i2c_inst[inst_id].i2c_type = i2c_type;
  i2c_op->i2c_inst[inst_id].delay = delay;
  i2c_op->i2c_inst[inst_id].wr_cnt = wr_cnt;
  i2c_op->i2c_inst[inst_id].rd_cnt = rd_cnt;
}


bf_pltfm_status_t _bf_fpga_i2c_write(int fd,
                                    int bus,
                                    uint8_t delay,
                                    uint8_t addr,
                                    uint8_t *wr_buf,
                                    uint8_t wr_sz) {
  bf_fpga_i2c_t i2c_op;
  int ret;

  if (fd >= BF_FPGA_MAX_CNT || !wr_sz || !wr_buf ||
      bus >= BF_I2C_FPGA_NUM_CTRL || wr_sz > BF_FPGA_MAX_I2C_WR_DATA) {
    return BF_PLTFM_INVALID_ARG; /* BF_PLTFM_COMM_FAILED */
  }
  i2c_op.one_time = 1;
  i2c_op.num_i2c = 1;
  i2c_op.inst_hndl.bus_id = bus;
  /* populate i2c operation */
  populate_i2c_inst_ctrl_fields(
      &i2c_op, 0, false, true, addr, BF_FPGA_I2C_WRITE, delay, wr_sz, 0);
  memcpy(i2c_op.i2c_inst[0].wr_buf, wr_buf, wr_sz);
  ret = fpga_i2c_oneshot(&i2c_op);
  if (ret) {
    ret = BF_PLTFM_COMM_FAILED; /* errorno has the actual system error code */
  }
  return ret;
}

bf_pltfm_status_t _bf_fpga_i2c_addr_write(int bus,
                                          uint8_t addr,
                                          uint8_t *reg_addr,
                                          uint8_t reg_sz,
                                          uint8_t *wr_buf,
                                          uint8_t wr_sz) {
  bf_fpga_i2c_t i2c_op;
  int ret;

  if (!reg_addr || !reg_sz || !wr_sz || !wr_buf ||
      bus >= BF_I2C_FPGA_NUM_CTRL || reg_sz + wr_sz > BF_FPGA_MAX_I2C_WR_DATA) {
    return BF_PLTFM_INVALID_ARG; /* BF_PLTFM_COMM_FAILED */
  }
  i2c_op.one_time = 1;
  i2c_op.num_i2c = 1;
  i2c_op.inst_hndl.bus_id = bus;
  /* populate i2c operation */
  populate_i2c_inst_ctrl_fields(
      &i2c_op, 0, false, true, addr, BF_FPGA_I2C_WRITE, 0, reg_sz + wr_sz, 0);
  memcpy(i2c_op.i2c_inst[0].wr_buf, reg_addr, reg_sz);
  memcpy(i2c_op.i2c_inst[0].wr_buf + reg_sz, wr_buf, wr_sz);
  ret = fpga_i2c_oneshot(&i2c_op);
  if (ret) {
    ret = BF_PLTFM_COMM_FAILED; /* errorno has the actual system error code */
  }
  return ret;
}

bf_pltfm_status_t _bf_fpga_i2c_addr_read(int fd,
                                        int bus,
                                        uint8_t delay,
                                        uint8_t addr,
                                        uint8_t *wr_buf,
                                        uint8_t *rd_buf,
                                        uint8_t wr_sz,
                                        uint8_t rd_sz) {
  bf_fpga_i2c_t i2c_op;
  int ret;

  if (fd >= BF_FPGA_MAX_CNT || !wr_sz || !rd_sz || !wr_buf || !rd_buf ||
      bus >= BF_I2C_FPGA_NUM_CTRL || rd_sz > BF_FPGA_MAX_I2C_RD_DATA) {
    return BF_PLTFM_INVALID_ARG; /* BF_PLTFM_COMM_FAILED */
  }
  i2c_op.one_time = 1;
  i2c_op.num_i2c = 1;
  i2c_op.inst_hndl.bus_id = bus;
  /* populate i2c operation */
  populate_i2c_inst_ctrl_fields(&i2c_op,
                                0,
                                false,
                                true,
                                addr,
                                BF_FPGA_I2C_ADDR_READ,
                                delay,
                                wr_sz,
                                rd_sz);
  memcpy(i2c_op.i2c_inst[0].wr_buf, wr_buf, wr_sz);
  ret = fpga_i2c_oneshot(&i2c_op);
  if (ret) {
    ret = BF_PLTFM_COMM_FAILED; /* errorno has the actual system error code */
  } else {
    memcpy(rd_buf, i2c_op.i2c_inst[0].rd_buf, rd_sz);
  }
  return ret;
}

bf_pltfm_status_t _bf_fpga_i2c_read(int fd,
                                   int bus,
                                   uint8_t delay,
                                   uint8_t addr,
                                   uint8_t *rd_buf,
                                   uint8_t rd_sz) {
  bf_fpga_i2c_t i2c_op;
  int ret;

  if (fd >= BF_FPGA_MAX_CNT || !rd_sz || !rd_buf ||
      bus >= BF_I2C_FPGA_NUM_CTRL || rd_sz > BF_FPGA_MAX_I2C_RD_DATA) {
    return BF_PLTFM_INVALID_ARG; /* BF_PLTFM_COMM_FAILED */
  }
  i2c_op.one_time = 1;
  i2c_op.num_i2c = 1;
  i2c_op.inst_hndl.bus_id = bus;
  /* populate i2c operation */
  populate_i2c_inst_ctrl_fields(
      &i2c_op, 0, false, true, addr, BF_FPGA_I2C_READ, delay, 0, rd_sz);
  memset(i2c_op.i2c_inst[0].rd_buf, 0, rd_sz);
  ret = fpga_i2c_oneshot(&i2c_op);
  if (ret) {
    ret = BF_PLTFM_COMM_FAILED; /* errorno has the actual system error code */
  } else {
    memcpy(rd_buf, i2c_op.i2c_inst[0].rd_buf, rd_sz);
  }
  return ret;
}

bf_pltfm_status_t _bf_fpga_i2c_write_mux(int fd,
                                        int bus,
                                        uint8_t delay,
                                        uint8_t mux_addr,
                                        uint8_t mux_chn,
                                        uint8_t i2c_addr,
                                        uint8_t *wr_buf,
                                        uint8_t wr_sz) {
  bf_fpga_i2c_t i2c_op;
  int ret;

  if (fd >= BF_FPGA_MAX_CNT || !wr_sz || !wr_buf ||
      bus >= BF_I2C_FPGA_NUM_CTRL || mux_addr > 0x7F ||
      wr_sz > BF_FPGA_MAX_I2C_WR_DATA) {
    return BF_PLTFM_INVALID_ARG;
  }
  i2c_op.one_time = 1;
  i2c_op.num_i2c = 3;
  i2c_op.inst_hndl.bus_id = bus;
  /* populate first operation -> set mux channel */
  populate_i2c_inst_ctrl_fields(
      &i2c_op, 0, true, true, mux_addr, BF_FPGA_I2C_WRITE, delay, 1, 0);
  i2c_op.i2c_inst[0].wr_buf[0] = mux_chn;

  /* populate second operation -> perform data transfer */
  populate_i2c_inst_ctrl_fields(
      &i2c_op, 1, true, true, i2c_addr, BF_FPGA_I2C_WRITE, 0, wr_sz, 0);
  memcpy(i2c_op.i2c_inst[1].wr_buf, wr_buf, wr_sz);

  /* populate third operation -> reset mux channel */
  populate_i2c_inst_ctrl_fields(
      &i2c_op, 2, false, true, mux_addr, BF_FPGA_I2C_WRITE, 0, 1, 0);
  i2c_op.i2c_inst[2].wr_buf[0] =
      0x00; /* disable all mux channels */

  ret = fpga_i2c_oneshot(&i2c_op);
  if (ret) {
    ret = BF_PLTFM_COMM_FAILED; /* errorno has the actual system error code */
  }
  return ret;
}

bf_pltfm_status_t _bf_fpga_i2c_addr_write_mux(int bus,
                                              uint8_t mux_addr,
                                              uint8_t mux_chn,
                                              uint8_t i2c_addr,
                                              uint8_t *reg_addr,
                                              uint8_t reg_sz,
                                              uint8_t *wr_buf,
                                              uint8_t wr_sz) {
  bf_fpga_i2c_t i2c_op;
  int ret;

  if (!reg_addr || !reg_sz || !wr_sz || !wr_buf ||
      bus >= BF_I2C_FPGA_NUM_CTRL || mux_addr > 0x7F ||
      reg_sz + wr_sz > BF_FPGA_MAX_I2C_WR_DATA ) {
    return BF_PLTFM_INVALID_ARG;
  }
  i2c_op.one_time = 1;
  i2c_op.num_i2c = 3;
  i2c_op.inst_hndl.bus_id = bus;
  /* populate first operation -> set mux channel */
  populate_i2c_inst_ctrl_fields(
      &i2c_op, 0, true, true, mux_addr, BF_FPGA_I2C_WRITE, 0, 1, 0);
  i2c_op.i2c_inst[0].wr_buf[0] = mux_chn;

  /* populate second operation -> perform data transfer */
  populate_i2c_inst_ctrl_fields(
      &i2c_op, 1, true, true, i2c_addr, BF_FPGA_I2C_WRITE, 0, reg_sz+wr_sz, 0);
  memcpy(i2c_op.i2c_inst[1].wr_buf, reg_addr, reg_sz);
  memcpy(i2c_op.i2c_inst[1].wr_buf + reg_sz, wr_buf, wr_sz);

  /* populate third operation -> reset mux channel */
  populate_i2c_inst_ctrl_fields(
      &i2c_op, 2, false, true, mux_addr, BF_FPGA_I2C_WRITE, 0, 1, 0);
  i2c_op.i2c_inst[2].wr_buf[0] =
      0x00; /* disable all mux channels */

  ret = fpga_i2c_oneshot(&i2c_op);
  if (ret) {
    ret = BF_PLTFM_COMM_FAILED; /* errorno has the actual system error code */
  }
  return ret;
}

bf_pltfm_status_t _bf_fpga_i2c_read_mux(int fd,
                                       int bus,
                                       uint8_t delay,
                                       uint8_t mux_addr,
                                       uint8_t mux_chn,
                                       uint8_t i2c_addr,
                                       uint8_t *rd_buf,
                                       uint8_t rd_sz) {
  bf_fpga_i2c_t i2c_op;
  int ret;

  if (fd >= BF_FPGA_MAX_CNT || !rd_buf || !rd_sz ||
      bus >= BF_I2C_FPGA_NUM_CTRL || mux_addr > 0x7F ||
      rd_sz > BF_FPGA_MAX_I2C_RD_DATA) {
    return BF_PLTFM_INVALID_ARG;
  }
  i2c_op.one_time = 1;
  i2c_op.num_i2c = 3;
  i2c_op.inst_hndl.bus_id = bus;
  /* populate first operation -> set mux channel */
  populate_i2c_inst_ctrl_fields(
      &i2c_op, 0, true, true, mux_addr, BF_FPGA_I2C_WRITE, delay, 1, 0);
  i2c_op.i2c_inst[0].wr_buf[0] = mux_chn;

  /* populate second operation -> perform data transfer */
  populate_i2c_inst_ctrl_fields(
      &i2c_op, 1, true, true, i2c_addr, BF_FPGA_I2C_READ, 0, 0, rd_sz);
  memset(i2c_op.i2c_inst[1].rd_buf, 0, rd_sz);

  /* populate third operation -> reset mux channel */
  populate_i2c_inst_ctrl_fields(
      &i2c_op, 2, false, true, mux_addr, BF_FPGA_I2C_WRITE, 0, 1, 0);
  i2c_op.i2c_inst[2].wr_buf[0] =
      0x00; /* disable all mux channels */

  ret = fpga_i2c_oneshot(&i2c_op);
  if (ret) {
    ret = BF_PLTFM_COMM_FAILED; /* errorno has the actual system error code */
  } else {
    memcpy(rd_buf, i2c_op.i2c_inst[1].rd_buf, rd_sz);
  }
  return ret;
}

bf_pltfm_status_t _bf_fpga_i2c_addr_read_mux(int fd,
                                            int bus,
                                            uint8_t delay,
                                            uint8_t mux_addr,
                                            uint8_t mux_chn,
                                            uint8_t i2c_addr,
                                            uint8_t *wr_buf,
                                            uint8_t *rd_buf,
                                            uint8_t wr_sz,
                                            uint8_t rd_sz) {
  bf_fpga_i2c_t i2c_op;
  int ret;

  if (fd >= BF_FPGA_MAX_CNT || !wr_sz || !rd_sz || !wr_buf || !rd_buf ||
      bus >= BF_I2C_FPGA_NUM_CTRL || mux_addr > 0x7F ||
      rd_sz > BF_FPGA_MAX_I2C_RD_DATA) {
    return BF_PLTFM_INVALID_ARG;
  }
  i2c_op.one_time = 1;
  i2c_op.num_i2c = 3;
  i2c_op.inst_hndl.bus_id = bus;
  /* populate first operation -> set mux channel */
  populate_i2c_inst_ctrl_fields(
      &i2c_op, 0, true, true, mux_addr, BF_FPGA_I2C_WRITE, delay, 1, 0);
  i2c_op.i2c_inst[0].wr_buf[0] = mux_chn;

  /* populate second operation -> perform data transfer */
  populate_i2c_inst_ctrl_fields(
      &i2c_op, 1, true, true, i2c_addr, BF_FPGA_I2C_ADDR_READ, 0, wr_sz, rd_sz);
  memcpy(i2c_op.i2c_inst[1].wr_buf, wr_buf, wr_sz);

  /* populate third operation -> reset mux channel */
  populate_i2c_inst_ctrl_fields(
      &i2c_op, 2, false, true, mux_addr, BF_FPGA_I2C_WRITE, 0, 1, 0);
  i2c_op.i2c_inst[2].wr_buf[0] =
      0x00; /* disable all mux channels */

  ret = fpga_i2c_oneshot(&i2c_op);
  if (ret) {
    ret = BF_PLTFM_COMM_FAILED; /* errorno has the actual system error code */
  } else {
    memcpy(rd_buf, i2c_op.i2c_inst[1].rd_buf, rd_sz);
  }
  return ret;
}

// void bf_fpga_reg_write32(int fd, uint32_t offset, uint32_t val) {
//   if (fd > BF_FPGA_MAX_CNT || offset > BF_FPGA_BAR_SIZE(0)) {
//     LOG_ERROR("invalid arguments\n");
//     return;
//   }
//   *(uint32_t *)(bf_fpga_fd[fd].base_addr + offset) = val;
// }

// int bf_fpga_reg_read32(int fd, uint32_t offset, uint32_t *val) {
//   if (fd > BF_FPGA_MAX_CNT || offset > BF_FPGA_BAR_SIZE(0)) {
//     LOG_ERROR("invalid arguments\n");
//     return -1;
//   }
//   *val = *(uint32_t *)(bf_fpga_fd[fd].base_addr + offset);
//   return 0;
// }

bf_pltfm_status_t bf_fpga_i2c_read(uint8_t bus,
                                   bf_mux_addr_t mux_addr,
                                   uint8_t mux_chn,
                                   uint8_t i2c_addr,
                                   uint8_t *rd_buf,
                                   uint8_t rd_sz) {
  if(mux_addr > 0x80)
    return _bf_fpga_i2c_read(0, bus, 0, i2c_addr, rd_buf, rd_sz);
  else
    return _bf_fpga_i2c_read_mux(0, bus, 0, mux_addr, mux_chn, i2c_addr, rd_buf,
                                 rd_sz);
}
EXPORT_SYMBOL(bf_fpga_i2c_read);

bf_pltfm_status_t bf_fpga_i2c_addr_read(int bus,
                                        bf_mux_addr_t mux_addr,
                                        uint8_t mux_chn,
                                        uint8_t i2c_addr,
                                        uint8_t *wr_buf,
                                        uint8_t wr_sz,
                                        uint8_t *rd_buf,
                                        uint8_t rd_sz)  {
  if(mux_addr > 0x80)
    return _bf_fpga_i2c_addr_read(0, bus, 0, i2c_addr, wr_buf, rd_buf, wr_sz,
                                  rd_sz);
  else
    return _bf_fpga_i2c_addr_read_mux(0, bus, 0, mux_addr, mux_chn, i2c_addr,
                                      wr_buf, rd_buf, wr_sz, rd_sz);
}
EXPORT_SYMBOL(bf_fpga_i2c_addr_read);

bf_pltfm_status_t bf_fpga_i2c_write(int bus,
                                    bf_mux_addr_t mux_addr,
                                    uint8_t mux_chn,
                                    uint8_t i2c_addr,
                                    uint8_t *wr_buf,
                                    uint8_t wr_sz) {
  if(mux_addr > 0x80)
    return _bf_fpga_i2c_write(0, bus, 0, i2c_addr, wr_buf, wr_sz);
  else
    return _bf_fpga_i2c_write_mux(0, bus, 0, mux_addr, mux_chn, i2c_addr,
                                  wr_buf, wr_sz);
}
EXPORT_SYMBOL(bf_fpga_i2c_write);

bf_pltfm_status_t bf_fpga_i2c_addr_write(int bus,
                                         uint8_t mux_addr,
                                         uint8_t mux_chn,
                                         uint8_t i2c_addr,
                                         uint8_t *reg_addr,
                                         uint8_t reg_sz,
                                         uint8_t *wr_buf,
                                         uint8_t wr_sz) {
  if(mux_addr > 0x80)
    return _bf_fpga_i2c_addr_write(bus, i2c_addr, reg_addr, reg_sz, wr_buf,
                                   wr_sz);
  else
    return _bf_fpga_i2c_addr_write_mux(bus, mux_addr, mux_chn, i2c_addr,
                                       reg_addr, reg_sz, wr_buf, wr_sz);
}
EXPORT_SYMBOL(bf_fpga_i2c_addr_write);
