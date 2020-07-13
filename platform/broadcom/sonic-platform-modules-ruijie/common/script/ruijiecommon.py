#!/usr/bin/python
# -*- coding: UTF-8 -*-
#-------------------------------------------------------------------------------
# Name:        锐捷 python通用模块 
# Purpose:      供其他模块调用
#
# Author:      tjm
#
# Created:     02/07/2018
# Copyright:   (c) tjm 2018
#-------------------------------------------------------------------------------

################################驱动加载适配#######################################################
#   需导出接口
###################################################################################################

fancontrol_loc        = "/usr/local/bin" 
fancontrol_config_loc = "/usr/local/bin" 

GLOBALCONFIG       = "GLOBALCONFIG"
MONITOR_CONST      = "MONITOR_CONST"

RUIJIE_PART_NUMBER    = "RJ000001"
RUIJIE_LABEL_REVISION = "R01"
RUIJIE_ONIE_VERSION   = "2018.02"
RUIJIE_MAC_SIZE       = 3
RUIJIE_MANUF_NAME     = "Ruijie"
RUIJIE_MANUF_COUNTRY  = "CHN"
RUIJIE_VENDOR_NAME    = "Ruijie"
RUIJIE_DIAG_VERSION   = "0.1.0.15"
RUIJIE_SERVICE_TAG    = "www.ruijie.com.cn"

DEV_LEDS = {}
MEM_SLOTS = []

LOCAL_LED_CONTROL = {
    "CLOSE":{},
    "OPEN":{}
}

FIRMWARE_TOOLS = {}
#启机模块
STARTMODULE  = {
                "fancontrol":1,
                "avscontrol":1
                    }

i2ccheck_params = {"busend":"i2c-66","retrytime":6}

###################################################################################################
#####          风扇板卡ID参照表
###################################################################################################
FANS_DEF = {
    0x8100:"M6500-FAN-F",
    0x8101:"M6510-FAN-F",
    0x8102:"M6520-FAN-F",
    0x8103:"M6510-FAN-R"
}

factest_module = {
    "sysinfo_showfanmsg":1,
    "sysinfo_showPsumsg":1,
    "sysinfo_showrestfanmsg":0,
    "sysinfo_showrestpsumsg":0
}

#################风扇调速参数##############################
MONITOR_TEMP_MIN           = 38    # 调速开始温度
MONITOR_K                  = 11    # 调速策略
MONITOR_MAC_IN             = 35    # mac与芯片的温差(备用)
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

MONITOR_MAC_SOURCE_SYSFS = 0 #1从sysfs拿mac温度,0从bcmcmd拿mac温度
MONITOR_MAC_SOURCE_PATH = None #sysfs路径

###################################################################


#####################MAC调压参数(B6510)####################################
MAC_AVS_PARAM ={
    0x72:0x0384 ,
    0x73:0x037e ,
    0x74:0x0378 ,
    0x75:0x0372 ,
    0x76:0x036b ,
    0x77:0x0365 ,
    0x78:0x035f ,
    0x79:0x0359 ,
    0x7a:0x0352 ,
    0x7b:0x034c ,
    0x7c:0x0346 ,
    0x7d:0x0340 ,
    0x7e:0x0339 ,
    0x7f:0x0333 ,
    0x80:0x032d ,
    0x81:0x0327 ,
    0x82:0x0320 ,
    0x83:0x031a ,
    0x84:0x0314 ,
    0x85:0x030e ,
    0x86:0x0307 ,
    0x87:0x0301 ,
    0x88:0x02fb ,
    0x89:0x02f5 ,
    0x8A:0x02ee 
}

# 默认6520模板配置
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
  "sdkreg":"DMU_PCU_OTP_CONFIG_8", # SDK寄存器名称
  "sdktype": 1,                    # type 0表示 不需要移位 / 1 表示需要移位
  "macregloc":24 ,                 # 移位操作
  "mask": 0xff                     # 移位后掩码
}

MONITOR_SYS_LED = [
        {"bus":2,"devno":0x33, "addr":0xb2, "yellow":0x06, "red":0x02,"green":0x04},
        {"bus":2,"devno":0x32, "addr":0x72, "yellow":0x06, "red":0x02,"green":0x04}]

MONITOR_SYS_FAN_LED =[
          {"bus":2,"devno":0x33, "addr":0xb4, "yellow":0x06, "red":0x02,"green":0x04},
    ]

MONITOR_FANS_LED = [
          {"bus":2,"devno":0x32, "addr":0x23, "green":0x09, "red":0x0a},
          {"bus":2,"devno":0x32, "addr":0x24, "green":0x09, "red":0x0a},
          {"bus":2,"devno":0x32, "addr":0x25, "green":0x09, "red":0x0a},
          {"bus":2,"devno":0x32, "addr":0x26, "green":0x09, "red":0x0a}]


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

