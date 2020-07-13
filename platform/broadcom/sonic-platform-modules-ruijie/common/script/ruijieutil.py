#!/usr/bin/python
# -*- coding: UTF-8 -*-
#-------------------------------------------------------------------------
# Name:        锐捷 python通用模块
# Purpose:      供其他模块调用
#
# Author:      tjm
#
# Created:     02/07/2018
# Copyright:   (c) tjm 2018
#-------------------------------------------------------------------------
import sys
import os
import re
import commands
import syslog
import time
import binascii
import tty
import termios
import threading
import click
import mmap
from ruijieconfig import *
#from fruutil import fru
#from tabulate import tabulate
#import readline
try:
    from eepromutil.fru import *
except:
    pass

import logging.handlers
import shutil
import gzip
import glob

MENUID = "menuid"
MENUPARENT = "parentid"
MENUVALUE = "value"
CHILDID = "childid"
MENUITEMNAME = "name"
MENUITEMDEAL = "deal"
GOBACK = "goBack"
GOQUIT = "quit"

file_name = "/etc/init.d/opennsl-modules-3.16.0-5-amd64"
##########################################################################
# 错误日志等级
##########################################################################
CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0

levelNames = {
    CRITICAL: 'CRITICAL',
    ERROR: 'ERROR',
    WARNING: 'WARNING',
    INFO: 'INFO',
    DEBUG: 'DEBUG',
    NOTSET: 'NOTSET',
    'CRITICAL': CRITICAL,
    'ERROR': ERROR,
    'WARN': WARNING,
    'WARNING': WARNING,
    'INFO': INFO,
    'DEBUG': DEBUG,
    'NOTSET': NOTSET,
}

TLV_INFO_ID_STRING = "TlvInfo\x00"
TLV_INFO_VERSION = 0x01
TLV_INFO_LENGTH = 0x00
TLV_INFO_LENGTH_VALUE = 0xba

##########################################################################
# eeprom信息索引定义
##########################################################################
TLV_CODE_PRODUCT_NAME = 0x21
TLV_CODE_PART_NUMBER = 0x22
TLV_CODE_SERIAL_NUMBER = 0x23
TLV_CODE_MAC_BASE = 0x24
TLV_CODE_MANUF_DATE = 0x25
TLV_CODE_DEVICE_VERSION = 0x26
TLV_CODE_LABEL_REVISION = 0x27
TLV_CODE_PLATFORM_NAME = 0x28
TLV_CODE_ONIE_VERSION = 0x29
TLV_CODE_MAC_SIZE = 0x2A
TLV_CODE_MANUF_NAME = 0x2B
TLV_CODE_MANUF_COUNTRY = 0x2C
TLV_CODE_VENDOR_NAME = 0x2D
TLV_CODE_DIAG_VERSION = 0x2E
TLV_CODE_SERVICE_TAG = 0x2F
TLV_CODE_VENDOR_EXT = 0xFD
TLV_CODE_CRC_32 = 0xFE
_TLV_DISPLAY_VENDOR_EXT = 1
TLV_CODE_RJ_CARID = 0x01
_TLV_INFO_HDR_LEN = 11


SYSLOG_IDENTIFIER = "UTILTOOL"

# ========================== Syslog wrappers ==========================

def log_info(msg, also_print_to_console=False):
    #msg = msg.decode('utf-8').encode('gb2312')
    syslog.openlog(SYSLOG_IDENTIFIER)
    syslog.syslog(syslog.LOG_INFO, msg)
    syslog.closelog()

    if also_print_to_console:
        click.echo(msg)


def log_debug(msg, also_print_to_console=False):
    try:
        #msg = msg.decode('utf-8').encode('gb2312')
        syslog.openlog(SYSLOG_IDENTIFIER)
        syslog.syslog(syslog.LOG_DEBUG, msg)
        syslog.closelog()

        if also_print_to_console:
            click.echo(msg)
    except Exception as e:
        pass


def log_warning(msg, also_print_to_console=False):
    #msg = msg.decode('utf-8').encode('gb2312')
    syslog.openlog(SYSLOG_IDENTIFIER)
    syslog.syslog(syslog.LOG_WARNING, msg)
    syslog.closelog()

    if also_print_to_console:
        click.echo(msg)


def log_error(msg, also_print_to_console=False):
    #msg = msg.decode('utf-8').encode('gb2312')
    syslog.openlog(SYSLOG_IDENTIFIER)
    syslog.syslog(syslog.LOG_ERR, msg)
    syslog.closelog()

    if also_print_to_console:
        click.echo(msg)

