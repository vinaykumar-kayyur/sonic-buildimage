/*
 * Copyright 2019 Broadcom. All rights reserved.
 * The term “Broadcom” refers to Broadcom Inc. and/or its subsidiaries.
 *
 * Description
 *  FAN driver api declarations
 */

#ifndef __PDDF_FAN_API_H__
#define __PDDF_FAN_API_H__

extern int pddf_fan_post_probe_default(struct i2c_client *client, const struct i2c_device_id *dev_id);

extern void get_fan_duplicate_sysfs(int idx, char *str);
extern ssize_t fan_show_default(struct device *dev, struct device_attribute *da, char *buf);
extern ssize_t fan_store_default(struct device *dev, struct device_attribute *da, const char *buf, size_t count);


extern int sonic_i2c_get_fan_present_default(void *client, FAN_DATA_ATTR *adata, void *data);
extern int sonic_i2c_get_fan_rpm_default(void *client, FAN_DATA_ATTR *adata, void *data);
extern int sonic_i2c_get_fan_direction_default(void *client, FAN_DATA_ATTR *adata, void *data);
extern int sonic_i2c_get_fan_pwm_default(void *client, FAN_DATA_ATTR *adata, void *data);
extern int sonic_i2c_get_fan_fault_default(void *client, FAN_DATA_ATTR *adata, void *data);
extern int sonic_i2c_set_fan_pwm_default(void *client, FAN_DATA_ATTR *adata, void *data);

#endif //__PDDF_FAN_API_H__
