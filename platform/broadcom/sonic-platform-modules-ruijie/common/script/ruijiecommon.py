#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""Load drivers and adapters"""

fancontrol_loc        = "/usr/local/bin"
fancontrol_config_loc = "/usr/local/bin"

DEVICE                = "DEVICE"
GLOBALCONFIG          = "GLOBALCONFIG"
DRIVERLISTS           = "DRIVERLISTS"
INIT_PARAM            = "INIT_PARAM"
RUIJIE_CARDID         = "RUIJIE_CARDID"
RUIJIE_PRODUCTNAME    = "RUIJIE_PRODUCTNAME"
E2_PROTECT            = "E2_PROTECT"
FAN_PROTECT           = "FAN_PROTECT"
MONITOR_CONST         = "MONITOR_CONST"

RUIJIE_PART_NUMBER    = "RJ000001"
RUIJIE_LABEL_REVISION = "R01"
RUIJIE_ONIE_VERSION   = "2018.02"
RUIJIE_MAC_SIZE       = 3
RUIJIE_MANUF_NAME     = "Ruijie"
RUIJIE_MANUF_COUNTRY  = "CHN"
RUIJIE_VENDOR_NAME    = "Ruijie"
RUIJIE_DIAG_VERSION   = "0.1.0.15"
RUIJIE_SERVICE_TAG    = "www.ruijie.com.cn"

DEV_LEDS              = {}
MEM_SLOTS             = []

LOCAL_LED_CONTROL     = {"CLOSE": {}, "OPEN": {}}
FIRMWARE_TOOLS        = {}

STARTMODULE           = {"fancontrol": 1, "avscontrol": 1}
i2ccheck_params       = {"busend": "i2c-66", "retrytime": 6}

# Fan ID map
FANS_DEF = {
    0x8100: "M6500-FAN-F",
    0x8101: "M6510-FAN-F",
    0x8102: "M6520-FAN-F",
    0x8103: "M6510-FAN-R"
}

# Fan Control Parameter
MONITOR_TEMP_MIN                     = 38
MONITOR_K                            = 11
MONITOR_MAC_IN                       = 35
MONITOR_DEFAULT_SPEED                = 0x60
MONITOR_MAX_SPEED                    = 0xFF
MONITOR_MIN_SPEED                    = 0x33
MONITOR_MAC_ERROR_SPEED              = 0XBB
MONITOR_FAN_TOTAL_NUM                = 4
MONITOR_MAC_UP_TEMP                  = 50
MONITOR_MAC_LOWER_TEMP               = -50
MONITOR_MAC_MAX_TEMP                 = 100

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
MONITOR_CRITICAL_NUM                 = 3
MONITOR_SHAKE_TIME                   = 20
MONITOR_INTERVAL                     = 60

# MAC Voltage Para
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

MAC_DEFAULT_PARAM = {
    "type": 1,
    "default": 0x74,
    "loopaddr": 0x00,
    "loop": 0x00,
    "open": 0x00,
    "close": 0x40,
    "bus": 2,
    "devno": 0x60,
    "addr": 0x21,
    "protectaddr": 0x10,
    "sdkreg": "DMU_PCU_OTP_CONFIG_8",
    "sdktype": 1,
    "macregloc": 24,
    "mask": 0xff
}

MONITOR_SYS_LED = [{
    "bus": 2,
    "devno": 0x33,
    "addr": 0xb2,
    "yellow": 0x06,
    "red": 0x02,
    "green": 0x04
}, {
    "bus": 2,
    "devno": 0x32,
    "addr": 0x72,
    "yellow": 0x06,
    "red": 0x02,
    "green": 0x04
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

fanloc = {"name": "fanset", "location": "0-0032/fan_speed_set"}

"""
Product Adapter Area
for RUIJIE_COMMON platform
"""
PCA9548START = 11
PCA9548BUSEND = 74

RUIJIE_CARDID = 0x00004040
RUIJIE_PRODUCTNAME = "ruijie_b6510"

FAN_PROTECT = {
    "bus": 0,
    "devno": 0x32,
    "addr": 0x19,
    "open": 0x00,
    "close": 0x0f
}
rg_eeprom = "2-0057/eeprom"
E2_LOC = {"bus": 2, "devno": 0x57}
E2_PROTECT = {"bus": 2, "devno": 0x33, "addr": 0xb0, "open": 0, "close": 1}

INIT_PARAM = [{
    "loc": "1-0034/sfp_enable",
    "value": "01"
}, {
    "loc": "2-0035/sfp_enable2",
    "value": "ff"
}, {
    "loc": "2-0033/mac_led",
    "value": "ff"
}, {
    "loc": "1-0034/sfp_txdis1",
    "value": "00"
}, {
    "loc": "1-0034/sfp_txdis2",
    "value": "00"
}, {
    "loc": "1-0034/sfp_txdis3",
    "value": "00"
}, {
    "loc": "1-0036/sfp_txdis4",
    "value": "00"
}, {
    "loc": "1-0036/sfp_txdis5",
    "value": "00"
}, {
    "loc": "1-0036/sfp_txdis6",
    "value": "00"
}, {
    "loc": fanloc["location"],
    "value": "80"
}]

INIT_COMMAND = []

CPLDVERSIONS = [{
    "loc": "2-0033/cpld_version",
    "des": "MAC CPLDA"
}, {
    "loc": "2-0035/cpld_version",
    "des": "MAC CPLDB"
}, {
    "loc": "2-0037/cpld_version",
    "des": "CPU cpld"
}]

DRIVERLISTS = [
    "i2c_dev",
    "i2c_algo_bit",
    "i2c_gpio",
    "i2c_mux",
    "i2c_mux_pca9641",
    "i2c_mux_pca954x",
    "eeprom",
    "at24",
    "rg_sff",
    "ruijie_platform",
    "rg_avs",
    "rg_cpld",
    "rg_fan",
    "rg_psu",
    "csu550",
    "rg_gpio_xeon",
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
        "name": "pca9548",
        "bus": 1,
        "loc": 0x77
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
        "name": "rg_psu",
        "bus": 7,
        "loc": 0x50
    },
    {
        "name": "csu550",
        "bus": 7,
        "loc": 0x58
    },
    {
        "name": "rg_psu",
        "bus": 8,
        "loc": 0x53
    },
    {
        "name": "csu550",
        "bus": 8,
        "loc": 0x5b
    },
]

# FRU info adapter
E2TYPE = {
    "1": "tlveeprom",
    "2": "x86cpueeprom",
    "3": "bmceeprom",
    "4": "cpueeprom",
    "5": "maceeprom",
    "6": "sloteeprom",
    "7": "fanconnecteeprom",
    "8": "M1HFANI-F",
    "9": "M1HFANI-R",
    "A": "M2HFANI-F",
    "B": "M2HFANI-R",
    "C": "psu"
}
FRULISTS = []