#bmc-console.log bmc_feed_watchdog.log日志压缩
class CompressedRotatingFileHandler(logging.handlers.RotatingFileHandler):
    def doRollover(self):
        """
        Do a rollover, as described in __init__().
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = "%s.%d.gz" % (self.baseFilename, i)
                dfn = "%s.%d.gz" % (self.baseFilename, i + 1)
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            dfn = self.baseFilename + ".1.gz"
            if os.path.exists(dfn):
                os.remove(dfn)
            # These two lines below are the only new lines. I commented out the os.rename(self.baseFilename, dfn) and
            #  replaced it with these two lines.
            with open(self.baseFilename, 'rb') as f_in, gzip.open(dfn, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        self.mode = 'w'
        self.stream = self._open()


class SETMACException(Exception):
    def __init__(self, param='错误', errno="-1"):
        err = "setmac出错[%s]: %s" % (errno, param)
        Exception.__init__(self, err)
        self.param = param
        self.errno = errno

def checkinput(b):
    if b.isdigit() == False:
        raise Exception("非法数字")
    if int(b) > 0xff or int(b) < 0:
        raise Exception("不在区间内")

def checkinputproduct(b):
    if b.isalnum() ==False:
        raise Exception("非法字符串")

def getInputSetmac(val):
    bia = val.boardInfoArea
    pia = val.productInfoArea
    if bia != None:
        a = raw_input("[板卡区]产品序列号:")
        if len(a) != 13:
            raise Exception("序列号长度不对")
        checkinputproduct(a)
        bia.boardSerialNumber = a
        b = raw_input("[板卡区]产品版本号:(从1-255)")
        checkinput(b)
        b = "%0x" % int(b)
        bia.boardextra1 = b.upper()
    if pia != None:
        a = raw_input("[产品区]产品序列号:")
        if len(a) != 13:
            raise Exception("序列号长度不对")
        checkinputproduct(a)
        pia.productSerialNumber = a
        b = raw_input("[产品区]产品版本号:(从1-255)")
        checkinput(b)
        b = "%0x" % int(b)
        pia.productVersion = b.upper()
    return val

'''
class FruUtil():
    def test(self):
        ret = fru.E2Util.decodeBinName("/sys/bus/i2c/devices/4-0051/eeprom")
        bia = ret.boardInfoArea
        pia = ret.productInfoArea
        print bia
        print pia
    
    def setmac_InputBoardArea(self, bia):
        if bia != None:
            a = raw_input("[板卡区]产品序列号:")
            bia.boardSerialNumber = a
            b = raw_input("[板卡区]产品版本号:(从1-255)")
            bia.boardextra1 = b.upper()
        return bia
    
    def getInputSetmac(self, val):
        bia = val.boardInfoArea
        pia = val.productInfoArea
        if bia != None:
            a = raw_input("[板卡区]产品序列号:")
            bia.boardSerialNumber = a
            b = raw_input("[板卡区]产品版本号:(从1-255)")
            bia.boardextra1 = b.upper()
        if pia != None:
            a = raw_input("[产品区]产品序列号:")
            pia.productSerialNumber = a
            b = raw_input("[产品区]产品版本号:(从1-255)")
            pia.productVersion = b.upper()
            if pia.productExtra2 != None:
                b = raw_input("[产品区]MAC地址:")
                pia.productExtra2 = fru.E2Util.encodeMac(b.upper())

            if pia.productExtra3 != None:
                b = raw_input("[产品区]MAC数量:")
                pia.productExtra3 = fru.E2Util.encodeMacLen(b)
        result = fru.E2Util.generateBinBySetMac(bia, pia)
        return result
    
    def globalsetmac(self, type1):
        msg  = type1[0]
        fruMsg = self.getfruMsg(msg['bus'], msg['loc'])
        result = self.getInputSetmac(fruMsg)
        I2CUTIL.writeToE2(msg['bus'], msg['loc'], result.bindata)
    
    def dumpValueByI2c(self, bus, loc):
        str = ""
        for i in range(256):
            ret,val = rji2cget(bus, loc, i)
            str += chr(strtoint(val))
        return str
    
    def fansetmac(self, vals):
        x = sorted(vals,lambda x,y: cmp(x["name"], y["name"]))
        for item in x:
            fruMsg = self.getfruMsg(item['bus'], item['loc'])
            print "%s:"% item['name']
            result = self.getInputSetmac(fruMsg)
            I2CUTIL.writeToE2(item['bus'], item['loc'], result.bindata)
        pass
    
    def getsyseepromDict(self):
        ret = get_sys_eeprom()
        ret_t = {}
        for item in ret:
            ret_t[item['code']] = item['value']
        return ret_t
    
    def cpufrusetmac(self, vals):
        msg  = vals[0]
        fruMsg = self.getfruMsg(msg['bus'], msg['loc'])
        bia = fruMsg.boardInfoArea
        pia = fruMsg.productInfoArea
        
        bia = self.setmac_InputBoardArea(bia)
        sysee = self.getsyseepromDict()
        pia.productName = sysee[33]
        pia.productPartModelName = sysee[34]
        pia.productVersion = sysee[38]
        pia.productSerialNumber = sysee[35]
        pia.productExtra2 = fru.E2Util.encodeMac(sysee[36].replace(":",""))
        pia.productExtra3 = fru.E2Util.encodeMacLen(sysee[42])
        result = fru.E2Util.generateBinBySetMac(bia, pia)
        I2CUTIL.writeToE2(msg['bus'], msg['loc'], result.bindata)
        pass 
        
    def slotmac(self, vals):
        x = sorted(vals,lambda x,y: cmp(x["name"], y["name"]))
        for item in x:
            fruMsg = self.getfruMsg(item['bus'], item['loc'])
            print "%s:"% item['name']
            result = self.getInputSetmac(fruMsg)
            I2CUTIL.writeToE2(item['bus'], item['loc'], result.bindata)
        pass

    def showmac(self, type):
        vals = [ elem  for elem in FRULISTS if type == elem["E2TYPE"]]
        val_ts = sorted(vals,lambda x,y: cmp(x["name"], y["name"]))
        for val in val_ts:
            print "####################%s####################" % val["name"]
            filename = I2CUTIL.getE2File(val['bus'], val['loc'])
            ret = FruUtil.fru_decode_eeprom(filename)
            head = ["key","value"]
            if ret.boardInfoArea!= None:
                print "=================board================="
                print tabulate(ret.boardInfoArea.todict().items(), head, tablefmt="simple")
             
            if ret.productInfoArea!= None:
                print"=================product================="
                print tabulate(ret.productInfoArea.todict().items(), head, tablefmt="simple")

    def setmac(self, type1):
        vals = [ elem  for elem in FRULISTS if (type1 == elem["E2TYPE"] and elem["CANRESET"] == '1' )]
        if len(vals) <= 0:
            return None
        if type1 == "8" or type1 == "A":
            I2CUTIL.openFanE2Protect()
            self.fansetmac(vals)
            I2CUTIL.closeFanE2Protect()
            return
        elif type1 == "6":
            return  self.slotmac(vals)
        elif type1 == "4":
            return self.cpufrusetmac(vals)
        else:
            return self.globalsetmac(vals)

    def getfruMsg(self, bus, loc):
        filename = I2CUTIL.getE2File(bus, loc)
        ret = FruUtil.fru_decode_eeprom(filename)
        return ret
        
    def getfruMsgByI2C(self, bus,loc):
        retval = self.dumpValueByI2c(bus,loc)
        return FruUtil.fru_decode_eepromByValue(retval)
        
    @staticmethod
    def fru_getdefault_eeprom(product, type1):
        return fru.E2Util.defaultBinByConfig(product,type1)
    
    @staticmethod
    def fru_decode_eeprom(filename):
        return fru.E2Util.decodeBinName(filename)
    
    @staticmethod
    def fru_decode_eepromByValue(val):
        return fru.E2Util.decodeBinByValue(val)
'''

class fan_tlv():
    VERSION = 0x01                       # E2PROM文件定义的版本号，初始版本为0x01
    FLAG = 0x7E                       # 新版本E2PROM标识为0x7E
    HW_VER = 0X01                       # 由主版本号与修正版本两部份构成
    TYPE = 0xf1                       # 硬件类型定义信息
    TLV_LEN = 00                        # 有效数据长度（16bit）
    _FAN_TLV_HDR_LEN = 6
    _FAN_TLV_CRC_LEN = 2

    _FAN_TLV_TYPE_NAME = 0x02
    _FAN_TLV_TYPE_SN = 0x03
    _FAN_TLV_TYPE_HW_INFO = 0x05
    _FAN_TLV_TYPE_DEV_TYPE = 0x06

    _fandecodetime = 0

    @property
    def dstatus(self):
        return self._dstatus

    @property
    def typename(self):
        return self._typename

    @property
    def typesn(self):
        return self._typesn

    @property
    def typehwinfo(self):
        return self._typehwinfo

    @property
    def typedevtype(self):
        return self._typedevtype

    @property
    def fanbus(self):
        return self._fanbus

    @property
    def fanloc(self):
        return self._fanloc

    @property
    def fandecodetime(self):
        return self._fandecodetime

    def __init__(self):
        self._typename = ""
        self._typesn = ""
        self._typehwinfo = ""
        self._typedevtype = ""
        self._dstatus = 0

    def strtoarr(self, str):
        s = []
        if str is not None :
            for index in str:
                s.append(index)
        return s

    def generate_fan_value(self):
        bin_buffer = [chr(0xff)] * 256
        bin_buffer[0] = chr(self.VERSION)
        bin_buffer[1] = chr(self.FLAG)
        bin_buffer[2] = chr(self.HW_VER)
        bin_buffer[3] = chr(self.TYPE)

        temp_t = "%08x" % self.typedevtype  # 把devtype先处理下
        typedevtype_t = hex_to_str(temp_t)
        total_len = len(self.typename) + len(self.typesn) + \
            len(self.typehwinfo) + len(typedevtype_t) + 8

        bin_buffer[4] = chr(total_len >> 8)
        bin_buffer[5] = chr(total_len & 0x00FF)

        index_start = 6
        bin_buffer[index_start] = chr(self._FAN_TLV_TYPE_NAME)
        bin_buffer[index_start + 1] = chr(len(self.typename))
        bin_buffer[index_start + 2: index_start + 2 +
                   len(self.typename)] = self.strtoarr(self.typename)
        index_start = index_start + 2 + len(self.typename)

        bin_buffer[index_start] = chr(self._FAN_TLV_TYPE_SN)
        bin_buffer[index_start + 1] = chr(len(self.typesn))
        bin_buffer[index_start + 2:index_start + 2 +
                   len(self.typesn)] = self.strtoarr(self.typesn)
        index_start = index_start + 2 + len(self.typesn)

        bin_buffer[index_start] = chr(self._FAN_TLV_TYPE_HW_INFO)
        bin_buffer[index_start + 1] = chr(len(self.typehwinfo))
        bin_buffer[index_start + 2:index_start + 2 +
                   len(self.typehwinfo)] = self.strtoarr(self.typehwinfo)
        index_start = index_start + 2 + len(self.typehwinfo)

        bin_buffer[index_start] = chr(self._FAN_TLV_TYPE_DEV_TYPE)
        bin_buffer[index_start + 1] = chr(len(typedevtype_t))
        bin_buffer[index_start + 2:index_start + 2 +
                   len(typedevtype_t)] = self.strtoarr(typedevtype_t)
        index_start = index_start + 2 + len(typedevtype_t)

        crcs = fan_tlv.fancrc(''.join(bin_buffer[0:index_start]))  # 2个字节检验
        bin_buffer[index_start] = chr(crcs >> 8)
        bin_buffer[index_start + 1] = chr(crcs & 0x00ff)
        # printvalue(bin_buffer)
        return bin_buffer

    def decode(self, e2):
        ret = []
        self.VERSION = ord(e2[0])
        self.FLAG = ord(e2[1])
        self.HW_VER = ord(e2[2])
        self.TYPE = ord(e2[3])
        self.TLV_LEN = (ord(e2[4]) << 8) | ord(e2[5])

        tlv_index = self._FAN_TLV_HDR_LEN
        tlv_end = self._FAN_TLV_HDR_LEN + self.TLV_LEN

        # 判断校验和
        if len(e2) < self._FAN_TLV_HDR_LEN + self.TLV_LEN + 2:
            self._dstatus = -2
            return ret
        sumcrc = fan_tlv.fancrc(e2[0:self._FAN_TLV_HDR_LEN + self.TLV_LEN])
        readcrc = ord(e2[self._FAN_TLV_HDR_LEN + self.TLV_LEN]
                      ) << 8 | ord(e2[self._FAN_TLV_HDR_LEN + self.TLV_LEN + 1])
        if sumcrc != readcrc:
            self._dstatus = -1
            return ret
        else:
            self._dstatus = 0
        while (tlv_index + 2) < len(e2) and tlv_index < tlv_end:
            s = self.decoder(
                e2[tlv_index:tlv_index + 2 + ord(e2[tlv_index + 1])])
            tlv_index += ord(e2[tlv_index + 1]) + 2
            ret.append(s)

        return ret

    @staticmethod
    def fancrc(t):
        sum = 0
        for index in range(len(t)):
            sum += ord(t[index])
        return sum

    def decoder(self, t):
        try:
            name = ""
            value = ""
            if ord(t[0]) == self._FAN_TLV_TYPE_NAME:
                name = "Product Name"
                value = str(t[2:2 + ord(t[1])])
                self._typename = value
            elif ord(t[0]) == self._FAN_TLV_TYPE_SN:
                name = "serial Number"
                value = str(t[2:2 + ord(t[1])])
                self._typesn = value
            elif ord(t[0]) == self._FAN_TLV_TYPE_HW_INFO:
                name = "hardware info"
                value = str(t[2:2 + ord(t[1])])
                self._typehwinfo = value
            elif ord(t[0]) == self._FAN_TLV_TYPE_DEV_TYPE:
                name = "dev type"
                value = str(t[2:2 + ord(t[1])])
                value = str_to_hex(value)
                self._typedevtype = value
                value = "0x08%x" % value
        except Exception as e:
            print e
        return {"name": name, "code": ord(t[0]), "value": value}

    def __str__(self):
        formatstr = "VERSION     : 0x%02x  \n" \
                    "   FLAG     : 0x%02x  \n" \
                    " HW_VER     : 0x%02x  \n" \
                    "   TYPE     : 0x%02x  \n" \
                    "typename    : %s      \n" \
                    "typesn      : %s      \n" \
                    "typehwinfo  : %s      \n"
        return formatstr % (self.VERSION, self.FLAG, self.HW_VER, self.TYPE, self.typename, self.typesn, self.typehwinfo)


class AVSUTIL():
    @staticmethod
    def mac_avs_chip(bus, devno, loc, open, close, loop, protectaddr, level, loopaddr):
        # 关闭保护
        rji2cset(bus, devno, protectaddr, open)
        rji2cset(bus, devno, loopaddr, loop)
        rji2csetWord(bus, devno, loc, level)
        ret, value = rji2cgetWord(bus, devno, loc)
        if strtoint(value) == level:
            ret = 0
        # 打开保护
        rji2cset(bus, devno, protectaddr, close)
        if ret == 0:
            return True
        return False

    @staticmethod
    def macPressure_adj(macavs, avs_param, mac_def_param):
        # 判断是否在范围内
        max_adj = max(avs_param.keys())
        min_adj = min(avs_param.keys())
        type = mac_def_param["type"]
        level = 0
        if type == 0:
            if macavs not in range(min_adj, max_adj + 1):
                return False
            else:
                level = macavs
        else:
            if macavs not in range(min_adj, max_adj + 1):
                level = mac_def_param["default"]
            else:
                level = macavs
        ret = AVSUTIL.mac_avs_chip(mac_def_param["bus"], mac_def_param["devno"], mac_def_param["addr"], mac_def_param["open"],
                                   mac_def_param["close"], mac_def_param["loop"], mac_def_param["protectaddr"], avs_param[level], mac_def_param["loopaddr"])
        return ret

    @staticmethod
    def mac_adj():
        macavs = 0
        name = MAC_DEFAULT_PARAM["sdkreg"]
        ret, status = getSdkReg(name)
        if ret == False:
            return False
        status = strtoint(status)
        # 移位操作
        if MAC_DEFAULT_PARAM["sdktype"] != 0:
            status = (
                status >> MAC_DEFAULT_PARAM["macregloc"]) & MAC_DEFAULT_PARAM["mask"]
        macavs = status
        ret = AVSUTIL.macPressure_adj(macavs, MAC_AVS_PARAM, MAC_DEFAULT_PARAM)
        return ret


class I2CUTIL():
    @staticmethod
    def getvaluefromdevice(name):
        ret = []
        for item in DEVICE:
            if item["name"] == name:
                ret.append(item)
        return ret

    @staticmethod
    def openFanE2Protect():
        rji2cset(FAN_PROTECT["bus"], FAN_PROTECT["devno"],
                 FAN_PROTECT["addr"], FAN_PROTECT["open"])

    @staticmethod
    def closeFanE2Protect():
        rji2cset(FAN_PROTECT["bus"], FAN_PROTECT["devno"],
                 FAN_PROTECT["addr"], FAN_PROTECT["close"])

    @staticmethod
    def writeToFanE2(bus, loc, rst_arr):
        index = 0
        for item in rst_arr:
            rji2cset(bus, loc, index, ord(item))
            index += 1
            
    @staticmethod
    def writeToE2(bus, loc, rst_arr):
        index = 0
        for item in rst_arr:
            rji2cset(bus, loc, index, ord(item))
            index += 1
    
    @staticmethod
    def getE2File(bus, loc):
        return "/sys/bus/i2c/devices/%d-00%02x/eeprom" % (bus, loc)


class BMC():
    _instance_lock = threading.Lock()

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if not hasattr(Singleton, "_instance"):
            with Singleton._instance_lock:
                if not hasattr(Singleton, "_instance"):
                    Singleton._instance = object.__new__(cls)
        return Singleton._instance

# 内部接口


def getSdkReg(reg):
    try:
        cmd = "bcmcmd -t 1 'getr %s ' < /dev/null" % reg
        ret, result = rj_os_system(cmd)
        result_t = result.strip().replace("\r", "").replace("\n", "")
        if ret != 0 or "Error:" in result_t:
            return False, result
        patt = r"%s.(.*):(.*)>drivshell" % reg
        rt = re.findall(patt, result_t, re.S)
        test = re.findall("=(.*)", rt[0][0])[0]
    except Exception as e:
        return False, 'getsdk register error'
    return True, test


def getfilevalue(location):
    try:
        with open(location, 'r') as fd:
            value = fd.read()
        return True, value.strip()
    except Exception as e:
        return False, "error"


def get_sysfs_value(location):
    pos_t = str(location)
    name = get_pmc_register(pos_t)
    return name


def write_sysfs_value(reg_name, value):
    fileLoc = MAILBOX_DIR + reg_name
    try:
        if not os.path.isfile(fileLoc):
            print fileLoc,  'not found !'
            return False
        with open(fileLoc, 'w') as fd:
            fd.write(value)
    except Exception as error:
        log_error("Unable to open " + fileLoc + "file !")
        return False
    return True


def RJPRINTERR(str):
    print("\033[0;31m%s\033[0m" % str)


def strtoint(str):  # 16进制字符串转int 如"4040"/"0x4040"/"0X4040" = 16448
    value = 0
    rest_v = str.replace("0X", "").replace("0x", "")
    for index in range(len(rest_v)):
        value |= int(rest_v[index], 16) << ((len(rest_v) - index - 1) * 4)
    return value

def inttostr(vl,len): # 将int 转为字符串 如 0x3030 = 00
    if type(vl) != int:
        raise Exception(" type error")
    index = 0
    ret_t = ""
    while index < len:
        ret = 0xff & (vl >> index * 8)
        ret_t += chr(ret)
        index += 1;
    return ret_t

def str_to_hex(rest_v):
    value = 0
    for index in range(len(rest_v)):
        value |= ord(rest_v[index]) << ((len(rest_v) - index - 1) * 8)
    return value


def hex_to_str(s):
    len_t = len(s)
    if len_t % 2 != 0:
        return 0
    ret = ""
    for t in range(0, len_t / 2):
        ret += chr(int(s[2 * t:2 * t + 2], 16))
    return ret


def str_to_bin(s):
    return ' '.join([bin(ord(c)).replace('0b', '') for c in s])


def bin_to_str(s):
    return ''.join([chr(i) for i in [int(b, 2) for b in s.split(' ')]])


def getMacTemp():
    result = {}
    #waitForDocker()
    # 连续执行两次，取第二次
    rj_os_system("bcmcmd -t 1 \"show temp\" < /dev/null")
    ret, log = rj_os_system("bcmcmd -t 1 \"show temp\" < /dev/null")
    if ret:
        return False, result
    else:
        # 解析读取出来的信息
        logs = log.splitlines()
        for line in logs:
            if "average" in line:
                b = re.findall(r'\d+.\d+', line)
                result["average"] = b[0]
            elif "maximum" in line:
                b = re.findall(r'\d+.\d+', line)
                result["maximum"] = b[0]
    return True, result

def getMacTemp_sysfs(mactempconf):
    try:
        temp = -1000000
        temp_list = []
        mac_temp_loc = mactempconf.get("loc", [])
        mac_temp_flag = mactempconf.get("flag",None)
        if mac_temp_flag is not None: # 判断mac温度有效标志
            gettype = mac_temp_flag.get('gettype')
            okbit = mac_temp_flag.get('okbit')
            okval = mac_temp_flag.get('okval')
            if gettype == "io":
                io_addr = mac_temp_flag.get('io_addr')
                val = io_rd(io_addr)
                if val is None:
                    raise Exception("get mac_flag by io failed.")
            else:
                bus = mac_temp_flag.get('bus')
                loc = mac_temp_flag.get('loc')
                offset = mac_temp_flag.get('offset')
                ind, val = rji2cget(bus, loc, offset)
                if ind is not True:
                    raise Exception("get mac_flag by i2c failed.")
            val_t = (int(val,16) & (1<< okbit)) >> okbit
            if val_t != okval:
                raise Exception("mac_flag invalid, val_t:%d." % val_t)
        for loc in mac_temp_loc:
            temp_s = get_sysfs_value(loc)
            if isinstance(temp_s, str) and temp_s.startswith("ERR"):
                raise Exception("get mac temp error. loc:%s" % loc)
            temp_t = int(temp_s)
            if temp_t == -1000000:
                raise Exception("mac temp invalid.loc:%s" % loc)
            temp_list.append(temp_t)
        temp_list.sort(reverse=True)
        temp = temp_list[0]
    except Exception as e:
        return False, temp
    return True, temp

def restartDockerService(force=False):
    container_name = ["database","snmp","syncd","swss","dhcp_relay","radv","teamd","pmon"]
    ret, status = rj_os_system("docker ps")
    if ret == 0 :
        for tmpname in container_name:
            if (tmpname not in status):
                if (force == True):
                    rj_os_system("docker restart %s"%tmpname)
                else:
                    rj_os_system("systemctl restart %s"%tmpname)


def waitForDhcp(timeout):
    time_cnt = 0
    while True:
        try:
            ret, status = rj_os_system("systemctl status dhcp_relay.service")
            if (ret == 0 and "running" in status)  or "SUCCESS" in status:
                break
            else:
                sys.stdout.write(".")
                sys.stdout.flush()
                time_cnt = time_cnt + 1
                if time_cnt > timeout:
                    raise Exception("waitForDhcp timeout")
                time.sleep(1)
        except Exception as e:
            return False
    return True

def waitForSdk(sdk_fpath ,timeout):
    time_cnt = 0
    while True:
        try:
            if os.path.exists(sdk_fpath):
                break
            else:
                sys.stdout.write(".")
                sys.stdout.flush()
                time_cnt = time_cnt + 1
                if time_cnt > timeout:
                    raise Exception("waitForSdk timeout")
                time.sleep(1)
        except Exception as e:
            return False
    return True

def waitForDocker(need_restart=False,timeout=180):
    sdkcheck_params = STARTMODULE.get("sdkcheck",{})
    if sdkcheck_params.get("checktype") == "file": # 通过文件判断
        sdk_fpath = sdkcheck_params.get("sdk_fpath")
        return waitForSdk(sdk_fpath,timeout)
    return waitForDhcp(timeout)


def getTLV_BODY(type, productname):
    x = []
    temp_t = ""
    if type == TLV_CODE_MAC_BASE:
        arr = productname.split(':')
        for tt in arr:
            temp_t += chr(int(tt, 16))
    elif type == TLV_CODE_DEVICE_VERSION:
        temp_t = chr(productname)
    elif type == TLV_CODE_MAC_SIZE:
        temp_t = chr(productname >> 8) + chr(productname & 0x00ff)
    else:
        temp_t = productname
    x.append(chr(type))
    x.append(chr(len(temp_t)))
    for i in temp_t:
        x.append(i)
    return x


def _crc32(v):
    return '0x%08x' % (binascii.crc32(v) & 0xffffffff)  # 取crc32的八位数据 %x返回16进制


def printvalue(b):
    index = 0
    for i in range(0, len(b)):
        if index % 16 == 0:
            print " "
        print "%02x " % ord(b[i]),
        index += 1
    print "\n"


def generate_value(_t):
    ret = []
    for i in TLV_INFO_ID_STRING:
        ret.append(i)
    ret.append(chr(TLV_INFO_VERSION))
    ret.append(chr(TLV_INFO_LENGTH))
    ret.append(chr(TLV_INFO_LENGTH_VALUE))

    total_len = 0
    for key in _t:
        x = getTLV_BODY(key, _t[key])
        ret += x
        total_len += len(x)
    ret[10] = chr(total_len + 6)

    ret.append(chr(0xFE))
    ret.append(chr(0x04))
    s = _crc32(''.join(ret))
    for t in range(0, 4):
        ret.append(chr(int(s[2 * t + 2:2 * t + 4], 16)))
    totallen = len(ret)
    if (totallen < 256):
        for left_t in range(0, 256 - totallen):
            ret.append(chr(0x00))
    return (ret, True)


def getsyseeprombyId(id):  # 根据ID获取系统系统
    ret = get_sys_eeprom()
    for item in ret:
        if item["code"] == id:
            return item
    return None


def fac_init_cardidcheck():
    rest = getsyseeprombyId(TLV_CODE_RJ_CARID)  # 判断cardId是否相同
    if rest is None:
        print "需要烧写bin文件"
        return False
    else:
        rest_v = rest['value']
        value = strtoint(rest_v)
        if value == RUIJIE_CARDID:
            log_debug("板卡ID检测通过")
        else:
            log_debug("板卡ID有误")
            return False
    return True


def isValidMac(mac):
    if re.match(r"^\s*([0-9a-fA-F]{2,2}:){5,5}[0-9a-fA-F]{2,2}\s*$", mac):
        return True
    return False

# 网卡setmac


def util_setmac(eth, mac):
    rulefile = "/etc/udev/rules.d/70-persistent-net.rules"
    if isValidMac(mac) == False:
        return False, "MAC非法"
    cmd = "ethtool -e %s | grep 0x0010 | awk '{print \"0x\"$13$12$15$14}'" % eth
    ret, log = rj_os_system(cmd)
    log_debug(log)
    magic = ""
    if ret == 0 and len(log):
        magic = log
    macs = mac.upper().split(":")

    # 暂时把本地的ETH0改为setmac后的值
    ifconfigcmd = "ifconfig eth0 hw ether %s" % mac
    log_debug(ifconfigcmd)
    ret, status = rj_os_system(ifconfigcmd)
    if ret:
        raise SETMACException("软件设置网卡MAC出错")
    index = 0
    for item in macs:
        cmd = "ethtool -E %s magic %s offset %d value 0x%s" % (
            eth, magic, index, item)
        log_debug(cmd)
        index += 1
        ret, log = rj_os_system(cmd)
        if ret != 0:
            raise SETMACException("设置硬件网卡MAC出错")
    # 取设置后的返回值
    cmd_t = "ethtool -e eth0 offset 0 length 6"
    ret, log = rj_os_system(cmd_t)
    m = re.split(':', log)[-1].strip().upper()
    mac_result = m.upper().split(" ")

    for ind, s in enumerate(macs):
        if s != mac_result[ind]:
            RJPRINTERR("MAC比较出错")
    if os.path.exists(rulefile):
        os.remove(rulefile)  # 删除文件
    print "MGMT MAC【%s】" % mac
    return True


def getInputCheck(tips):
    str = raw_input(tips)
    if astrcmp(str, "y") or astrcmp(str, "ye") or astrcmp(str, "yes") or astrcmp(str, ""):
        return True
    else:
        return False

def getrawch():
  fd = sys.stdin.fileno()
  old_settings = termios.tcgetattr(fd)
  try:
    tty.setraw(sys.stdin.fileno())
    ch = sys.stdin.read(1)
  finally:
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
  return ch

def upper_input(tips):
    sys.stdout.write(tips)
    sys.stdout.flush()
    passwd = []
    while True:
        ch = getrawch().upper()
        if ch == "\r" or ch == "\n":
          print
          return "".join(passwd)
        elif ch == '\b' or ord(ch) == 127:
            if passwd:
                del passwd[-1]
                sys.stdout.write('\b \b')
        else:
          sys.stdout.write(ch)
          passwd.append(ch)

def changeTypeValue(_value, type1, tips, example):
    if type1 == TLV_CODE_PRODUCT_NAME:
        while True:
            print "请确认 (1)前后进风/(2)后前进风:",
            option = raw_input()
            if option == "1":
                _value[type1] = example + "-F-RJ"
                print "确认该产品为前后进风设备,产品名称:%s"%_value[type1]
                break
            elif option == "2":
                _value[type1] = example + "-R-RJ"
                print "确认该产品为后前进风设备,产品名称:%s"%_value[type1]
                break
            else:
                print "输入错误,请认真核对"
        return True
    print "请输入【%s】如(%s):" % (tips, example),
    name = upper_input("")
    if type1 == TLV_CODE_MAC_BASE:
        if len(name) != 12:
            raise SETMACException("MAC地址长度不对,请认真核对")
        release_mac = ""
        for i in range(len(name) / 2):
            if i == 0:
                release_mac += name[i * 2:i * 2 + 2]
            else:
                release_mac += ":" + name[i * 2:i * 2 + 2]
        if isValidMac(release_mac) == True:
            _value[type1] = release_mac
        else:
            raise SETMACException("MAC地址非法,请认真核对")
    elif type1 == TLV_CODE_DEVICE_VERSION:
        if name.isdigit():
            _value[type1] = int(name)
        else:
            raise SETMACException("版本号非数字,请认真核对")
    elif type1 == TLV_CODE_MAC_SIZE:
        if name.isdigit():
            _value[type1] = int(name, 16)
        else:
            raise SETMACException("版本号非数字,请认真核对")
    elif type1 == TLV_CODE_SERIAL_NUMBER:
        if name.isalnum() == False:
            raise SETMACException("序列号非法字符串,请认真核对")
        elif len(name) != 13:
            raise SETMACException("序列号长度不对,请认真核对")
        else:
            _value[type1] = name
    elif type1 == TLV_CODE_VENDOR_EXT:
        _value[type1] = name
    else:
        _value[type1] = name
    return True
# 不论大小比较字符串


def astrcmp(str1, str2):
    return str1.lower() == str2.lower()


def generate_ext(cardid):
    s = "%08x" % cardid
    ret = ""
    for t in range(0, 4):
        ret += chr(int(s[2 * t:2 * t + 2], 16))
    ret = chr(0x01) + chr(len(ret)) + ret
    return ret


def rji2cget(bus, devno, address):
    command_line = "i2cget -f -y %d 0x%02x 0x%02x " % (bus, devno, address)
    retrytime = 6
    ret_t = ""
    for i in range(retrytime):
        ret, ret_t = rj_os_system(command_line)
        if ret == 0:
            return True, ret_t
        time.sleep(0.1)
    return False, ret_t


def rji2cset(bus, devno, address, byte):
    command_line = "i2cset -f -y %d 0x%02x 0x%02x 0x%02x" % (
        bus, devno, address, byte)
    retrytime = 6
    ret_t = ""
    for i in range(retrytime):
        ret, ret_t = rj_os_system(command_line)
        if ret == 0:
            return True, ret_t
    return False, ret_t

def rjpcird(pcibus , slot , fn, bar,  offset):
    '''read pci register'''
    if offset % 4 != 0:
        return
    filename = "/sys/bus/pci/devices/0000:%02x:%02x.%x/resource%d" % (int(pcibus), int(slot), int(fn), int(bar))
    file = open(filename, "r+")
    size = os.path.getsize(filename)
    data = mmap.mmap(file.fileno(), size)
    result = data[offset: offset + 4]
    s = result[::-1]
    val = 0
    for i in range(0, len(s)):
        val = val << 8  | ord(s[i])
    return "0x%08x" % val


def rjpciwr(pcibus , slot ,fn, bar, offset, data):
    '''write pci register'''
    ret = inttostr(data, 4)
    filename = "/sys/bus/pci/devices/0000:%02x:%02x.%x/resource%d" % (int(pcibus), int(slot), int(fn), int(bar))
    file = open(filename, "r+")
    size = os.path.getsize(filename)
    data = mmap.mmap(file.fileno(), size)
    data[offset: offset + 4] = ret
    result = data[offset: offset + 4]
    s = result[::-1]
    val = 0
    for i in range(0, len(s)):
        val = val << 8  | ord(s[i])
    data.close()

def rjsysset(location, value):
    command_line = "echo 0x%02x > %s" % (value, location)
    retrytime = 6
    ret_t = ""
    for i in range(retrytime):
        ret, ret_t = rj_os_system(command_line)
        if ret == 0:
            return True, ret_t
    return False, ret_t


def rji2cgetWord(bus, devno, address):
    command_line = "i2cget -f -y %d 0x%02x 0x%02x w" % (bus, devno, address)
    retrytime = 3
    ret_t = ""
    for i in range(retrytime):
        ret, ret_t = rj_os_system(command_line)
        if ret == 0:
            return True, ret_t
    return False, ret_t


def rji2csetWord(bus, devno, address, byte):
    command_line = "i2cset -f -y %d 0x%02x 0x%02x 0x%x w" % (
        bus, devno, address, byte)
    rj_os_system(command_line)


def fan_setmac():
    rji2cset(FAN_PROTECT["bus"], FAN_PROTECT["devno"],
             FAN_PROTECT["addr"], FAN_PROTECT["open"])
    rji2cset(FAN_PROTECT["bus"], FAN_PROTECT["devno"],
             FAN_PROTECT["addr"], FAN_PROTECT["close"])


def checkfansninput(fan_sn, fansntemp):
    if fan_sn in fansntemp:
        RJPRINTERR("存在相同序列号，请重新输入！")
        return False
    if(len(fan_sn) != 13):
        RJPRINTERR("序列号长度错误，请重新输入！")
        return False
    return True

# 判断输入的硬件版本号


def checkfanhwinput(hw):
    if len(hw) != 4:
        RJPRINTERR("硬件版本号长度不正确,请重新输入！")
        return False
    if hw.find(".") != 1:
        RJPRINTERR("硬件版本号不正确,请重新输入！")
        return False
    return True


def util_show_fanse2(fans):
    formatstr = "%-8s  %-20s  %-20s  %-20s %-20s"
    print formatstr % ("id", "名称", "硬件版本号", "序列号", "时间")
    print formatstr % ("------", "---------------", "---------------", "---------------", "----")
    for fan in fans:
        # print fan.dstatus
        if fan.dstatus < 0:
            print "%-8s" % ("风扇%d" % (fans.index(fan) + 1)),
            RJPRINTERR("  解析e2出错")
        else:
            print formatstr % ("风扇%d" % (fans.index(fan) + 1), fan.typename.replace(chr(0x00), ""),
                               fan.typehwinfo.replace(chr(0x00), ""), fan.typesn.replace(chr(0x00), ""), fan.fandecodetime)


def get_fane2_sysfs(bus, loc):
    rg_fan_e2 = "%d-%04x/fan" % (bus, loc)
    eeprom = get_sysfs_value(rg_fan_e2)
    return eeprom


def util_show_fane2():
    ret = sorted(I2CUTIL.getvaluefromdevice("rg_fan"))    
    if len(ret) <=0:
        return None
    fans = []
    for index in range(len(ret)):
        t1 = (int(round(time.time() * 1000)))
        eeprom = get_fane2_sysfs(ret[index]["bus"], ret[index]["loc"])
        t2 = (int(round(time.time() * 1000)))
        fane2 = fan_tlv()
        fane2.fandecodetime = t2 - t1
        fane2.decode(eeprom)
        fans.append(fane2)
    util_show_fanse2(fans)


def getPid(name):
    ret = []
    for dirname in os.listdir('/proc'):
        if dirname == 'curproc':
            continue
        try:
            with open('/proc/{}/cmdline'.format(dirname), mode='rb') as fd:
                content = fd.read()
        except Exception:
            continue
        if name in content:
            ret.append(dirname)
    return ret

def fac_fans_setmac_tlv(ret):
    if len(ret) <=0:
        return None
    fans = []
    fansntemp = []
    for index in range(len(ret)):
        item = ret[index]
        log_debug(item)
        eeprom = get_fane2_sysfs(item["bus"], item["loc"])
        fane2 = fan_tlv()
        fane2.decode(eeprom)
        fane2.fanbus = item["bus"]
        fane2.fanloc = item["loc"]
        log_debug("decode eeprom success")

        print "风扇【%d】-【%s】setmac" % ((index + 1), FANS_DEF[fane2.typedevtype])
        while True:
            print "请输入[%s]:" % "序列号",
            fan_sn = raw_input()
            if checkfansninput(fan_sn, fansntemp) == False:
                continue
            fansntemp.append(fan_sn)
            fan_sn = fan_sn + chr(0x00)
            fane2.typesn = fan_sn + chr(0x00)
            break
        while True:
            print "请输入[%s]:" % "硬件版本号",
            hwinfo = raw_input()
            if checkfanhwinput(hwinfo) == False:
                continue
            fan_hwinfo = hwinfo + chr(0x00)
            fane2.typehwinfo = fan_hwinfo + chr(0x00)
            break
        log_debug(fane2.typedevtype)
        fane2.typename = FANS_DEF[fane2.typedevtype] + chr(0x00)
        fans.append(fane2)
        print "\n"
    print "\n*******************************\n"

    util_show_fanse2(fans)
    if getInputCheck("确认是否输入正确（Yes/No):") == True:
        for fan in fans:
            log_debug("ouput fan")
            fac_fan_setmac(fan)
    else:
        print "setmac退出"
        return False


def fac_fan_setmac_fru(ret):
    fans =  FRULISTS.get('fans')
    
    fanfrus = {}
    newfrus = {}
    
    #getmsg
    try:
        for fan in fans:
            print "===============%s ================getmessage" % fan.get('name')
            eeprom = getsysvalue(I2CUTIL.getE2File(fan.get('bus'), fan.get('loc')))
            fru = ipmifru()
            fru.decodeBin(eeprom)
            fanfrus[fan.get('name')] = fru
    except Exception as e:
        print str(e)
        return False
    
    #setmsg
    for fan in fans:
        print "===============%s ================setmac" % fan.get('name')
        fruold = fanfrus.get(fan.get('name'))
        newfru = getInputSetmac(fruold)
        newfru.recalcute()
        newfrus[fan.get('name')] = newfru
    #writemsg
    for fan in fans:
        print "===============%s ================writeToE2" % fan.get('name')
        ret_t = newfrus.get(fan.get('name'))
        I2CUTIL.openFanE2Protect()
        I2CUTIL.writeToFanE2(fan.get('bus'), fan.get('loc'), ret_t.bindata)
        I2CUTIL.closeFanE2Protect()
    #check
    try:
        for fan in fans:
            print "===============%s ================getmessage" % fan.get('name')
            eeprom = getsysvalue(I2CUTIL.getE2File(fan.get('bus'), fan.get('loc')))
            fru = ipmifru()
            fru.decodeBin(eeprom)
    except Exception as e:
        print str(e)
        return False
    return True

def fac_fans_setmac():
    ret =  I2CUTIL.getvaluefromdevice("rg_fan")
    if ret is not None and len(ret) > 0:
        return fac_fans_setmac_tlv(ret)
    fans =  FRULISTS.get('fans', None)
    if fans is not None and len(fans)>0:
        return fac_fan_setmac_fru(ret)
    return False

def fac_fan_setmac(item):
    I2CUTIL.openFanE2Protect()
    I2CUTIL.writeToFanE2(item.fanbus, item.fanloc, item.generate_fan_value())
    I2CUTIL.closeFanE2Protect()

def writeToEEprom(rst_arr):
    dealtype = E2_PROTECT.get('gettype',None)
    if dealtype is None:
        rji2cset(E2_PROTECT["bus"], E2_PROTECT["devno"],
                 E2_PROTECT["addr"], E2_PROTECT["open"])
    elif dealtype == "io":
        io_wr(E2_PROTECT["io_addr"], E2_PROTECT["open"])
    index = 0
    for item in rst_arr:
        rji2cset(E2_LOC["bus"], E2_LOC["devno"], index, ord(item))
        index += 1
    
    if dealtype is None:
        rji2cset(E2_PROTECT["bus"], E2_PROTECT["devno"],
                 E2_PROTECT["addr"], E2_PROTECT["close"])
    elif dealtype == "io":
        io_wr(E2_PROTECT["io_addr"], E2_PROTECT["close"])
    # 最后处理系统驱动
    os.system("rmmod at24 ")
    os.system("modprobe at24 ")
    os.system("rm -f /var/cache/sonic/decode-syseeprom/syseeprom_cache")


def get_local_eth0_mac():
    cmd = "ifconfig eth0 |grep HWaddr"
    print rj_os_system(cmd)

def getonieversion():
    if not os.path.isfile('/host/machine.conf'):
        return ""
    machine_vars = {}
    with open('/host/machine.conf') as machine_file:
        for line in machine_file:
            tokens = line.split('=')
            if len(tokens) < 2:
                continue
            machine_vars[tokens[0]] = tokens[1].strip()
    return machine_vars.get("onie_version")

def createbmcMac(cpumac , num = 2):
    bcmvalue =  strtoint(cpumac[cpumac.rindex(":")+ 1:len(cpumac)]) + num
    # bmcmac = 
    t = cpumac.split(":")
    t[5] = "%02x" %  bcmvalue
    bmcmac = ":".join(t)
    return bmcmac.upper()


def fac_board_setmac():
    _value = {}
    # 默认赋值
    _value[TLV_CODE_VENDOR_EXT] = generate_ext(RUIJIE_CARDID)  # 生成锐捷特有的id
    _value[TLV_CODE_PRODUCT_NAME] = RUIJIE_PRODUCTNAME
    _value[TLV_CODE_PART_NUMBER]    = RUIJIE_PART_NUMBER
    _value[TLV_CODE_LABEL_REVISION] = RUIJIE_LABEL_REVISION
    _value[TLV_CODE_PLATFORM_NAME]  = platform
    _value[TLV_CODE_ONIE_VERSION]   = getonieversion()
    _value[TLV_CODE_MAC_SIZE]       = RUIJIE_MAC_SIZE
    _value[TLV_CODE_MANUF_NAME]     = RUIJIE_MANUF_NAME
    _value[TLV_CODE_MANUF_COUNTRY]  = RUIJIE_MANUF_COUNTRY
    _value[TLV_CODE_VENDOR_NAME]    = RUIJIE_VENDOR_NAME
    _value[TLV_CODE_DIAG_VERSION]   = RUIJIE_DIAG_VERSION
    _value[TLV_CODE_SERVICE_TAG]    = RUIJIE_SERVICE_TAG
    try:
        if 0x00004052 == RUIJIE_CARDID:
            _value[TLV_CODE_PRODUCT_NAME] = RUIJIE_PRODUCTNAME + "-RJ"
        elif 0x00004051 == RUIJIE_CARDID or 0x00004050 == RUIJIE_CARDID:
            changeTypeValue(_value, TLV_CODE_PRODUCT_NAME,
                        "产品名称",RUIJIE_PRODUCTNAME)

        changeTypeValue(_value, TLV_CODE_SERIAL_NUMBER,
                        "SN", "0000000000000")  # 添加序列号
        changeTypeValue(_value, TLV_CODE_DEVICE_VERSION,
                        "硬件版本号", "101")  # 硬件版本号
        changeTypeValue(_value, TLV_CODE_MAC_BASE,
                        "MAC地址", "58696cfb2108")  # MAC地址
        _value[TLV_CODE_MANUF_DATE] = time.strftime(
            '%m/%d/%Y %H:%M:%S', time.localtime())  # 自动添加setmac时间
        rst, ret = generate_value(_value)
        if util_setmac("eth0", _value[TLV_CODE_MAC_BASE]) == True:  # 设置网卡IP
            writeToEEprom(rst)  # 写值到e2中
            #设置BMC MAC
            if FACTESTMODULE.has_key("bmcsetmac") and FACTESTMODULE['bmcsetmac'] == 1:
                bmcmac = createbmcMac(_value[TLV_CODE_MAC_BASE])
                if ipmi_set_mac(bmcmac) == True:
                    print("BMC  MAC【%s】"%bmcmac)
                else:
                    print("SET BMC MAC FAILED")
                    return False
        else:
            return False
    except SETMACException as e:
        #print e
        RJPRINTERR("\n\n%s\n\n" % e)
        return False
    except ValueError as e:
        return False
    return True


def ipmi_set_mac(mac):
    macs = mac.split(":")
    cmdinit = "ipmitool raw 0x0c 0x01 0x01 0xc2 0x00"
    cmdset = "ipmitool raw 0x0c 0x01 0x01 0x05"
    for ind in range(len(macs)):
        cmdset += " 0x%02x" % int(macs[ind], 16)
    rj_os_system(cmdinit)
    ret, status = rj_os_system(cmdset)
    if ret:
        RJPRINTERR("\n\n%s\n\n" % status)
        return False
    return True


def getInputValue(title, tips):
    print "请输入【%s】如(%s):" % (title, tips),
    name = raw_input()

    return name


def bmc_setmac():
    tips = "BMC MAC"
    print "请输入你要改的值[%s]:" % tips,
    name = raw_input()
    if len(name) != 12:
        RJPRINTERR("\nMAC地址非法,请重新输入\n")
        return False
    release_mac = ""
    for i in range(len(name) / 2):
        if i == 0:
            release_mac += name[i * 2:i * 2 + 2]
        else:
            release_mac += ":" + name[i * 2:i * 2 + 2]
    if isValidMac(release_mac) == True:
        if ipmi_set_mac(release_mac) == True:
            return True
    else:
        RJPRINTERR("\nMAC地址非法,请重新输入\n")
    return False


def closeProtocol():
    # 关闭LLDP
    log_info("关闭LLDP")
    sys.stdout.write(".")
    sys.stdout.flush()
    rj_os_system("systemctl stop lldp.service")
    log_info("关闭网关边界服务")
    sys.stdout.write(".")
    sys.stdout.flush()
    rj_os_system("systemctl stop bgp.service")
    log_info("关闭生成树")
    sys.stdout.write(".")
    sys.stdout.flush()
    #ret, status = rj_os_system('bcmcmd "port ce,xe stp=disable"')

# 检测SDK内存 必须为256M


def checkSdkMem():
    ind = 0
    file_data = ""
    with open(file_name, "r") as f:
        for line in f:
            if "dmasize=16M" in line:
                line = line.replace("dmasize=16M", "dmasize=256M")
                ind = -1
            file_data += line
    if ind == 0:
        return
    with open(file_name, "w") as f:
        f.write(file_data)
    print "修订SDK内存为256，需要重启生效"
    rj_os_system("sync")
    rj_os_system("reboot")

##########################################################################
# 窗口接收一个字符设置
##########################################################################


def getch(msg):
    ret = ""
    fd = sys.stdin.fileno()
    old_ttyinfo = termios.tcgetattr(fd)
    new_ttyinfo = old_ttyinfo[:]
    new_ttyinfo[3] &= ~termios.ICANON
    new_ttyinfo[3] &= ~termios.ECHO
    sys.stdout.write(msg)
    sys.stdout.flush()
    try:
        termios.tcsetattr(fd, termios.TCSANOW, new_ttyinfo)
        ret = os.read(fd, 1)
    finally:
        # print "try to setting"
        termios.tcsetattr(fd, termios.TCSANOW, old_ttyinfo)
    return ret

def get_raw_input():
    ret=""
    fd=sys.stdin.fileno()
    old_ttyinfo=termios.tcgetattr(fd)
    new_ttyinfo=old_ttyinfo[:]
    new_ttyinfo[3] &= ~termios.ICANON
    new_ttyinfo[3] &= ~termios.ECHO
    try:
        termios.tcsetattr(fd,termios.TCSANOW,new_ttyinfo)
        ret=raw_input("")
    except Exception as e:
        print e
    finally:
        termios.tcsetattr(fd,termios.TCSANOW,old_ttyinfo)
    return ret


def getsysvalue(location):
    retval = None
    mb_reg_file = location
    if (not os.path.isfile(mb_reg_file)):
        print mb_reg_file,  'not found !'
        return retval
    try:
        if (not os.path.isfile(mb_reg_file)):
            print mb_reg_file,  'not found !'
            return retval
        with open(mb_reg_file, 'r') as fd:
            retval = fd.read()
    except Exception as error:
        log_error("Unable to open " + mb_reg_file + "file !")
    retval = retval.rstrip('\r\n')
    retval = retval.lstrip(" ")
    #log_debug(retval)
    return retval

# 获取文件值


def get_pmc_register(reg_name):
    retval = 'ERR'
    mb_reg_file = MAILBOX_DIR + reg_name
    filepath = glob.glob(mb_reg_file)
    if(len(filepath) == 0):
        return "%s %s  notfound"% (retval , mb_reg_file)
    mb_reg_file = filepath[0]        #如果找到多个匹配的路径，默认取第一个匹配的路径。
    if (not os.path.isfile(mb_reg_file)):
        return "%s %s  notfound"% (retval , mb_reg_file)
    try:
        with open(mb_reg_file, 'r') as fd:
            retval = fd.read()
    except Exception as error:
        pass
    retval = retval.rstrip('\r\n')
    retval = retval.lstrip(" ")
    return retval

# 按锐捷规则解析EEPROM


def decoder(s, t):
    if ord(t[0]) == TLV_CODE_PRODUCT_NAME:
        name = "Product Name"
        value = str(t[2:2 + ord(t[1])])
    elif ord(t[0]) == TLV_CODE_PART_NUMBER:
        name = "Part Number"
        value = t[2:2 + ord(t[1])]
    elif ord(t[0]) == TLV_CODE_SERIAL_NUMBER:
        name = "Serial Number"
        value = t[2:2 + ord(t[1])]
    elif ord(t[0]) == TLV_CODE_MAC_BASE:
        name = "Base MAC Address"
        value = ":".join([binascii.b2a_hex(T) for T in t[2:8]]).upper()
    elif ord(t[0]) == TLV_CODE_MANUF_DATE:
        name = "Manufacture Date"
        value = t[2:2 + ord(t[1])]
    elif ord(t[0]) == TLV_CODE_DEVICE_VERSION:
        name = "Device Version"
        value = str(ord(t[2]))
    elif ord(t[0]) == TLV_CODE_LABEL_REVISION:
        name = "Label Revision"
        value = t[2:2 + ord(t[1])]
    elif ord(t[0]) == TLV_CODE_PLATFORM_NAME:
        name = "Platform Name"
        value = t[2:2 + ord(t[1])]
    elif ord(t[0]) == TLV_CODE_ONIE_VERSION:
        name = "ONIE Version"
        value = t[2:2 + ord(t[1])]
    elif ord(t[0]) == TLV_CODE_MAC_SIZE:
        name = "MAC Addresses"
        value = str((ord(t[2]) << 8) | ord(t[3]))
    elif ord(t[0]) == TLV_CODE_MANUF_NAME:
        name = "Manufacturer"
        value = t[2:2 + ord(t[1])]
    elif ord(t[0]) == TLV_CODE_MANUF_COUNTRY:
        name = "Manufacture Country"
        value = t[2:2 + ord(t[1])]
    elif ord(t[0]) == TLV_CODE_VENDOR_NAME:
        name = "Vendor Name"
        value = t[2:2 + ord(t[1])]
    elif ord(t[0]) == TLV_CODE_DIAG_VERSION:
        name = "Diag Version"
        value = t[2:2 + ord(t[1])]
    elif ord(t[0]) == TLV_CODE_SERVICE_TAG:
        name = "Service Tag"
        value = t[2:2 + ord(t[1])]
    elif ord(t[0]) == TLV_CODE_VENDOR_EXT:
        name = "Vendor Extension"
        value = ""
        if _TLV_DISPLAY_VENDOR_EXT:
            value = t[2:2 + ord(t[1])]
    elif ord(t[0]) == TLV_CODE_CRC_32 and len(t) == 6:
        name = "CRC-32"
        value = "0x%08X" % (((ord(t[2]) << 24) | (
            ord(t[3]) << 16) | (ord(t[4]) << 8) | ord(t[5])),)
    elif ord(t[0]) == TLV_CODE_RJ_CARID:
        name = "rj_cardid"
        value = ""
        for c in t[2:2 + ord(t[1])]:
            value += "%02X" % (ord(c),)
    else:
        name = "Unknown"
        value = ""
        for c in t[2:2 + ord(t[1])]:
            value += "0x%02X " % (ord(c),)
    return {"name": name, "code": ord(t[0]), "value": value}


def decode_eeprom(e):
    total_len = (ord(e[9]) << 8) | ord(e[10])
    tlv_index = _TLV_INFO_HDR_LEN
    tlv_end = _TLV_INFO_HDR_LEN + total_len
    ret = []
    while (tlv_index + 2) < len(e) and tlv_index < tlv_end:
        rt = decoder(None, e[tlv_index:tlv_index + 2 + ord(e[tlv_index + 1])])
        ret.append(rt)
        if ord(e[tlv_index]) == TLV_CODE_CRC_32:
            break
        tlv_index += ord(e[tlv_index + 1]) + 2
    for item in ret:
        if item['code'] == TLV_CODE_VENDOR_EXT:
            rt = decoder(None, item["value"]
                         [0: 0 + 2 + ord(item["value"][0 + 1])])
            ret.append(rt)
    return ret


def get_sys_eeprom():
    eeprom = get_sysfs_value(rg_eeprom)
    return decode_eeprom(eeprom)

# 获取板卡ID
def getCardId():
    ret = get_sys_eeprom()
    for item in ret:
        if item['code'] == TLV_CODE_RJ_CARID:
            return item.get('value',None)
    return None

# ====================================
# 执行shell命令
# ====================================
def rj_os_system(cmd):
    status, output = commands.getstatusoutput(cmd)
    return status, output

###########################################
# 通过DMI命令获取系统的内存插槽和内存数
###########################################
def getsysmeminfo():
    ret, log = rj_os_system("which dmidecode ")
    if ret != 0 or len(log) <= 0:
        error = "cmd find dmidecode"
        return False, error
    cmd = log + "|grep -P -A5 \"Memory\s+Device\"|grep Size|grep -v Range"
    # 先获取总数
    result = []
    ret1, log1 = rj_os_system(cmd)
    if ret1 == 0 and len(log1):
        log1 = log1.lstrip()
        arr = log1.split("\n")
        #total = len(arr)  # 总共的插槽数
        for i in range(len(arr)):
            val = re.sub("\D", "", arr[i])
            if val == "":
                val = arr[i].lstrip()
                val = re.sub('Size:', '', val).lstrip()
            # print val
            result.append({"slot": i + 1, "size": val})
        return True, result
    return False, "error"

###########################################
# 通过DMI命令获取系统的内存插槽和内存数
# 返回值包含多个数组
###########################################
def getsysmeminfo_detail():
    ret, log = rj_os_system("which dmidecode ")
    if ret != 0 or len(log) <= 0:
        error = "cmd find dmidecode"
        return False, error
    cmd = log + " -t 17 | grep  -A21 \"Memory Device\""  # 17
    # 先获取总数
    ret1, log1 = rj_os_system(cmd)
    if ret1 != 0 or len(log1) <= 0:
        return False, "命令执行出错[%s]" % cmd
    result_t = log1.split("--")
    mem_rets = []
    for item in result_t:
        its = item.replace("\t", "").strip().split("\n")
        ret = {}
        for it in its:
            if ":" in it:
                key = it.split(":")[0].lstrip()
                value = it.split(":")[1].lstrip()
                ret[key] = value
        mem_rets.append(ret)
    return True, mem_rets


###########################################
# 通过DMI命令获取系统的BIOS信息
###########################################
def getDmiSysByType(type_t):
    ret, log = rj_os_system("which dmidecode ")
    if ret != 0 or len(log) <= 0:
        error = "cmd find dmidecode"
        return False, error
    cmd = log + " -t %s" % type_t
    # 先获取总数
    ret1, log1 = rj_os_system(cmd)
    if ret1 != 0 or len(log1) <= 0:
        return False, "命令执行出错[%s]" % cmd
    its = log1.replace("\t", "").strip().split("\n")
    ret = {}
    for it in its:
        if ":" in it:
            key = it.split(":")[0].lstrip()
            value = it.split(":")[1].lstrip()
            ret[key] = value
    return True, ret


def gethwsys():
    return getDmiSysByType(1)

###########################################
# 通过DMI命令获取系统的BIOS信息


def getsysbios():
    return getDmiSysByType(0)


def searchDirByName(name, dir):
    result = []
    try:
        files = os.listdir(dir)
        for file in files:
            if name in file:
                result.append(os.path.join(dir, file))
    except Exception as e:
        pass
    return result


def getUsbLocation():
    dir = "/sys/block/"
    spect = "sd"
    usbpath = ""
    result = searchDirByName(spect, dir)
    if len(result) <= 0:
        return False
    for item in result:
        with open(os.path.join(item, "removable"), 'r') as fd:
            value = fd.read()
            if value.strip() == "1":  # 表示找到U盘
                usbpath = item
                break
    if usbpath == "":  # 没找到U盘
        log_debug("no usb found")
        return False, usbpath
    return True, usbpath

# 判断USB文件 查找
def getusbinfo():
    ret, path = getUsbLocation()
    if ret == False:
        return False, "not usb exists"
    str = os.path.join(path, "size")
    ret, value = getfilevalue(str)
    if ret == True:
        return True, {"id": os.path.basename(path), "size": float(value) * 512 / 1024 / 1024 / 1024}
    else:
        return False, "Err"

def get_cpu_info():
    cmd = "cat /proc/cpuinfo |grep processor -A18"  # 17

    ret, log1 = rj_os_system(cmd)
    if ret != 0 or len(log1) <= 0:
        return False, "命令执行出错[%s]" % cmd
    result_t = log1.split("--")
    mem_rets = []
    for item in result_t:
        its = item.replace("\t", "").strip().split("\n")
        ret = {}
        for it in its:
            if ":" in it:
                key = it.split(":")[0].lstrip()
                value = it.split(":")[1].lstrip()
                ret[key] = value
        mem_rets.append(ret)
    return True, mem_rets
#  读取文件内容
def get_version_config_info(attr_key, file_name=None):
    if file_name is None:
        version_conf_filename = "/root/version.json"
    else:
        version_conf_filename = file_name
    if not os.path.isfile(version_conf_filename):
        return None
    with open(version_conf_filename) as rjconf_file:
        for line in rjconf_file:
            tokens = line.split('=')
            if len(tokens) < 2:
                continue
            if tokens[0] == attr_key:
                return tokens[1].strip()
    return None


def io_rd(reg_addr, len =1):
    u'''io读'''
    try: 
        regaddr = 0
        if type(reg_addr) == int:
            regaddr = reg_addr
        else:
            regaddr = int(reg_addr, 16)
        devfile = "/dev/port"
        fd = os.open(devfile, os.O_RDWR|os.O_CREAT)
        os.lseek(fd, regaddr, os.SEEK_SET)
        str = os.read(fd, len)
        return "".join(["%02x"% ord(item) for item in str])
    except ValueError: 
        return None
    except Exception as e:
        print e
        return None
    finally:
        os.close(fd)
    

def io_wr(reg_addr, reg_data):
    u'''io写'''
    try:
        regdata  = 0
        regaddr  = 0
        if type(reg_addr) == int:
            regaddr = reg_addr
        else:
            regaddr = int(reg_addr, 16)
        if type(reg_data) == int:
            regdata = reg_data
        else:
            regdata = int(reg_data, 16)
        devfile = "/dev/port"
        fd = os.open(devfile, os.O_RDWR|os.O_CREAT)
        os.lseek(fd, regaddr, os.SEEK_SET)
        os.write(fd, chr(regdata))
        return True
    except ValueError as e:
        print e
        return False
    except Exception as e:
        print e
        return False
    finally:
        os.close(fd)
    
