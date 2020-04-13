#!/usr/bin/python
# -*- coding: UTF-8 -*-

from ruijiecommon import *

RUIJIE_CARDID      = 0x00004040
RUIJIE_PRODUCTNAME = "B6510-48VS8CQ"

fanlevel = {
    "tips"       : ["low", "mid", "high"],
    "level"      : [51, 150, 255],
    "low_speed"  : [500, 7500, 17000],
    "high_speed" : [11000, 22500, 28500]
}

fanloc = [
    {
        "name":
            "Fan1/Fna2/Fan3/Fan4",
        "location":
            "0-0032/fan_speed_set",
        "childfans": [{
            "name": "Fan1",
            "location": "2-0037/hwmon/hwmon4/fan1_input"
        }, {
            "name": "Fan2",
            "location": "2-0037/hwmon/hwmon4/fan2_input"
        }, {
            "name": "Fan3",
            "location": "2-0037/hwmon/hwmon4/fan3_input"
        }, {
            "name": "Fan4",
            "location": "2-0037/hwmon/hwmon4/fan4_input"
        }]
    },
]

# Fan control parameters
MONITOR_TEMP_MIN        = 38   # default temperature
MONITOR_K               = 11   # fan regulation coefficient
MONITOR_MAC_IN          = 35   # temperature difference between inlet value and critical value on MAC
MONITOR_DEFAULT_SPEED   = 0x60
MONITOR_MAX_SPEED       = 0xFF
MONITOR_MIN_SPEED       = 0x33
MONITOR_MAC_ERROR_SPEED = 0XBB # speed when error occurs
MONITOR_FAN_TOTAL_NUM   = 4    # there are 4 fans in total, 3 main and 1 redundancy
MONITOR_MAC_UP_TEMP     = 50   # upper limit of temperature difference between mac and inlet
MONITOR_MAC_LOWER_TEMP  = -50  # lower limit of temperature difference between mac and inlet
MONITOR_MAC_MAX_TEMP    = 100

"""
critical value of temperature difference between previous and current moments,
if the difference is bigger than this value the speed regulation would be started
"""
MONITOR_FALL_TEMP                    = 4
MONITOR_MAC_WARNING_THRESHOLD        = 100
MONITOR_OUTTEMP_WARNING_THRESHOLD    = 85
MONITOR_BOARDTEMP_WARNING_THRESHOLD  = 85
MONITOR_CPUTEMP_WARNING_THRESHOLD    = 85
MONITOR_INTEMP_WARNING_THRESHOLD     = 70

MONITOR_MAC_CRITICAL_THRESHOLD       = 105
MONITOR_OUTTEMP_CRITICAL_THRESHOLD   = 90
MONITOR_BOARDTEMP_CRITICAL_THRESHOLD = 90
MONITOR_CPUTEMP_CRITICAL_THRESHOLD   = 100
MONITOR_INTEMP_CRITICAL_THRESHOLD    = 80
MONITOR_CRITICAL_NUM                 = 3  # number of consecutive failures
MONITOR_SHAKE_TIME                   = 20 # interval of anti-jitter
MONITOR_INTERVAL                     = 60

MONITOR_SYS_LED = [{
    "bus": 2,
    "devno": 0x33,
    "addr": 0xb2,
    "yellow": 0x03,
    "red": 0x02,
    "green": 0x01
}, {
    "bus": 2,
    "devno": 0x37,
    "addr": 0xb2,
    "yellow": 0x03,
    "red": 0x02,
    "green": 0x01
}]

MONITOR_SYS_FAN_LED = [
    {
        "bus": 2,
        "devno": 0x33,
        "addr": 0xb4,
        "yellow": 0x06,
        "red": 0x02,
        "green": 0x04
    },
]
MONITOR_FANS_LED = [{
    "bus": 2,
    "devno": 0x32,
    "addr": 0x23,
    "green": 0x09,
    "red": 0x0a
}, {
    "bus": 2,
    "devno": 0x32,
    "addr": 0x24,
    "green": 0x09,
    "red": 0x0a
}, {
    "bus": 2,
    "devno": 0x32,
    "addr": 0x25,
    "green": 0x09,
    "red": 0x0a
}, {
    "bus": 2,
    "devno": 0x32,
    "addr": 0x26,
    "green": 0x09,
    "red": 0x0a
}]

