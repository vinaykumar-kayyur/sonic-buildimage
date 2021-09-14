/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * device attributes handler prototypes for bf fpga switch interface
 */

#ifndef __BF_FPGA_SWI_API_H__
#define __BF_FPGA_SWI_API_H__

ssize_t devnum_show(struct device *dev, struct device_attribute *da,
                            char *buf);
ssize_t fpga_alias_show(struct device *dev, struct device_attribute *da,
                            char *buf);
ssize_t fpga_type_show(struct device *dev, struct device_attribute *da,
                            char *buf);
ssize_t fpga_ver_show(struct device *dev, struct device_attribute *da,
                            char *buf);
ssize_t reset_reg_show(struct device *dev, struct device_attribute *da,
                            char *buf);
ssize_t reset_reg_store(struct device *dev, struct device_attribute *da,
                            const char *buf, size_t count);

#endif //__BF_FPGA_SWI_API_H__
