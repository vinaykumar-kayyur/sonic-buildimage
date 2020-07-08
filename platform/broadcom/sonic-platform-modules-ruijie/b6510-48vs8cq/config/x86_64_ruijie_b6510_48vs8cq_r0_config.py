#!/usr/bin/python
# -*- coding: UTF-8 -*-
from  ruijiecommon import *
PCA9548START  = -1
PCA9548BUSEND = -2


RUIJIE_CARDID      = 0x00004040
RUIJIE_PRODUCTNAME = "B6510-48VS8CQ"

STARTMODULE  = {
    "fancontrol":1,
    "avscontrol":1,
    "dev_monitor":1
}

i2ccheck_params = {"busend":"i2c-66","retrytime":6}

DEV_MONITOR_PARAM = {
    "polling_time": 10,
    "psus": [
        {
            "name": "psu1",
            "present": {
                "gettype": "i2c",
                "bus": 2,
                "loc": 0x37,
                "offset": 0x51,
                "presentbit": 0,
                "okval": 0,
            },
            "device": [
                {
                    "id": "psu1pmbus",
                    "name": "dps550",
                    "bus": 7,
                    "loc": 0x58,
                    "attr": "hwmon",
                },
            ],
        },
        {
            "name": "psu2",
            "present": {
                "gettype": "i2c",
                "bus": 2,
                "loc": 0x37,
                "offset": 0x51,
                "presentbit": 4,
                "okval": 0,
            },
            "device": [
                {
                    "id": "psu2pmbus",
                    "name": "dps550",
                    "bus": 8,
                    "loc": 0x5B,
                    "attr": "hwmon",
                },
            ],
        },
    ],
}

fanlevel = {
    "tips":["低","中","高"],
    "level":[51,150,255],
    "low_speed":[500,7500,17000],
    "high_speed":[11000,22500,28500]
}

fanloc =[ {"name":"风扇1/风扇2/风扇3/风扇4", "location":"0-0032/fan_speed_set" ,
          "childfans":[{"name":"风扇1", "location":"2-0037/hwmon/hwmon4/fan1_input"},
          {"name":"风扇2", "location":"2-0037/hwmon/hwmon4/fan2_input"},
          {"name":"风扇3", "location":"2-0037/hwmon/hwmon4/fan3_input"},
          {"name":"风扇4", "location":"2-0037/hwmon/hwmon4/fan4_input"} ]},
         ]


#################风扇调速参数##############################
MONITOR_TEMP_MIN           = 38    # 调速开始温度
MONITOR_K                  = 11    # 调速策略
MONITOR_MAC_IN             = 35    # mac与芯片的温差
MONITOR_DEFAULT_SPEED      = 0x60  # 默认转速
MONITOR_MAX_SPEED          = 0xFF  # 最大转速(全转)
MONITOR_MIN_SPEED          = 0x33  # 最小转速
MONITOR_MAC_ERROR_SPEED    = 0XBB  # MAC异常转速
MONITOR_FAN_TOTAL_NUM      = 4     # 3+1 冗余设计,有一个故障后报syslog
MONITOR_MAC_UP_TEMP        = 50    # MAC 与入温口比较 上
MONITOR_MAC_LOWER_TEMP     = -50   # MAC 与入入温口比较  下
MONITOR_MAC_MAX_TEMP       = 100   # 

MONITOR_FALL_TEMP = 4               # 调速下降温度
MONITOR_MAC_WARNING_THRESHOLD =  100 #100
MONITOR_OUTTEMP_WARNING_THRESHOLD = 85
MONITOR_BOARDTEMP_WARNING_THRESHOLD = 85
MONITOR_CPUTEMP_WARNING_THRESHOLD = 85
MONITOR_INTEMP_WARNING_THRESHOLD =  70  #70

MONITOR_MAC_CRITICAL_THRESHOLD = 105  #105
MONITOR_OUTTEMP_CRITICAL_THRESHOLD = 90 #90
MONITOR_BOARDTEMP_CRITICAL_THRESHOLD = 90 #90
MONITOR_CPUTEMP_CRITICAL_THRESHOLD = 100 #100
MONITOR_INTEMP_CRITICAL_THRESHOLD = 80  # 80 
MONITOR_CRITICAL_NUM              = 3 #重启次数
MONITOR_SHAKE_TIME                = 20 #防抖间隔
MONITOR_INTERVAL                   = 60

MONITOR_SYS_LED = [
          {"bus":2,"devno":0x33, "addr":0xb2, "yellow":0x03, "red":0x02,"green":0x01},
          {"bus":2,"devno":0x37, "addr":0xb2, "yellow":0x03, "red":0x02,"green":0x01}]

MONITOR_SYS_FAN_LED =[
          {"bus":2,"devno":0x33, "addr":0xb4, "yellow":0x06, "red":0x02,"green":0x04},
    ]
MONITOR_FANS_LED = [
          {"bus":2,"devno":0x32, "addr":0x23, "green":0x09, "red":0x0a},
          {"bus":2,"devno":0x32, "addr":0x24, "green":0x09, "red":0x0a},
          {"bus":2,"devno":0x32, "addr":0x25, "green":0x09, "red":0x0a},
          {"bus":2,"devno":0x32, "addr":0x26, "green":0x09, "red":0x0a}]