CPLDVERSIONS = [
    {
        "bus": 2,
        "devno": 0x33,
        "name": "MAC CPLD-A"
    },
    {
        "bus": 2,
        "devno": 0x35,
        "name": "MAC CPLD-B"
    },
    {
        "bus": 2,
        "devno": 0x37,
        "name": "CONNECT CPLD-A"
    },
    {
        "bus": 0,
        "devno": 0x0d,
        "name": "CPU CPLD"
    },
]

MONITOR_SYS_PSU_LED = [
    {
        "bus": 2,
        "devno": 0x33,
        "addr": 0xb3,
        "yellow": 0x06,
        "red": 0x02,
        "green": 0x04
    },
]

MONITOR_FAN_STATUS = [
    {
        'status': 'green',
        'minOkNum': 4,
        'maxOkNum': 4
    },
    {
        'status': 'yellow',
        'minOkNum': 3,
        'maxOkNum': 3
    },
    {
        'status': 'red',
        'minOkNum': 0,
        'maxOkNum': 2
    },
]

MONITOR_PSU_STATUS = [
    {
        'status': 'green',
        'minOkNum': 2,
        'maxOkNum': 2
    },
    {
        'status': 'yellow',
        'minOkNum': 1,
        'maxOkNum': 1
    },
    {
        'status': 'red',
        'minOkNum': 0,
        'maxOkNum': 0
    },
]

# B6510 AVS parameters
MAC_AVS_PARAM = {
    0x72: 0x0384,
    0x73: 0x037e,
    0x74: 0x0378,
    0x75: 0x0372,
    0x76: 0x036b,
    0x77: 0x0365,
    0x78: 0x035f,
    0x79: 0x0359,
    0x7a: 0x0352,
    0x7b: 0x034c,
    0x7c: 0x0346,
    0x7d: 0x0340,
    0x7e: 0x0339,
    0x7f: 0x0333,
    0x80: 0x032d,
    0x81: 0x0327,
    0x82: 0x0320,
    0x83: 0x031a,
    0x84: 0x0314,
    0x85: 0x030e,
    0x86: 0x0307,
    0x87: 0x0301,
    0x88: 0x02fb,
    0x89: 0x02f5,
    0x8A: 0x02ee
}

# B6510 default configurations
MAC_DEFAULT_PARAM = {
    "type"        : 1,                 # type of fan speed regulation
    "default"     : 0x74,
    "loopaddr"    : 0x00,              # AVS loop address
    "loop"        : 0x00,              # AVS loop value
    "open"        : 0x00,              # disable write protection
    "close"       : 0x40,              # enable write protection
    "bus"         : 2,                 # AVS I2C bus address
    "devno"       : 0x60,
    "addr"        : 0x21,              # AVS address
    "protectaddr" : 0x10,              # AVS write protection address
    "sdkreg"      : "TOP_AVS_SEL_REG", # SDK register name
    "sdktype"     : 0,                 # type 0: disable shifting / 1: enable shifting
    "macregloc"   : 24,                # shifting option
    "mask"        : 0xff               # mask for shifting
}

DRIVERLISTS = [
    {
        "name": "i2c_dev",
        "delay": 0
    },
    {
        "name": "i2c_algo_bit",
        "delay": 0
    },
    {
        "name": "i2c_gpio",
        "delay": 0
    },
    {
        "name": "i2c_mux",
        "delay": 0
    },
    {
        "name": "i2c_mux_pca9641",
        "delay": 0
    },
    {
        "name": "i2c_mux_pca954x",
        "delay": 0
    },
    {
        "name": "lm75",
        "delay": 0
    },
    {
        "name": "optoe",
        "delay": 0
    },
    {
        "name": "at24",
        "delay": 0
    },
    {
        "name": "rg_sff",
        "delay": 0
    },
    {
        "name": "ruijie_platform",
        "delay": 0
    },
    {
        "name": "rg_cpld",
        "delay": 0
    },
    {
        "name": "rg_fan",
        "delay": 0
    },
    {
        "name": "rg_psu",
        "delay": 0
    },
    {
        "name": "csu550",
        "delay": 0
    },
    {
        "name": "rg_gpio_xeon",
        "delay": 0
    },
]