MONITOR_DEV_STATUS = {}
MONITOR_DEV_STATUS_DECODE = {}
DEV_MONITOR_PARAM = {}
SLOT_MONITOR_PARAM = {}


fanloc = {"name":"fanset","location":"0-0032/fan_speed_set"}
#####################MAC调压参数####################################


####================================适配区================================
#### RUIJIE_COMMON 通用配置头 
#### “platform”    个性配置头 
####
PCA9548START  = 11
PCA9548BUSEND = 74

RUIJIE_CARDID      = 0x00004040
RUIJIE_PRODUCTNAME = "ruijie_b6510"

FAN_PROTECT = {"bus":0, "devno":0x32, "addr":0x19, "open":0x00, "close":0x0f}
rg_eeprom  = "2-0057/eeprom"
E2_LOC = {"bus":2, "devno":0x57}
E2_PROTECT ={"bus":2, "devno":0x33, "addr":0xb0, "open":0, "close":1}
MAC_LED_RESET = {"pcibus":8, "slot":0, "fn":0, "bar":0, "offset":64, "reset":0x98}

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
            {"loc":fanloc["location"], "value":"80"}
]

INIT_COMMAND = [
]

CPLDVERSIONS = [
        {"loc":"2-0033/cpld_version","des":"MAC板上CPLDA"},
        {"loc":"2-0035/cpld_version","des":"MAC板上CPLDB"},
        {"loc":"2-0037/cpld_version","des":"CPU板上cpld"}
]

## 驱动列表
## 
DRIVERLISTS = [
        "i2c_dev",
        "i2c_algo_bit",
        "i2c_gpio",
        "i2c_mux",
        "i2c_mux_pca9641",
        "i2c_mux_pca954x",  #  force_deselect_on_exit=1
        "eeprom",
        "at24",
		"rg_sff",
        "ruijie_b6510_platform",
        "ruijie_platform",
        "rg_avs",
        "rg_cpld",
        "rg_fan",
        "rg_psu",
        "csu550",
        "rg_gpio_xeon",
        #IPMIdriver
        "ipmi_msghandler",
        "ipmi_devintf",
        "ipmi_si",
]

DEVICE = [
        {"name":"pca9641","bus":0 ,"loc":0x10 },
        {"name":"pca9548","bus":2 ,"loc":0x70 },
        {"name":"lm75","bus": 2,   "loc":0x48 },
        {"name":"lm75","bus": 2,   "loc":0x49 },
        {"name":"lm75","bus": 2,   "loc":0x4a },
        {"name":"24c02","bus":2 , "loc":0x57 },
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
        {"name":"pca9548","bus":1,"loc":0x77 },
        {"name":"rg_fan","bus":3,"loc":0x53 },
        {"name":"rg_fan","bus":4,"loc":0x53 },
        {"name":"rg_fan","bus":5,"loc":0x53 },
        #{"name":"rg_fan","bus":6,"loc":0x53 }, #风扇单独处理
        {"name":"rg_psu","bus":7 ,"loc":0x50 },
        {"name":"csu550","bus":7 ,"loc":0x58 },
        {"name":"rg_psu","bus":8 ,"loc":0x53 },
        {"name":"csu550","bus":8 ,"loc":0x5b },
]

#####################FRU信息适配#################################
E2TYPE = {"1": "tlveeprom",
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
          "C": "psu"}
FRULISTS = []
################################生测适配区#######################################################
#   需导出接口
fanlevel_6510 = {
     "level":[51,150,255],
     "low_speed":[500,7500,17000],
     "high_speed":[11000,22500,28500]
}

fanlevel_6520 = {
     "level":[75,150,255],
     "low_speed":[750,4250,6750],
     "high_speed":[4500,7500,10000]
}

fanlevel = fanlevel_6520

TEMPIDCHANGE = {
  "lm75in":"入风口",
  "lm75out":"出风口",
  "lm75hot":"最热点",
  "入风口":"lm75in",
  "出风口":"lm75out",
  "最热点":"lm75hot",
}

#   生测模块
FACTESTMODULE  = { }

##################################生测菜单项
item1 = {"name":"单项测试", "deal" :"test_signal", "childid":1}
test_sys_reload_item = {"name":"整机复位", "deal" :"test_sys_reload"}

