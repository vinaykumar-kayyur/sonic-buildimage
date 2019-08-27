/*
 * Copyright 2019 Broadcom. All rights reserved.
 * The term “Broadcom” refers to Broadcom Inc. and/or its subsidiaries.
 *
 * Description
 *  PSU driver related api declarations
 */

#ifndef __PDDF_PSU_API_H__
#define __PDDF_PSU_API_H__

extern void get_psu_duplicate_sysfs(int idx, char *str);
extern ssize_t psu_show_default(struct device *dev, struct device_attribute *da, char *buf);
extern ssize_t psu_store_default(struct device *dev, struct device_attribute *da, const char *buf, size_t count);

extern int sonic_i2c_get_psu_present_default(void *client, PSU_DATA_ATTR *adata, void *data);
extern int sonic_i2c_get_psu_power_good_default(void *client, PSU_DATA_ATTR *adata, void *data);
extern int sonic_i2c_get_psu_model_name_default(void *client, PSU_DATA_ATTR *adata, void *data);
extern int sonic_i2c_get_psu_mfr_id_default(void *client, PSU_DATA_ATTR *adata, void *data);
extern int sonic_i2c_get_psu_serial_num_default(void *client, PSU_DATA_ATTR *adata, void *data);
extern int sonic_i2c_get_psu_fan_dir_default(void *client, PSU_DATA_ATTR *adata, void *data);
extern int sonic_i2c_get_psu_v_out_default(void *client, PSU_DATA_ATTR *adata, void *data);
extern int sonic_i2c_get_psu_i_out_default(void *client, PSU_DATA_ATTR *adata, void *data);
extern int sonic_i2c_get_psu_p_out_default(void *client, PSU_DATA_ATTR *adata, void *data);
extern int sonic_i2c_get_psu_fan1_speed_rpm_default(void *client, PSU_DATA_ATTR *adata, void *data);

#endif //__PDDF_PSU_API_H__