DEVICE = [
    {
        "name": "pca9641",
        "bus": 0,
        "loc": 0x10
    },
    {
        "name": "pca9548",
        "bus": 2,
        "loc": 0x70
    },
    {
        "name": "lm75",
        "bus": 2,
        "loc": 0x48
    },
    {
        "name": "lm75",
        "bus": 2,
        "loc": 0x49
    },
    {
        "name": "lm75",
        "bus": 2,
        "loc": 0x4a
    },
    {
        "name": "24c02",
        "bus": 2,
        "loc": 0x57
    },
    {
        "name": "rg_cpld",
        "bus": 0,
        "loc": 0x32
    },
    {
        "name": "rg_cpld",
        "bus": 1,
        "loc": 0x34
    },
    {
        "name": "rg_cpld",
        "bus": 1,
        "loc": 0x36
    },
    {
        "name": "rg_cpld",
        "bus": 2,
        "loc": 0x33
    },
    {
        "name": "rg_cpld",
        "bus": 2,
        "loc": 0x35
    },
    {
        "name": "rg_cpld",
        "bus": 2,
        "loc": 0x37
    },
    {
        "name": "rg_avs",
        "bus": 2,
        "loc": 0x60
    },
    {
        "name": "pca9548",
        "bus": 1,
        "loc": 0x70
    },
    {
        "name": "pca9548",
        "bus": 1,
        "loc": 0x71
    },
    {
        "name": "pca9548",
        "bus": 1,
        "loc": 0x72
    },
    {
        "name": "pca9548",
        "bus": 1,
        "loc": 0x73
    },
    {
        "name": "pca9548",
        "bus": 1,
        "loc": 0x74
    },
    {
        "name": "pca9548",
        "bus": 1,
        "loc": 0x75
    },
    {
        "name": "pca9548",
        "bus": 1,
        "loc": 0x76
    },
    {
        "name": "rg_fan",
        "bus": 3,
        "loc": 0x53
    },
    {
        "name": "rg_fan",
        "bus": 4,
        "loc": 0x53
    },
    {
        "name": "rg_fan",
        "bus": 5,
        "loc": 0x53
    },
    {
        "name": "rg_fan",
        "bus": 6,
        "loc": 0x53
    },
    {
        "name": "rg_psu",
        "bus": 7,
        "loc": 0x50
    },
    {
        "name": "dps550",
        "bus": 7,
        "loc": 0x58
    },
    {
        "name": "rg_psu",
        "bus": 8,
        "loc": 0x53
    },
    {
        "name": "dps550",
        "bus": 8,
        "loc": 0x5b
    },
]

INIT_PARAM = [
    {
        "loc": "1-0034/sfp_enable",
        "value": "01"
    },
    {
        "loc": "2-0035/sfp_enable2",
        "value": "ff"
    },
    {
        "loc": "2-0033/mac_led",
        "value": "ff"
    },
    {
        "loc": "1-0034/sfp_txdis1",
        "value": "00"
    },
    {
        "loc": "1-0034/sfp_txdis2",
        "value": "00"
    },
    {
        "loc": "1-0034/sfp_txdis3",
        "value": "00"
    },
    {
        "loc": "1-0036/sfp_txdis4",
        "value": "00"
    },
    {
        "loc": "1-0036/sfp_txdis5",
        "value": "00"
    },
    {
        "loc": "1-0036/sfp_txdis6",
        "value": "00"
    },
    {
        "loc": fanloc[0]["location"],
        "value": "80"
    },
    {
        "loc": "2-0033/sfp_led1_yellow",
        "value": "ad"
    },
    {
        "loc": "2-0035/sfp_led2_yellow",
        "value": "ad"
    },
]
