/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * Prototype for exporting FPGA I2C utilities
 */

#ifndef __BF_FPGA_I2C_UTIL_H__
#define __BF_FPGA_I2C_UTIL_H__

/*
 * Identifies an error code
 */
typedef int bf_pltfm_status_t;
typedef uint8_t bf_mux_addr_t;

enum bf_mux_addr_enum{
  WITH_MUX = 0x74,
  WITHOUT_MUX = 0xFF
};

#define FPGA_I2C_MAX_DATA 128 /* limited by buf size in bf_fpga_i2c_t */

#define BF_PLTFM_STATUS_VALUES                                         \
  BF_PLTFM_STATUS_(BF_PLTFM_SUCCESS, "Success"),                       \
      BF_PLTFM_STATUS_(BF_PLTFM_INVALID_ARG, "Invalid Arguments"),     \
      BF_PLTFM_STATUS_(BF_PLTFM_OBJECT_NOT_FOUND, "Object Not Found"), \
      BF_PLTFM_STATUS_(BF_PLTFM_COMM_FAILED,                           \
                       "Communication Failed with Hardware"),          \
      BF_PLTFM_STATUS_(BF_PLTFM_OBJECT_ALREADY_EXISTS,                 \
                       "Object Already Exists"),                       \
      BF_PLTFM_STATUS_(BF_PLTFM_OTHER, "Other")

enum bf_pltfm_status_enum {
#define BF_PLTFM_STATUS_(x, y) x
  BF_PLTFM_STATUS_VALUES,
  BF_PLTFM_STS_MAX
#undef BF_PLTFM_STATUS_
};

static const char *bf_pltfm_err_strings[BF_PLTFM_STS_MAX + 1] = {
#define BF_PLTFM_STATUS_(x, y) y
    BF_PLTFM_STATUS_VALUES, "Unknown error"
#undef BF_PLTFM_STATUS_
};

static inline const char *bf_pltfm_err_str(bf_pltfm_status_t sts) {
  if (BF_PLTFM_STS_MAX <= sts || 0 > sts) {
    return bf_pltfm_err_strings[BF_PLTFM_STS_MAX];
  } else {
    return bf_pltfm_err_strings[sts];
  }
}

bf_pltfm_status_t bf_fpga_i2c_read(uint8_t bus,
                                   bf_mux_addr_t mux_addr,
                                   uint8_t mux_chn,
                                   uint8_t i2c_addr,
                                   uint8_t *rd_buf,
                                   uint8_t rd_sz);

bf_pltfm_status_t bf_fpga_i2c_addr_read(int bus,
                                        bf_mux_addr_t mux_addr,
                                        uint8_t mux_chn,
                                        uint8_t addr,
                                        uint8_t *wr_buf,
                                        uint8_t wr_sz,
                                        uint8_t *rd_buf,
                                        uint8_t rd_sz);

bf_pltfm_status_t bf_fpga_i2c_write(int bus,
                                    bf_mux_addr_t mux_addr,
                                    uint8_t mux_chn,
                                    uint8_t i2c_addr,
                                    uint8_t *wr_buf,
                                    uint8_t wr_sz);

bf_pltfm_status_t bf_fpga_i2c_addr_write(int bus,
                                         uint8_t mux_addr,
                                         uint8_t mux_chn,
                                         uint8_t i2c_addr,
                                         uint8_t *reg_addr,
                                         uint8_t reg_sz,
                                         uint8_t *wr_buf,
                                         uint8_t wr_sz);

#endif //__BF_FPGA_I2C_UTIL_H__