CPLDVERSIONS = [ 
        {"bus":2, "devno":0x33, "name":"MAC板CPLD-A"},
        {"bus":2, "devno":0x35, "name":"MAC板CPLD-B"},
        {"bus":2, "devno":0x37, "name":"CONNECT板CPLD-A"},
        {"bus":0, "devno":0x0d, "name":"CPU板CPLD"},
]

MONITOR_SYS_PSU_LED =[
          {"bus":2,"devno":0x33, "addr":0xb3, "yellow":0x06, "red":0x02,"green":0x04},
    ]
    
MONITOR_FAN_STATUS = [
    {'status':'green' , 'minOkNum':4,'maxOkNum':4},
    {'status':'yellow', 'minOkNum':3,'maxOkNum':3},
    {'status':'red'   , 'minOkNum':0,'maxOkNum':2},
    ]

MONITOR_PSU_STATUS = [
    {'status':'green' , 'minOkNum':2,'maxOkNum':2},
    {'status':'yellow', 'minOkNum':1,'maxOkNum':1},
    {'status':'red'   , 'minOkNum':0,'maxOkNum':0},
    ]


MONITOR_DEV_STATUS = {
    "temperature": [
        {"name":"lm75in",       "location":"/sys/bus/i2c/devices/2-0048/hwmon/*/temp1_input"},
        {"name":"lm75out",      "location":"/sys/bus/i2c/devices/2-0049/hwmon/*/temp1_input"},
        {"name":"lm75hot",      "location":"/sys/bus/i2c/devices/2-004a/hwmon/*/temp1_input"},
        {"name":"cpu",          "location":"/sys/class/hwmon/hwmon0"},
    ],
    "fans": [
        {
            "name":"fan1",
            "presentstatus":{"bus":2, "loc":0x37, "offset":0x30, 'bit':0},
            "rollstatus": [
                {"name":"motor1","bus":2, "loc":0x37, "offset":0x31, 'bit':0},
            ]
        },
        {
            "name":"fan2",
            "presentstatus":{"bus":2, "loc":0x37, "offset":0x30, 'bit':1},
            "rollstatus":[
                {"name":"motor1","bus":2, "loc":0x37, "offset":0x31, 'bit':1},
            ]
        },
        {
            "name":"fan3",
            "presentstatus":{"bus":2, "loc":0x37, "offset":0x30, 'bit':2},
            "rollstatus":[
                {"name":"motor1","bus":2, "loc":0x37, "offset":0x31, 'bit':2},
            ]
        },
        {
            "name":"fan4",
            "presentstatus":{"bus":2, "loc":0x37, "offset":0x30, 'bit':3},
            "rollstatus":[
                {"name":"motor1","bus":2, "loc":0x37, "offset":0x31, 'bit':3},
            ]
        },
    ],
     "psus": [
        {"name":"psu1", "bus":2, "loc":0x37, "offset":0x51, "gettype":"i2c", 'presentbit': 0, 'statusbit':1,'alertbit':2},
        {"name":"psu2", "bus":2, "loc":0x37, "offset":0x51, "gettype":"i2c", 'presentbit': 4, 'statusbit':5,'alertbit':6},
     ],
    "mac_temp" : {
        "flag" : {"bus":2, "loc":0x33, "offset":0xd4, "gettype":"i2c", 'okbit': 0, 'okval':1},
        "loc" : [
                "2-0035/mac_temp_input",
            ],
        "try_bcmcmd" : 0,
    },
}

MONITOR_DEV_STATUS_DECODE = {
    'fanpresent':  {0:'PRESENT', 1:'ABSENT', 'okval':0},
    'fanroll'   :  {0:'STALL'  , 1:'ROLL',   'okval':1},
    'psupresent':  {0:'PRESENT', 1:'ABSENT', 'okval':0},
    'psuoutput' :  {0:'FAULT'  , 1:'NORMAL', 'okval':1},
    'psualert'  :  {0:'FAULT'  , 1:'NORMAL', 'okval':1},
}
###################################################################


#####################MAC调压参数(B6510)####################################
MAC_AVS_PARAM ={
    0x72:0x0384,
    0x73:0x037e,
    0x74:0x0378,
    0x75:0x0372,
    0x76:0x036b,
    0x77:0x0365,
    0x78:0x035f,
    0x79:0x0359,
    0x7a:0x0352,
    0x7b:0x034c,
    0x7c:0x0346,
    0x7d:0x0340,
    0x7e:0x0339,
    0x7f:0x0333,
    0x80:0x032d,
    0x81:0x0327,
    0x82:0x0320,
    0x83:0x031a,
    0x84:0x0314,
    0x85:0x030e,
    0x86:0x0307,
    0x87:0x0301,
    0x88:0x02fb,
    0x89:0x02f5,
    0x8A:0x02ee
}
# 6510模板配置
MAC_DEFAULT_PARAM = {
  "type": 1,                       # type 1表示 不在范围内用默认 / 0表示不在范围内不调
  "default":0x74,                  # 配合type使用
  "loopaddr":0x00,                 # AVS loop地址
  "loop":0x00,                     # AVS loop值
  "open":0x00,                     # 关闭写保护值
  "close":0x40,                    # 打开写保护值
  "bus":2,                         # AVSI2C总线地址
  "devno":0x60,                    # AVS地址
  "addr":0x21,                     # AVS调压地址
  "protectaddr":0x10,              # AVS写保护地址
  "sdkreg":"TOP_AVS_SEL_REG",      # SDK寄存器名称
  "sdktype": 0,                    # type 0表示 不需要移位 / 1 表示需要移位
  "macregloc":24 ,                 # 移位操作
  "mask": 0xff                     # 移位后掩码
}
#####################MAC调压参数####################################

