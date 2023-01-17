cust_sfp_cfg = {
    'x86_64-ragile_ra-b6510-48v8c-r0': {
        "ver": '2.1',
        "port_index_start": 0,
        "port_num": 56,
        "log_level": 2,
        "eeprom_retry_times": 5,
        "eeprom_retry_break_sec": 0.2,
        "presence_path": "/sys/bus/i2c/devices/%d-0053/xcvr_present",
        "presence_path_key": list(range(32, 88)),
        "presence_val_is_present": 1,
        "eeprom_path": "/sys/bus/i2c/devices/%d-0050/eeprom",
        "eeprom_path_key": list(range(32, 88)),
        "optoe_driver_path": "/sys/bus/i2c/devices/%d-0050/dev_class",
        "optoe_driver_key": list(range(32, 88)),
        "txdisable_path": "/sys/bus/i2c/devices/%d-0053/xcvr_txdisable",
        "txdisable_path_key": list(range(32, 80)) + [0] * 8,
        "txdisable_val_is_on": 0,
        "reset_path": "/sys/bus/i2c/devices/%d-0053/xcvr_reset",
        "reset_path_key": [0]* 48 + list(range(80, 88)),
        "reset_val_is_on": 0,
    },
}