test_sys_item           = { "name":"产品信息检测", "deal" :"test_sysinfo"}
test_temp_item          = { "name":"温度检测", "deal" :"test_tempinfo"}
test_mem_item           = { "name":"内存测试", "deal" :"test_cpumemoryinfo"}
test_hd_item            = { "name":"硬盘测试", "deal" :"test_hard"}
test_rtc_item           = { "name":"RTC测试 ", "deal" :"test_rtc"}
test_i2c_item           = { "name":"I2c测试 ", "deal" :"test_i2c"}
test_cpld_item          = { "name":"CPLD测试", "deal" :"test_cpld"}
test_portframe_item     = { "name":"端口收发帧测试", "deal" :"test_portframe"}
test_sysled_item        = { "name":"指示灯测试", "deal" :"test_led"}
test_fan_item           = { "name":"风扇状态检测", "deal" :"test_fan"}
test_power_item         = { "name":"电源状态检测", "deal" :"test_power"}
test_usb_item           = { "name":"USB测试", "deal" :"test_usb"}
test_prbs_item          = { "name":"PRBS测试", "deal" :"test_prbs"}
test_portbroadcast_item = { "name":"端口广播", "deal" :"test_portbroadcast"}

test_debug_level       = {"name":"调试更改", "deal" :"test_setdebug"}
test_log_level         = {"name":"日志输出等级", "deal" :"test_loginfolevel"}
test_setmac            = {"name":"setmac", "deal" :"test_setmac"}
test_setrtc            = {"name":"设置RTC", "deal" :"test_set_rtc"}

log_level_critical    = {"name":"CRITICAL", "deal" :"test_log_critical"}
log_level_debug       = {"name":"DEBUG", "deal" :"test_log_debug"}
log_level_error       = {"name":"ERROR", "deal" :"test_log_error"}
log_level_info        = {"name":"INFO", "deal" :"test_log_info"}
log_level_notset      = {"name":"NOTSET", "deal" :"test_log_notset"}
log_level_warning     = {"name":"WARNING", "deal" :"test_log_warning"}


test_e2_setmac_item   = {"name":"E2SETMAC", "deal" :"test_e2_setmac"}
test_bmc_setmac_item  = {"name":"BMCSETMAC", "deal" :"test_bmc_setmac"}
test_fan_setmac_item  = {"name":"风扇SETMAC", "deal" :"test_fan_setmac"}

alltest = [
        test_sys_item,
        test_temp_item,
        test_mem_item,
        test_hd_item,
        test_rtc_item,
        test_i2c_item,
        test_cpld_item,
        test_portframe_item,
        test_sysled_item,
        test_fan_item,
        test_power_item,
        test_usb_item,
        test_prbs_item,
        test_portbroadcast_item
        ]
        
looptest = [
        test_sys_item,
        test_temp_item,
        test_mem_item,
        test_hd_item,
        test_rtc_item,
        test_i2c_item,
        test_cpld_item,
        test_portframe_item,
        test_fan_item, 
        test_power_item,
        test_usb_item,
        test_prbs_item,
        test_portbroadcast_item , 
]

diagtestall = [
]

menuList =[
        {
        "menuid":0, "value":[
            {"name":"单项测试", "deal" :"test_signal", "childid":1},
            {"name":"所有测试", "deal" :"test_all"},
            {"name":"自动循环测试", "deal" :"test_loop"},
            #{"name":"拷机结果查看", "deal" :"test_loop_read"},
            #{"name":"拷机结果删除", "deal" :"test_loop_delete"},
#           {"name":"配置加载", "deal" :"test_config"},
            test_sys_reload_item,
            {"name":"系统配置", "deal" :"test_sysconfig","childid":2},
        ]
        },
        {
            "menuid":1, "parentid":0, "value":[
                        test_sys_item            ,
                        test_temp_item           ,
                        test_mem_item            ,
                        test_hd_item             ,
                        test_rtc_item            ,
                        test_i2c_item            ,
                        test_cpld_item           ,
                        test_portframe_item      ,
                        test_sysled_item         ,
                        test_fan_item            ,
                        test_power_item          ,
                        test_usb_item            ,
                        test_prbs_item           ,
                        test_portbroadcast_item  ,
            ]},
        {
                "menuid":2, "parentid":0, "value":[
                test_debug_level,
                test_log_level ,
                test_setmac ,
                test_setrtc ,
        ]},
        {
        "menuid":3, "parentid":2, "value":[
                    log_level_critical , 
                    log_level_debug    ,
                    log_level_error    ,
                    log_level_info     ,
                    log_level_notset   ,
                    log_level_warning  ,
        ]},
        {
        "menuid":4, "parentid":2, "value":[
            test_e2_setmac_item ,
            test_bmc_setmac_item,
            test_fan_setmac_item,
        ]},
]