## 驱动列表
## 
DRIVERLISTS = [
        {"name":"i2c_dev", "delay":0},
        {"name":"i2c_algo_bit","delay":0},
        {"name":"i2c_gpio", "delay":0},
        {"name":"i2c_mux", "delay":0},
        {"name":"i2c_mux_pca9641", "delay":0},
        {"name":"i2c_mux_pca954x force_create_bus=1", "delay":0},# force_deselect_on_exit=1
        {"name":"lm75", "delay":0},
        {"name":"optoe", "delay":0},
        {"name":"at24", "delay":0},
        {"name":"rg_sff", "delay":0},
        {"name":"ruijie_b6510_platform", "delay":0},
        {"name":"ruijie_platform", "delay":0},
        {"name":"rg_avs", "delay":0},
        {"name":"rg_cpld", "delay":0},
        {"name":"rg_fan", "delay":0},
        {"name":"rg_psu", "delay":0},
        {"name":"pmbus_core", "delay":0},
        {"name":"csu550", "delay":0},
        {"name":"rg_gpio_xeon", "delay":0},
        {"name":"ipmi_msghandler", "delay":0},
        {"name":"ipmi_devintf", "delay":0},
        {"name":"ipmi_si", "delay":0},
        {"name":"firmware_driver", "delay":0},
        {"name":"firmware_bin", "delay":0},
        {"name":"ruijie_b6510_sfputil", "delay":0},
        {"name":"ruijie_common dfd_my_type=0x4040", "delay":0},
        {"name":"lpc_dbg", "delay":0},
]

DEVICE = [
        {"name":"pca9641","bus":0 ,"loc":0x10 },
        {"name":"pca9548","bus":2 ,"loc":0x70 },
        {"name":"lm75","bus": 2,   "loc":0x48 },
        {"name":"lm75","bus": 2,   "loc":0x49 },
        {"name":"lm75","bus": 2,   "loc":0x4a },
        {"name":"24c02","bus":2 , "loc":0x57 },
        {"name":"rg_cpld","bus":0 ,"loc":0x32 },
        {"name":"rg_cpld","bus":1 ,"loc":0x34 },
        {"name":"rg_cpld","bus":1 ,"loc":0x36 },
        {"name":"rg_cpld","bus":2 ,"loc":0x33 },
        {"name":"rg_cpld","bus":2 ,"loc":0x35 },
        {"name":"rg_cpld","bus":2 ,"loc":0x37 },
        {"name":"rg_avs","bus": 2 ,"loc":0x60 },
        {"name":"pca9548","bus":1,"loc":0x70 },
        {"name":"pca9548","bus":1,"loc":0x71 },
        {"name":"pca9548","bus":1,"loc":0x72 },
        {"name":"pca9548","bus":1,"loc":0x73 },
        {"name":"pca9548","bus":1,"loc":0x74 },
        {"name":"pca9548","bus":1,"loc":0x75 },
        {"name":"pca9548","bus":1,"loc":0x76 },
        {"name":"rg_fan","bus":3,"loc":0x53 },
        {"name":"rg_fan","bus":4,"loc":0x53 },
        {"name":"rg_fan","bus":5,"loc":0x53 },
        {"name":"rg_fan","bus":6,"loc":0x53 }, 
        {"name":"rg_psu","bus":7 ,"loc":0x50 },
        {"name":"dps550","bus":7 ,"loc":0x58 },
        {"name":"rg_psu","bus":8 ,"loc":0x53 },
        {"name":"dps550","bus":8 ,"loc":0x5b },
]

INIT_PARAM = [
            {"loc":"1-0034/sfp_enable","value": "01"},
            {"loc":"2-0035/sfp_enable2","value":"ff"},
            {"loc":"2-0033/mac_led", "value":"ff"},
            {"loc":"1-0034/sfp_txdis1","value":"00"},
            {"loc":"1-0034/sfp_txdis2","value":"00"},
            {"loc":"1-0034/sfp_txdis3","value":"00"},
            {"loc":"1-0036/sfp_txdis4","value":"00"},
            {"loc":"1-0036/sfp_txdis5","value":"00"},
            {"loc":"1-0036/sfp_txdis6","value":"00"},
            {"loc":fanloc[0]["location"], "value":"80"},
            {"loc":"2-0033/sfp_led1_yellow","value":"ad"},
            {"loc":"2-0035/sfp_led2_yellow","value":"ad"},
]