TESTCASE={
    "CPLD":[
        {"name":"CONNECT板CPLD-A" ,"cases":[
              {"name":"cpld32",      "cmd":"grtd_test.py  cpld_check 0 0x32 0xAA"},
              {"name":"cpld37",      "cmd":"grtd_test.py  cpld_check 2 0x37 0xAC"},
            ]
        },
        {"name":"MAC板CPLD-A" ,"cases":[
              {"name":"cpld33",      "cmd":"grtd_test.py  cpld_check 2 0x33 0xAB"},
              {"name":"cpld34",      "cmd":"grtd_test.py  cpld_check 1 0x34 0xAA"},
            ]
        },
        {"name":"MAC板CPLD-B" ,"cases":[
              {"name":"cpld36",      "cmd":"grtd_test.py  cpld_check 1 0x36 0xAA"},
              {"name":"cpld35",      "cmd":"grtd_test.py  cpld_check 2 0x35 0xAB"},
            ]
        },
    ],
    "TEMPERATURE":[
                 {
                 "name":"-->温度测试" , "cases":[
                        {"name":"入风口","cmd":"grtd_test.py  temp 2-0048/hwmon/hwmon1/temp1_input"},
                        {"name":"出风口","cmd":"grtd_test.py  temp 2-0049/hwmon/hwmon2/temp1_input"},
                        {"name":"最热点","cmd":"grtd_test.py  temp 2-004a/hwmon/hwmon3/temp1_input"},
                    ]
                }
        ],
    "MEMTORY":{
        "cases":[
            {"name":"->内存测试 1M","cmd":"memtester 1M 1"},
            {"name":"->内存测试 2M","cmd":"memtester 2M 1"},
            {"name":"->内存测试 8M","cmd":"memtester 8M 1"},
#           {"name":"->内存测试 16M","cmd":"memtester 16M 1"},
#           {"name":"->内存测试 256M","cmd":"memtester 256M 1"},
        ]
    },
    "SMARTCTLCMDS":{
        "cases":[
            {"name":"->硬盘信息查看",     "cmd":"smartctl -i /dev/sda"},
            {"name":"->检查硬盘监控状态", "cmd":"smartctl -H /dev/sda"},
        ]
    },
    "LED":[
        {"name":"端口点灯测试","cases":[
              {"name":"-> 红灯灭",        "cmd":"grtd_test.py  led loc 1-0034/sfp_led1_red,1-0034/sfp_led2_red,1-0034/sfp_led3_red,1-0034/sfp_led8_red,1-0036/sfp_led4_red,1-0036/sfp_led5_red,1-0036/sfp_led6_red,1-0036/sfp_led7_red 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00"},
              {"name":"-> 红灯亮",        "cmd":"grtd_test.py  led loc 1-0034/sfp_led1_red,1-0034/sfp_led2_red,1-0034/sfp_led3_red,1-0034/sfp_led8_red,1-0036/sfp_led4_red,1-0036/sfp_led5_red,1-0036/sfp_led6_red,1-0036/sfp_led7_red 0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff"},
              {"name":"-> 恢复红灯灭",        "cmd":"grtd_test.py  led loc 1-0034/sfp_led1_red,1-0034/sfp_led2_red,1-0034/sfp_led3_red,1-0034/sfp_led8_red,1-0036/sfp_led4_red,1-0036/sfp_led5_red,1-0036/sfp_led6_red,1-0036/sfp_led7_red 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00"},
              
              {"name":"-> 黄灯灭",        "cmd":"grtd_test.py  led loc 1-0034/sfp_led1_yellow,1-0034/sfp_led2_yellow,1-0034/sfp_led3_yellow,1-0034/sfp_led8_yellow,1-0036/sfp_led4_yellow,1-0036/sfp_led5_yellow,1-0036/sfp_led6_yellow,1-0036/sfp_led7_yellow 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00"},
              {"name":"-> 黄灯亮",        "cmd":"grtd_test.py  led loc 1-0034/sfp_led1_yellow,1-0034/sfp_led2_yellow,1-0034/sfp_led3_yellow,1-0034/sfp_led8_yellow,1-0036/sfp_led4_yellow,1-0036/sfp_led5_yellow,1-0036/sfp_led6_yellow,1-0036/sfp_led7_yellow 0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff"},
              {"name":"-> 恢复黄灯灭",        "cmd":"grtd_test.py  led loc 1-0034/sfp_led1_yellow,1-0034/sfp_led2_yellow,1-0034/sfp_led3_yellow,1-0034/sfp_led8_yellow,1-0036/sfp_led4_yellow,1-0036/sfp_led5_yellow,1-0036/sfp_led6_yellow,1-0036/sfp_led7_yellow 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00"},
            ]
        },
        {"name":"风扇1灯" ,"cases":[
              {"name":"-> 灯灭",        "cmd":"grtd_test.py  led loc 0-0032/fan0_led 0x0b"},
              {"name":"-> 红灯",        "cmd":"grtd_test.py  led loc 0-0032/fan0_led 0x0a"},
              {"name":"-> 绿灯",        "cmd":"grtd_test.py  led loc 0-0032/fan0_led 0x09"},
              {"name":"-> 黄灯",        "cmd":"grtd_test.py  led loc 0-0032/fan0_led 0x08"},
              {"name":"-> 红灯闪烁",    "cmd":"grtd_test.py  led loc 0-0032/fan0_led 0x0e"},
              {"name":"-> 绿灯闪烁",    "cmd":"grtd_test.py  led loc 0-0032/fan0_led 0x0d"},
              {"name":"-> 黄灯闪烁",    "cmd":"grtd_test.py  led loc 0-0032/fan0_led 0x0c"},
              {"name":"-> 恢复绿灯",        "cmd":"grtd_test.py  led loc 0-0032/fan0_led 0x09"},
            ]
        },
        {"name":"风扇2灯" ,"cases":[
              {"name":"-> 灯灭",      "cmd":"grtd_test.py  led loc 0-0032/fan1_led 0x0b"},
              {"name":"-> 红灯",      "cmd":"grtd_test.py  led loc 0-0032/fan1_led 0x0a"},
              {"name":"-> 绿灯",      "cmd":"grtd_test.py  led loc 0-0032/fan1_led 0x09"},
              {"name":"-> 黄灯",      "cmd":"grtd_test.py  led loc 0-0032/fan1_led 0x08"},
              {"name":"-> 红灯闪烁",  "cmd":"grtd_test.py  led loc 0-0032/fan1_led 0x0e"},
              {"name":"-> 绿灯闪烁",  "cmd":"grtd_test.py  led loc 0-0032/fan1_led 0x0d"},
              {"name":"-> 黄灯闪烁",  "cmd":"grtd_test.py  led loc 0-0032/fan1_led 0x0c"},
              {"name":"-> 恢复绿灯",      "cmd":"grtd_test.py  led loc 0-0032/fan1_led 0x09"},
            ]
        },
        {"name":"风扇3灯" ,"cases":[
              {"name":"-> 灯灭",      "cmd":"grtd_test.py  led loc 0-0032/fan2_led 0x0b"},
              {"name":"-> 红灯",      "cmd":"grtd_test.py  led loc 0-0032/fan2_led 0x0a"},
              {"name":"-> 绿灯",      "cmd":"grtd_test.py  led loc 0-0032/fan2_led 0x09"},
              {"name":"-> 黄灯",      "cmd":"grtd_test.py  led loc 0-0032/fan2_led 0x08"},
              {"name":"-> 红灯闪烁",  "cmd":"grtd_test.py  led loc 0-0032/fan2_led 0x0e"},
              {"name":"-> 绿灯闪烁",  "cmd":"grtd_test.py  led loc 0-0032/fan2_led 0x0d"},
              {"name":"-> 黄灯闪烁",  "cmd":"grtd_test.py  led loc 0-0032/fan2_led 0x0c"},
              {"name":"-> 恢复绿灯",      "cmd":"grtd_test.py  led loc 0-0032/fan2_led 0x09"},
            ]
        },
        {"name":"前面板CPU灯", "cases":[
              {"name":"-> 灯灭",        "cmd":"grtd_test.py  led loc 2-0035/broad_front_cpu 0x00"},
              {"name":"-> 绿灯不闪烁",    "cmd":"grtd_test.py  led loc 2-0035/broad_front_cpu 0x01"},
              {"name":"-> 红灯不闪烁",  "cmd":"grtd_test.py  led loc 2-0035/broad_front_cpu 0x02"},
              {"name":"-> 黄灯不闪烁",    "cmd":"grtd_test.py  led loc 2-0035/broad_front_cpu 0x03"},
              {"name":"-> 绿灯1/4s闪烁  ",    "cmd":"grtd_test.py  led loc 2-0035/broad_front_cpu 0x11"},
              {"name":"-> 绿灯1/2s闪烁  ",    "cmd":"grtd_test.py  led loc 2-0035/broad_front_cpu 0x21"},
              {"name":"-> 绿灯1s闪烁    ",    "cmd":"grtd_test.py  led loc 2-0035/broad_front_cpu 0x41"},
              {"name":"-> 绿灯2s闪烁    ",    "cmd":"grtd_test.py  led loc 2-0035/broad_front_cpu 0x81"},
              {"name":"-> 红灯1/4s闪烁  ",    "cmd":"grtd_test.py  led loc 2-0035/broad_front_cpu 0x12"},
              {"name":"-> 红灯1/2s闪烁  ",    "cmd":"grtd_test.py  led loc 2-0035/broad_front_cpu 0x22"},
              {"name":"-> 红灯1s闪烁    ",    "cmd":"grtd_test.py  led loc 2-0035/broad_front_cpu 0x42"},
              {"name":"-> 红灯2s闪烁    ",    "cmd":"grtd_test.py  led loc 2-0035/broad_front_cpu 0x82"},
              {"name":"-> 黄灯1/4s闪烁  ",    "cmd":"grtd_test.py  led loc 2-0035/broad_front_cpu 0x13"},
              {"name":"-> 黄灯1/2s闪烁  ",    "cmd":"grtd_test.py  led loc 2-0035/broad_front_cpu 0x23"},
              {"name":"-> 黄灯1s闪烁    ",    "cmd":"grtd_test.py  led loc 2-0035/broad_front_cpu 0x43"},
              {"name":"-> 黄灯2s闪烁    ",    "cmd":"grtd_test.py  led loc 2-0035/broad_front_cpu 0x83"},
              {"name":"-> 恢复绿灯",        "cmd":"grtd_test.py  led loc 2-0035/broad_front_cpu 0x01"},
            ]
        },
        {"name":"前面板BMC灯" ,"cases":[
              {"name":"-> 灯灭",        "cmd":"grtd_test.py  led loc 2-0035/broad_front_bmc 0x00"},
              {"name":"-> 红灯闪烁",    "cmd":"grtd_test.py  led loc 2-0035/broad_front_bmc 0x01"},
              {"name":"-> 红灯不闪烁",  "cmd":"grtd_test.py  led loc 2-0035/broad_front_bmc 0x02"},
              {"name":"-> 绿灯闪烁",    "cmd":"grtd_test.py  led loc 2-0035/broad_front_bmc 0x03"},
              {"name":"-> 绿灯不闪烁",  "cmd":"grtd_test.py  led loc 2-0035/broad_front_bmc 0x04"},
              {"name":"-> 黄灯闪烁",    "cmd":"grtd_test.py  led loc 2-0035/broad_front_bmc 0x05"},
              {"name":"-> 黄灯不闪烁",  "cmd":"grtd_test.py  led loc 2-0035/broad_front_bmc 0x06"},
              {"name":"-> 恢复绿灯",    "cmd":"grtd_test.py  led loc 2-0035/broad_front_bmc 0x04"},
            ]
        },
        {"name":"前面板定位灯" , "cases":[
                {"name":"->灯灭","cmd":"grtd_test.py  led loc 2-0035/broad_front_lct 0xff"},
                {"name":"->灯亮","cmd":"grtd_test.py  led loc 2-0035/broad_front_lct 0xfe"},
                {"name":"->恢复灯灭","cmd":"grtd_test.py  led loc 2-0035/broad_front_lct 0xff"},
                ]
        },
        
        {"name":"前面板pwr灯" ,"cases":[
              {"name":"-> 灯灭",        "cmd":"grtd_test.py  led loc 2-0035/broad_front_pwr 0x00"},
              {"name":"-> 红灯闪烁",    "cmd":"grtd_test.py  led loc 2-0035/broad_front_pwr 0x01"},
              {"name":"-> 红灯不闪烁",  "cmd":"grtd_test.py  led loc 2-0035/broad_front_pwr 0x02"},
              {"name":"-> 绿灯闪烁",    "cmd":"grtd_test.py  led loc 2-0035/broad_front_pwr 0x03"},
              {"name":"-> 绿灯不闪烁",  "cmd":"grtd_test.py  led loc 2-0035/broad_front_pwr 0x04"},
              {"name":"-> 黄灯闪烁",    "cmd":"grtd_test.py  led loc 2-0035/broad_front_pwr 0x05"},
              {"name":"-> 黄灯不闪烁",  "cmd":"grtd_test.py  led loc 2-0035/broad_front_pwr 0x06"},
              {"name":"-> 恢复绿灯",        "cmd":"grtd_test.py  led loc 2-0035/broad_front_pwr 0x04"},
            ]
        },
        {"name":"前面板fan灯" ,"cases":[
              {"name":"-> 灯灭",        "cmd":"grtd_test.py  led loc 2-0035/broad_front_fan 0x00"},
              {"name":"-> 红灯闪烁",    "cmd":"grtd_test.py  led loc 2-0035/broad_front_fan 0x01"},
              {"name":"-> 红灯不闪烁",  "cmd":"grtd_test.py  led loc 2-0035/broad_front_fan 0x02"},
              {"name":"-> 绿灯闪烁",    "cmd":"grtd_test.py  led loc 2-0035/broad_front_fan 0x03"},
              {"name":"-> 绿灯不闪烁",  "cmd":"grtd_test.py  led loc 2-0035/broad_front_fan 0x04"},
              {"name":"-> 黄灯闪烁",    "cmd":"grtd_test.py  led loc 2-0035/broad_front_fan 0x05"},
              {"name":"-> 黄灯不闪烁",  "cmd":"grtd_test.py  led loc 2-0035/broad_front_fan 0x06"},
              {"name":"-> 恢复绿灯",    "cmd":"grtd_test.py  led loc 2-0035/broad_front_fan 0x04"},
            ]
        },

    ],
    "I2C":[
    ####type 1表示取到的值与value比较
    ####type 2表示返回的是True或False
            {"name":"I2C设备检测" ,"cases":[
                  {"name":" PCA9641测试", "cmd":"grtd_test.py  dev_rd  0 10 0","deal_type":2},
                  {"name":" cpld32测试", "cmd":"grtd_test.py  dev_rd  0 32 0","deal_type":2},
                  {"name":" cpld33测试", "cmd":"grtd_test.py  dev_rd  0 32 0","deal_type":2},
                  {"name":" cpld34测试", "cmd":"grtd_test.py  dev_rd  0 32 0","deal_type":2},
                  {"name":" cpld35测试", "cmd":"grtd_test.py  dev_rd  0 32 0","deal_type":2},
                  {"name":" cpld36测试", "cmd":"grtd_test.py  dev_rd  0 32 0","deal_type":2},
                  {"name":" cpld37测试", "cmd":"grtd_test.py  dev_rd  0 32 0","deal_type":2},
                  {"name":" 入风口LM75", "cmd":"grtd_test.py  dev_rd  0 32 0","deal_type":2},
                  {"name":" 出风口LM75", "cmd":"grtd_test.py  dev_rd  0 32 0","deal_type":2},
                  {"name":" 最热点LM75", "cmd":"grtd_test.py  dev_rd  0 32 0","deal_type":2},
                  {"name":" EEPROM", "cmd":"grtd_test.py  dev_rd  0 32 0","deal_type":2},
                  {"name":" 端口1",        "cmd":"grtd_test.py  dev_rd  11 0050 0","deal_type":2},
                  {"name":" 端口2",        "cmd":"grtd_test.py  dev_rd  12 0050 0","deal_type":2},
                  {"name":" 端口3",        "cmd":"grtd_test.py  dev_rd  13 0050 0","deal_type":2},
                  {"name":" 端口4",        "cmd":"grtd_test.py  dev_rd  14 0050 0","deal_type":2},
                  {"name":" 端口5",        "cmd":"grtd_test.py  dev_rd  15 0050 0","deal_type":2},
                  {"name":" 端口6",        "cmd":"grtd_test.py  dev_rd  16 0050 0","deal_type":2},
                  {"name":" 端口7",        "cmd":"grtd_test.py  dev_rd  17 0050 0","deal_type":2},
                  {"name":" 端口8",        "cmd":"grtd_test.py  dev_rd  18 0050 0","deal_type":2},
                  {"name":" 端口9",        "cmd":"grtd_test.py  dev_rd  19 0050 0","deal_type":2},
                  {"name":" 端口10",        "cmd":"grtd_test.py  dev_rd  20 0050 0","deal_type":2},
                  {"name":" 端口11",        "cmd":"grtd_test.py  dev_rd  21 0050 0","deal_type":2},
                  {"name":" 端口12",        "cmd":"grtd_test.py  dev_rd  22 0050 0","deal_type":2},
                  {"name":" 端口13",        "cmd":"grtd_test.py  dev_rd  23 0050 0","deal_type":2},
                  {"name":" 端口14",        "cmd":"grtd_test.py  dev_rd  24 0050 0","deal_type":2},
                  {"name":" 端口15",        "cmd":"grtd_test.py  dev_rd  25 0050 0","deal_type":2},
                  {"name":" 端口16",        "cmd":"grtd_test.py  dev_rd  26 0050 0","deal_type":2},
                  {"name":" 端口17",        "cmd":"grtd_test.py  dev_rd  27 0050 0","deal_type":2},
                  {"name":" 端口18",        "cmd":"grtd_test.py  dev_rd  28 0050 0","deal_type":2},
                  {"name":" 端口19",        "cmd":"grtd_test.py  dev_rd  29 0050 0","deal_type":2}, 
                  {"name":" 端口20",        "cmd":"grtd_test.py  dev_rd  30 0050 0","deal_type":2},
                  {"name":" 端口21",        "cmd":"grtd_test.py  dev_rd  31 0050 0","deal_type":2},
                  {"name":" 端口22",        "cmd":"grtd_test.py  dev_rd  32 0050 0","deal_type":2},
                  {"name":" 端口23",        "cmd":"grtd_test.py  dev_rd  33 0050 0","deal_type":2},
                  {"name":" 端口24",        "cmd":"grtd_test.py  dev_rd  34 0050 0","deal_type":2},
                  {"name":" 端口25",        "cmd":"grtd_test.py  dev_rd  35 0050 0","deal_type":2},
                  {"name":" 端口26",        "cmd":"grtd_test.py  dev_rd  36 0050 0","deal_type":2},
                  {"name":" 端口27",        "cmd":"grtd_test.py  dev_rd  37 0050 0","deal_type":2},
                  {"name":" 端口28",        "cmd":"grtd_test.py  dev_rd  38 0050 0","deal_type":2},
                  {"name":" 端口29",        "cmd":"grtd_test.py  dev_rd  39 0050 0","deal_type":2},
                  {"name":" 端口30",        "cmd":"grtd_test.py  dev_rd  40 0050 0","deal_type":2},
                  {"name":" 端口31",        "cmd":"grtd_test.py  dev_rd  41 0050 0","deal_type":2},
                  {"name":" 端口32",        "cmd":"grtd_test.py  dev_rd  42 0050 0","deal_type":2},
                  {"name":" 端口33",        "cmd":"grtd_test.py  dev_rd  43 0050 0","deal_type":2},
                  {"name":" 端口34",        "cmd":"grtd_test.py  dev_rd  44 0050 0","deal_type":2},
                  {"name":" 端口35",        "cmd":"grtd_test.py  dev_rd  45 0050 0","deal_type":2},
                  {"name":" 端口36",        "cmd":"grtd_test.py  dev_rd  46 0050 0","deal_type":2},
                  {"name":" 端口37",        "cmd":"grtd_test.py  dev_rd  47 0050 0","deal_type":2},
                  {"name":" 端口38",        "cmd":"grtd_test.py  dev_rd  48 0050 0","deal_type":2},
                  {"name":" 端口39",        "cmd":"grtd_test.py  dev_rd  49 0050 0","deal_type":2},
                  {"name":" 端口40",        "cmd":"grtd_test.py  dev_rd  50 0050 0","deal_type":2},
                  {"name":" 端口41",        "cmd":"grtd_test.py  dev_rd  51 0050 0","deal_type":2},
                  {"name":" 端口42",        "cmd":"grtd_test.py  dev_rd  52 0050 0","deal_type":2},
                  {"name":" 端口43",        "cmd":"grtd_test.py  dev_rd  53 0050 0","deal_type":2},
                  {"name":" 端口44",        "cmd":"grtd_test.py  dev_rd  54 0050 0","deal_type":2},
                  {"name":" 端口45",        "cmd":"grtd_test.py  dev_rd  55 0050 0","deal_type":2},
                  {"name":" 端口46",        "cmd":"grtd_test.py  dev_rd  56 0050 0","deal_type":2},
                  {"name":" 端口47",        "cmd":"grtd_test.py  dev_rd  57 0050 0","deal_type":2},
                  {"name":" 端口48",        "cmd":"grtd_test.py  dev_rd  58 0050 0","deal_type":2},
                  {"name":" 端口49",        "cmd":"grtd_test.py  dev_rd  59 0050 0","deal_type":2},
                  {"name":" 端口50",        "cmd":"grtd_test.py  dev_rd  60 0050 0","deal_type":2},
                  {"name":" 端口51",        "cmd":"grtd_test.py  dev_rd  61 0050 0","deal_type":2},
                  {"name":" 端口52",        "cmd":"grtd_test.py  dev_rd  62 0050 0","deal_type":2},
                  {"name":" 端口53",        "cmd":"grtd_test.py  dev_rd  63 0050 0","deal_type":2},
                  {"name":" 端口54",        "cmd":"grtd_test.py  dev_rd  64 0050 0","deal_type":2},
                  {"name":" 端口55",        "cmd":"grtd_test.py  dev_rd  65 0050 0","deal_type":2},
                  {"name":" 端口56",        "cmd":"grtd_test.py  dev_rd  66 0050 0","deal_type":2},
                  {"name":" 端口57",        "cmd":"grtd_test.py  dev_rd  67 0050 0","deal_type":2},
                  {"name":" 端口58",        "cmd":"grtd_test.py  dev_rd  68 0050 0","deal_type":2},
                  {"name":" 端口59",        "cmd":"grtd_test.py  dev_rd  69 0050 0","deal_type":2},
                  {"name":" 端口60",        "cmd":"grtd_test.py  dev_rd  70 0050 0","deal_type":2},
                  {"name":" 端口61",        "cmd":"grtd_test.py  dev_rd  71 0050 0","deal_type":2},
                  {"name":" 端口62",        "cmd":"grtd_test.py  dev_rd  72 0050 0","deal_type":2},
                  {"name":" 端口63",        "cmd":"grtd_test.py  dev_rd  73 0050 0","deal_type":2},
                  {"name":" 端口64",        "cmd":"grtd_test.py  dev_rd  74 0050 0","deal_type":2},
                ]
            },
    ],
}

PCIe_DEV_LIST = []
PCIe_SPEED_ITEM = []

################################生测适配区#######################################################




