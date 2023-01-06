#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys
import click
import os
import subprocess
import syslog
import json
import mmap
import time
import device_i2c as di
import re
import traceback
from ragileutil import *
from click_default_group import DefaultGroup
from tabulate import tabulate
import unicodedata
from eepromutil.fru import *
# from rest.rest import DeviceMessage
# from rest.rest import BMCMessage

def restful_get(url):
    if url == "" or len(url) <=0:
        print ("invalid url")
        return
    from rest.rest import DeviceMessage, BMCMessage
    bmc = BMCMessage()
    value = bmc.getBmcValue(url)
    json_dicts=json.dumps(value,indent=4)
    return str(json_dicts)

def wide_chars(s):
    if isinstance(s, str):
        s = s.decode('utf-8')
    return sum(unicodedata.east_asian_width(x) in ('F', 'W') for x in s)

try:
    from port import PortTest,PortPrbsTest
    import ConfigParser as configparser
    
except ImportError:
    pass

stopFanctrol           = di.stopFanctrol
startFanctrol          = di.startFanctrol

GRTD_BROADCAST_RETRY_SLEEP_TIME  = 3

SYSLOG_IDENTIFIER = "GRTD_TEST"

# ========================== Syslog wrappers ==========================
def log_info(msg, also_print_to_console=False):
    # msg = msg.decode('utf-8').encode('gb2312')
    syslog.openlog(SYSLOG_IDENTIFIER)
    syslog.syslog(syslog.LOG_INFO, msg)
    syslog.closelog()

    if also_print_to_console:
        click.echo(msg)

def log_debug(msg, also_print_to_console=False):
    try:
        # msg = msg.decode('utf-8').encode('gb2312')
        syslog.openlog(SYSLOG_IDENTIFIER)
        syslog.syslog(syslog.LOG_DEBUG, msg)
        syslog.closelog()

        if also_print_to_console:
            click.echo(msg)
    except Exception as e:
        pass

def log_warning(msg, also_print_to_console=False):
    # msg = msg.decode('utf-8').encode('gb2312')
    syslog.openlog(SYSLOG_IDENTIFIER)
    syslog.syslog(syslog.LOG_WARNING, msg)
    syslog.closelog()

    if also_print_to_console:
        click.echo(msg)


def log_error(msg, also_print_to_console=False):
    # msg = msg.decode('utf-8').encode('gb2312')
    syslog.openlog(SYSLOG_IDENTIFIER)
    syslog.syslog(syslog.LOG_ERR, msg)
    syslog.closelog()

    if also_print_to_console:
        click.echo(msg)

# Print the output according to the format
def port_totalprint(arr, tips):
    if len(arr) <= 0:
        return 
    print("%-20s" % tips ,)
    for index in range(len(arr)):
        print ("%03d" % arr[index] ,)
        if (index + 1) % 8 == 0:
            print ("")
            print (" " * 20,)
    print ("")

# Port frame
def test_port_portframe():
    try:
        from port import PortScene, hsdk_check
        if (hsdk_check()):
            portscene = PortScene()
            return portscene.port_frame_test(port_list=[])
        else:
            return test_port_portframe_old()
    except Exception as except_result:
        msg = traceback.format_exc()
        print("Exception_info:\n%s" % msg)

# Original logic of sending and receiving frames on the port
def test_port_portframe_old():
    framenum = 10000
    len_t = len(PortTest().bcm_ports)
    upports = []
    ret_t = 0
    errt_t = []
    testerror ={}
    caseerror=[]
    testerror["name"] = "端口收发帧"
    successport=[]
    updownerrport=[]
    errorport = []
    try:
        # All values UP Port PRBS
        for i in range(len_t):
            status = PortTest().get_port_status(i + 1)
            if status == "up":
                upports.append(i + 1)
        PortTest().init_port_cpu()
        PortTest().clear_port_packets()
        for i in range(len(PortTest().bcm_ports)):
            if (i + 1) in upports :
                PortTest().start_send_port_packets(i + 1, framenum, 1024)
                log_debug("%d:正在发包"%(i+1))
        time.sleep(5)
        for i in range(len(PortTest().bcm_ports)):
            if (i + 1) in upports :
                ret, log = PortTest().check_port_packets(i + 1, framenum, "rx")
                log_debug(ret)
                if ret == True:
                    successport.append(i + 1)
                else:
                    errorport.append(i + 1)
                    ret_t -= 1
                    caseerror.append({"name":"端口%d"%(i + 1), "error":"端口收发帧失败"})
                    log_debug(log)
            else:
                ret_t -= 1
                caseerror.append({"name":"端口%d"%(i + 1), "error":"up/down状态异常"})
                updownerrport.append(i+1)
    except Exception as e:
        print (e)
        ret_t  = -1
    finally:
        PortTest().reset_port_cpu()
    port_totalprint(successport, "OK")
    port_totalprint(updownerrport, "up/down状态异常")
    port_totalprint(errorport, "failed")
    testerror['errmsg'] = caseerror
    errt_t.append(testerror)
    if ret_t < 0:
        return False , errt_t
    return True ,""


def test_ports_prbs_new():
    '''ports prbs'''
    
    result_t = []
    testerror1 = {}
    testerror1["name"] = "mac prbs测试结果"
    testerror2 = {}
    testerror2["name"] = "sys prbs测试结果"
    testerror3 = {}
    testerror3["name"] = "line prbs测试结果"
    pr = None
    val_ber  = TESTCASE.get("PRBS").get("prbsber", None)
    # print val_ber
    if val_ber is None:
        pr = PortPrbsTest(val_ber)
    else:
        pr = PortPrbsTest()
    pr.clear_port_prbs()
    ret, log = pr.init_port_prbs()
    if  ret == False:
        raise Exception("prbs初始化失败 %s" % log)
    total_err = 0
    caseerror=[]
    print ("mac prbs测试结果:")
    for i in range(len(pr.bcm_ports)):
        ret, result = pr.get_port_prbs_result("mac", i + 1)
        if ret == False:
            print ("端口%03d : " % (i + 1),)
            print (result)
            total_err -= 1
            caseerror.append({"name":"端口%03d"%(i + 1), "error":result})
    testerror1['errmsg'] = caseerror
    
    caseerror=[]
    print ("sys prbs测试结果:")
    for i in range(len(pr.bcm_ports)):
        ret, result = pr.get_port_prbs_result("sys", i + 1)
        if ret == False:
            print ("端口%03d : " % (i + 1),)
            print (result)
            total_err -= 1
            caseerror.append({"name":"端口%03d"%(i + 1), "error":str(result)})
    testerror2['errmsg'] = caseerror
    
    caseerror=[]
    print ("line prbs测试结果:")
    for i in range(len(pr.bcm_ports)):
        ret, result = pr.get_port_prbs_result("line", i + 1)
        if ret == False:
            print ("端口%03d : " % (i + 1),)
            print (result)
            total_err -= 1
            caseerror.append({"name":"端口%03d"%(i + 1), "error":str(result)})
        
    testerror3['errmsg'] = caseerror
    pr.clear_port_prbs()
    
    result_t.append(testerror1)
    result_t.append(testerror2)
    result_t.append(testerror3)
    
    if total_err < 0:
        return False , result_t
    return True ,""

# port prbs
def test_port_prbs():
    errt_t = []
    ret_t = 0
    # Take port
    len_t = len(PortTest().bcm_ports)
    errmsg = []
    testerror ={}
    caseerror=[]
    testerror["name"] = "端口PRBS" 
    upports = []
    
    successport=[]
    updownerrport=[]
    errorport = []
    
    PortTest().init_port_prbs()
    for i in range(len_t):
        sta = PortTest().get_port_status(i + 1)
        if sta == "up":
            upports.append(i + 1);
    log_debug(",".join(str(index) for index in upports))
    for i in range(len_t):
        if (i + 1) in upports :
            PortTest().set_port_prbs(i + 1, 1)
    time.sleep(5)
    # get value
    for i in range(len_t):
        if (i + 1) in upports :
            log_debug("端口prbs校验:%d"% (i + 1))
            ret  = PortTest().get_port_prbs_result(i + 1)
            # log_debug(ret)
            if ret == 0:
                # print "端口%d : %s" %( i + 1, "[ok]")
                successport.append(i + 1)
            else:
                errorport.append(i + 1)
                caseerror.append({"name":"端口%d"%(i + 1), "error":"prbs测试失败"})
                ret_t -= 1
        else:
            updownerrport.append(i + 1)
            ret_t -= 1
            caseerror.append({"name":"端口%d"%(i + 1),"error":"up/down状态异常"})

    # All values UP Port PRBS
    for i in range(len_t):
        if (i + 1) in upports :
            PortTest().set_port_prbs(i + 1, 0)
    PortTest().reset_port_prbs()
    testerror['errmsg'] = caseerror
    errt_t.append(testerror)
    
    port_totalprint(successport, "OK")
    port_totalprint(updownerrport, "up/down状态异常")
    port_totalprint(errorport, "failed")
    
    if ret_t < 0:
        return False , errt_t
    return True ,""

# Port broadcast test
def test_port():
    errt_t = []
    ret_t = 0
    # Take port
    len_t = len(PortTest().bcm_ports)
    errmsg = []
    
    successport=[]
    updownerrport=[]
    errorport = []
    
    # Obtain which port is valid
    for i in range(len_t):
        sta = PortTest().get_port_status(i + 1)
        if sta == "up":
            log_debug("发送广播报文端口:%d" % (i+1))
            ret = PortTest().start_send_port_packets((i + 1), 10000)
            break
        else:
            log_debug(" 端口%d 状态:%s"% ( i + 1 ,sta))
            errmsg.append({"name":PortTest().bcm_ports[i], "error":sta})
    # Waiting time
    time.sleep(GRTD_BROADCAST_RETRY_SLEEP_TIME)
    log_debug("等待结果......")
    
    errt_t = []
    testerror ={}
    caseerror=[]
    testerror["name"] = "端口广播"
    for i in range(len_t):
        sta = PortTest().get_port_status(i + 1)
        log_debug("端口%d结果%s......"% ((i+1),sta))
        if sta == "up":
            ret , fcs = PortTest().get_port_fcs_status(i + 1)
            if ret == True and fcs[0] == 0 and fcs[1] == 0:
                successport.append(i + 1)
            else:
                ret_t -= 1
                errorport.append(i + 1)
                caseerror.append({"name":"端口%d"%(i + 1) ,"error":" 发送校验：%d  接收校验 %d" %(fcs[0], fcs[0]) })
                log_debug("error: 端口%d  发送校验：%d  接收校验 %d" %( (i + 1), fcs[0], fcs[0]) )
        else:
            ret_t -= 1
            updownerrport.append(i + 1)
            caseerror.append({"name":"端口%d"%(i + 1), "error":"up/down状态异常"})
    testerror['errmsg'] = caseerror
    errt_t.append(testerror)
    # Close the radio
    sta = PortTest().stop_send_port_packets()
    time.sleep(5)
    
    port_totalprint(successport, "OK")
    port_totalprint(updownerrport, "up/down状态异常")
    port_totalprint(errorport, "failed")
    if ret_t < 0:
        return False , errt_t
    return True ,""
    
def fan_check(fans, levelpolicy , errt_t):
    ret_t = 0
    try:
        stopFanctrol()
        # Keep the current fan level
        currentValue = "null"
        currentValue = get_pmc_register(fans["location"])
        log_debug("当前转速等级为: %s" % currentValue)
        print ("%s" % fans.get("name",None))
        # Keep the current fan level
        for level in levelpolicy["level"]:
            testerror = {}
            testind = 0
            ind = levelpolicy["level"].index(level)
            loc = fans["location"]
            if write_sysfs_value(loc, "0x%02x"% level ) :
                time.sleep(2)
                print ("风扇转速等级: 【%s】 0x%02x "% (levelpolicy["tips"][ind], level))
                log_debug("风扇转速等级: 【%s】 0x%02x " % (levelpolicy["tips"][ind], level))
            caseerror = []
            for fanstatus in fans["childfans"]:
                real_value = get_pmc_register(fanstatus["location"])
                nowspeed = int(real_value)
                lowspeed = levelpolicy["low_speed"][ind]
                highspeed = levelpolicy["high_speed"][ind]
                log_debug("%s [nowspeed: %d low_speed:%d high:%d]"% (fanstatus["name"], nowspeed ,lowspeed,highspeed))
                if lowspeed < nowspeed and highspeed > nowspeed:
                    print ("    %s : %s"%(fanstatus["name"], "[PASS]"))
                else:
                    print ("    %s : %s"%(fanstatus["name"], "[FAILED]"))
                    caseerror.append({"name":fanstatus["name"] ,"error":"不在转速范围内 [nowspeed: %d low_speed:%d high:%d]" % ( nowspeed ,lowspeed,highspeed)})
                    ret_t -= 1
                    testind -= 1
                if len(caseerror) > 0:
                    testerror["name"] = "[%s]转速等级:[%s]0x%02x "% (fans.get("name",None),levelpolicy["tips"][ind], level)
                    testerror['errmsg'] = caseerror
            if testind < 0:
                errt_t.append(testerror)
    except Exception as e:
        log_error(e.message)
        return False
    finally:
        if write_sysfs_value(loc, currentValue):
            log_debug("恢复初始转速")
        startFanctrol()
    if ret_t < 0: 
        return ret_t 
    return ret_t

# execute shell command
def log_os_system(cmd):
    status, output = subprocess.getstatusoutput(cmd)
    return  status, output

class Config(object):
    """Object to hold CLI config"""
    def __init__(self):
        self.path = os.getcwd()
        self.aliases = {}

    def read_config(self, filename):
        parser = configparser.RawConfigParser()
        parser.read([filename])
        try:
            self.aliases.update(parser.items('aliases'))
        except configparser.NoSectionError:
            pass
_config = None

#############################################################################
######### ragile util cli
############################################################################
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
        
class AliasedGroup(DefaultGroup):
    def get_command(self, ctx, cmd_name):
        global _config
        if _config is None:
            _config = Config()
            cfg_file = os.path.join(os.path.dirname(__file__), 'aliases.ini')
            _config.read_config(cfg_file)
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        if cmd_name in _config.aliases:
            actual_cmd = _config.aliases[cmd_name]
            return click.Group.get_command(self, ctx, actual_cmd)
        matches = [x for x in self.list_commands(ctx)
                   if x.lower().startswith(cmd_name.lower())]
        if not matches:
            ctx.arg0 = cmd_name
            cmd_name = self.default_cmd_name
            return DefaultGroup.get_command(self, ctx, cmd_name)
        elif len(matches) == 1:
            return DefaultGroup.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))

@click.group(context_settings=CONTEXT_SETTINGS)
def main():
    '''ragileutil interface'''
    pass

# get regisetr value
@main.command()
@click.argument('bus', required=True)
@click.argument('loc', required=True)
@click.argument('bit', required=True)
def dev_rd(bus, loc , bit):
    '''  i2c_rd get issuccess'''
    ret , log = rji2cget(int(bus), int(loc, 16) , int(bit, 16))
    if ret == True:
        click.echo("SUCCESS")
    else:
        click.echo(log)

# write register
@main.command()
@click.argument('bus', required=True)
@click.argument('loc', required=True)
@click.argument('bit', required=True)
@click.argument('value', required=True)
def dev_wr(bus, loc , bit, value):
    ''' i2c_set set value if success'''
    ret , log = rji2cset (int(bus), int(loc, 16) , int(bit, 16), int(value, 16)) 
    if ret == True:
        click.echo("SUCCESS")
    else:
        click.echo("Error:" + log)
          
# cpld test
@main.command()
@click.argument('bus', required=True)
@click.argument('loc', required=True)
@click.argument('bit', required=True)
def cpld_check(bus, loc , bit): 
    '''check read/write test'''
    try: 
        ret , log = rji2cget(int(bus), int(loc, 16) , int(bit, 16))
        if ret != True:
            click.echo("Error[get bus:%s loc:%s bit:%s] %s" %(bus, loc,bit ,log))
            return 
        value = 0xFF ^ int(log, 16) 
        ''' check i2c dev'''
        ret , log = rji2cset(int(bus), int(loc, 16) , int(bit, 16), value) 
        if ret != True:
            click.echo("Error[write bus:%s loc:%s bit:%s] %s" %(bus, loc,bit ,log))
            return
        ret , log = rji2cget(int(bus), int(loc, 16) , int(bit, 16))
        if ret != True :
            click.echo("Error[confirm bus:%s loc:%s bit:%s] %s" %(bus, loc,bit ,log))
            return 
        if int(log, 16) != value :
            click.echo("Error: read not equal write")
            return
        click.echo("SUCCESS")
    except Exception as e:
        click.echo("Error" + str(e))

@main.command()
@click.argument('location', required=True)
def sysfs(location):
    '''get sysfs value'''
    pos_t = str(location)
    name = get_pmc_register(pos_t)
    click.echo(name)

# Takes the I2C name at the specified location
@main.command()
@click.argument('location', required=True)
@click.argument('value', required=False)
def i2c(location , value):
    '''check i2c name'''
    pos_t = str(location) + "/name"
    name = get_pmc_register(pos_t)
    click.echo(name)

@main.group()
def led():
    ''' led test'''
    pass

# Writes values to the specified file
# grtd_test led loc 2-0033/broad_front_cpu 0x01
@led.command()
@click.argument('location', required=True)
@click.argument('value', required=True)
def loc(location, value):
    locs = location.split(",")
    val = value.split(",")
    if len(locs) != len(val):
        click.echo("不相等")
    else:
        for i in range(len(locs)):
            cmd = "echo %s > %s%s" % (val[i], MAILBOX_DIR,locs[i])
            ret , log =log_os_system(cmd)
            if ret != 0:
                click.echo("Error")
                click.echo(log)
    click.echo("SUCCESS")

@main.command()
@click.argument('location', required=True)
def temp(location):
    cmd = "cat %s%s" % (MAILBOX_DIR, location)
    ret , log = log_os_system(cmd)
    if ret != 0:
        click.echo("Error")
    click.echo(log)

@main.group()
def fan():
    ''' fan set '''
    pass

def printbinvalue(b):
    index = 0
    print ("     ",)
    for width in range(16):
        print ("%02x " % width,)
    print ("")
    for i in range(0, len(b)):
        if index % 16 == 0:
            print (" ")
            print (" %02x  " % i,)
        print ("%02x " % ord(b[i]),)
        index += 1
    print ("")

def decodeBinByValue(retval):
    fru = ipmifru()
    fru.decodeBin(retval)
    return fru

@fan.command()
def resetfane2():
    ''' show fan e2'''
    fru = ipmifru()
    # fru.initDefault()
    boardinfoarea = BoardInfoArea(name="Board Info Area",
                                      size=0)
    boardinfoarea.isPresent = True
    boardinfoarea.boardManufacturer = "Ragile"
    boardinfoarea.boardProductName = "M2EFAN I"
    boardinfoarea.boardSerialNumber = "0000000000000"
    boardinfoarea.boardPartNumber = "M2EFAN I"
    boardinfoarea.fruFileId = "3-8"
    boardinfoarea.boardextra1 = 'AA'
    
    pia = ProductInfoArea(name="Product Info Area ",
                                                  size=0)
    pia.isPresent = True
    pia.productManufacturer = 'Ragile'
    pia.productName = 'M2EFAN I-F'
    pia.productPartModelName = 'M2EFAN I-F'
    pia.productVersion = '00'
    pia.productSerialNumber = '0000000000000'    
    pia.productAssetTag = None
    pia.fruFileId = '3-8'
    pia.productextra1 = '2019-03-27'
    pia.productextra2 = '8600'
    fru.productInfoArea = pia
    fru.boardInfoArea = boardinfoarea
    fru.recalcute()
    printbinvalue(fru.bindata)
    
    
    fans =  FRULISTS.get('fans')
    for fan in fans:
        I2CUTIL.openFanE2Protect()
        I2CUTIL.writeToFanE2(fan.get('bus'), fan.get('loc'), fru.bindata)
        I2CUTIL.closeFanE2Protect()

@fan.command()
def showfane2():
    fans =  FRULISTS.get('fans')
    header = [ 'FAN', 'Presence', 'Status', 'Speed', 'LowThd', 'HighThd', 'PN', 'SN', 'AirFlow' ]
    status_table = []
    for fan in fans:
        eeprom = getsysvalue(I2CUTIL.getE2File(fan.get('bus'), fan.get('loc')))
        ret = decodeBinByValue(eeprom)
        # print ret
        fan_name =  fan.get('name')
        presence  = True
        status  = True
        speed = 0
        low = 0
        high = 0
        pn  = ret.productInfoArea.productName
        sn = ret.productInfoArea.productSerialNumber
        airflow  = 'FTOB'
        
        status_table.append([fan_name, presence, status, speed, low, high, pn, sn, airflow])
    click.echo(tabulate(status_table, header, tablefmt='simple'))


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

@fan.command()
def setmace2():
    '''fan setmac e2'''
    fans =  FRULISTS.get('fans')
    for fan in fans:
        eeprom = get_fane2_sysfs(fan.get('bus'), fan.get('loc'))
        fru = decodeBinByValue(eeprom)
        newfru = getInputSetmac(fru)
        
        newfru.recalcute()
        
        I2CUTIL.openFanE2Protect()
        I2CUTIL.writeToFanE2(fan.get('bus'), fan.get('loc'), newfru.bindata)
        I2CUTIL.closeFanE2Protect()
        
    pass
    
@fan.command()
def setmac_open():
    '''enable setmac fan e2'''
    I2CUTIL.openFanE2Protect()
    
@fan.command()
def setmac_close():
    '''disable setmac fan e2'''
    I2CUTIL.closeFanE2Protect()

@fan.command()
def speed_max():
    ''' set fan speed max'''
    stopFanctrol()
    cmd = "echo 0xFF > /sys/bus/i2c/devices/0-0032/fan_speed_set" 
    ret , log = log_os_system(cmd)
    if ret != 0:
        click.echo("Error")
    click.echo(log)
    
@fan.command()
@click.argument('level', required=True)
def speed(level):
    ''' set fan speed_level as input'''
    cmd = "echo %s  > /sys/bus/i2c/devices/0-0032/fan_speed_set" % level
    ret , log = log_os_system(cmd)
    if ret != 0:
        click.echo("Error")
    click.echo(log)
    
@fan.command()
def monitor_start():
    ''' fan control beyond sonic'''
    if STARTMODULE['fancontrol'] == 1:
        startFanctrol()
    else:        
        click.echo("no fancontrol")

@fan.command()
def monitor_stop():
    '''stop fancontrol.py'''
    if STARTMODULE['fancontrol'] == 1:
        stopFanctrol()
    else:
        click.echo("no fancontrol")

@main.group()
def port():
    pass

@port.command()
def deleteprbs():
    '''clear port prbs'''
    len_t = len(PortTest().bcm_ports)
    print (len_t)
    for i in range(len_t):
        PortTest().set_port_prbs(i + 1, 0)

@main.group()
def e2():
    ''' show eeprom '''
    # ret = get_sys_eeprom()
    # for item in ret:
    #    print  "%-20s : %s" % (item["name"], item["value"])
        
@click.command()
def cardid():
    ''' product cardid '''
    ret = getCardId()
    click.echo(ret)
    
@click.command()
def cardidreset():
    '''product cardid reset'''
    ret = getCardId()
    if ret != None:
        ret_input = getInputCheck("realy want do reset tlv all(Yes/No):")
        print (ret_input)
        if ret_input != True:
            return None
        else:
            eeprom_ret = get_sys_eeprom()
            for item in eeprom_ret:
               print  ("%-20s : %s" % (item["name"], item["value"]) )
    _value = {}
    _value[TLV_CODE_VENDOR_EXT] = generate_ext(RAGILE_CARDID)  
    rst, ret = generate_value(_value)
    writeToEEprom(rst)
    
    ret = getCardId()
    print (ret)
    
@click.command()
def tlvdetail():
    ''' show eeprom detail '''
    ret = get_sys_eeprom()
    for item in ret:
        print  ("%-20s : %s" % (item["name"], item["value"]))

@click.command()
def settlve2():
   return fac_board_setmac()

def getfilevalue(location):
    try:
        with open(location, 'r') as fd:
            retval = fd.read()
            retval = retval.rstrip('\r\n')
            retval = retval.lstrip(" ")
        return True, retval.strip()
    except Exception as e:
        return False, "error"
ret, result = getfilevalue("/tmp/.debug")
if ret == True and result == "openset":
    e2.add_command(cardidreset)
    e2.add_command(settlve2)
    
e2.add_command(cardid)
e2.add_command(tlvdetail)

"""
@click.command()
def resetall():
    '''reset all E2'''
    ret = getInputCheck("realy want do reset all(Yes/No):")
    if ret != True:
        return 
    I2CUTIL.openFanE2Protect()
    frus = [ elem  for elem in FRULISTS if '1'==elem["CANRESET"] ]
    for fru in frus:
        ret = FruUtil.fru_getdefault_eeprom(fru['E2PRODUCT'], fru['E2TYPE'])
        I2CUTIL.writeToE2(fru['bus'], fru['loc'], ret.bindata)
        click.echo("%02d %02x update success" %(fru['bus'], fru['loc']))
    I2CUTIL.closeFanE2Protect()
    pass
    
    
    
@click.command()
@click.argument('e2type', required=True, default="ZZ" )
def set(e2type):
    '''set fru by type'''
    if e2type == "ZZ":
        showe2typetips();
        return 
    FruUtil().setmac(e2type)

@click.command()
@click.argument('type', required=True, default = 'ZZ')
def show(type):
    '''show frus by type'''
    if type == 'ZZ':
        showe2typetips();
        return 
    psus = [ elem  for elem in FRULISTS if type == elem["E2TYPE"]]
    for val in psus:
        print "####################%s####################" % val["name"]
        filename = I2CUTIL.getE2File(val['bus'], val['loc'])
        ret = FruUtil.fru_decode_eeprom(filename)
        head = ["key","value"]
        if ret.boardInfoArea!= None:
            click.echo("=================board=================")
            click.echo(tabulate(ret.boardInfoArea.todict().items(), head, tablefmt="simple"))
         
        if ret.productInfoArea!= None:
            click.echo("\n\n=================product=================")
            click.echo(tabulate(ret.productInfoArea.todict().items(), head, tablefmt="simple"))

@click.command()
def getall():
    '''get all E2'''
    for fru in FRULISTS:
        click.echo("\n\n================%s======================"%fru['name'])
        filename = I2CUTIL.getE2File(fru['bus'], fru['loc'])
        ret = FruUtil.fru_decode_eeprom(filename)        
        head = ["key","value"]
        if ret != None:
            if ret.boardInfoArea!= None:
                click.echo(tabulate(ret.boardInfoArea.todict().items(), head, tablefmt="simple"))
            if ret.productInfoArea!= None:
                click.echo(tabulate(ret.productInfoArea.todict().items(), head, tablefmt="simple"))
    pass    
def getfilevalue(location):
    try:
        with open(location, 'r') as fd:
            retval = fd.read()
            retval = retval.rstrip('\r\n')
            retval = retval.lstrip(" ")
        return True, retval.strip()
    except Exception as e:
        return False, "error"
ret, result = getfilevalue("/tmp/.debug")
if ret == True and result == "openset":
    e2.add_command(cardidreset)
    e2.add_command(resetall)
    e2.add_command(set)
    e2.add_command(settlve2)
    
  
  
e2.add_command(cardid)
e2.add_command(getall)
e2.add_command(tlvdetail)
"""


def showe2typetips():
    ret = FRULISTS.keys()
    
    e2type2  = FRULISTS.keys()
    click.echo("please inpute type such as:" )
    for itemtype in e2type2:
        click.echo("\t%s : %s" % (itemtype,itemtype))

@click.command()
@click.argument('types', required=True, default = 'ZZ')
def show(types):
    '''show frus by type'''
    if type == 'ZZ':
        showe2typetips();
        return 
    
    for val in FRULISTS.get(types):
        print ("####################%s####################" % val["name"])
        eeprom = get_fane2_sysfs(val['bus'], val['loc'])
        ret = decodeBinByValue(eeprom)
        head = ["key","value"]
        if ret.boardInfoArea!= None:
            click.echo("=================board=================")
            click.echo(tabulate(ret.boardInfoArea.todict().items(), head, tablefmt="simple"))
         
        if ret.productInfoArea!= None:
            click.echo("\n\n=================product=================")
            click.echo(tabulate(ret.productInfoArea.todict().items(), head, tablefmt="simple"))
e2.add_command(show)  

@main.group()
def sys():
     pass
     
     
@main.group(cls=AliasedGroup)
def setmac():
    pass

@setmac.command()
@click.argument('eth', required=False,default = "eth0" )
@click.argument('mac', required=True)
def hwaddrset(eth, mac):
    ''' set hwaddr'''
    ret ,msg = util_setmac(eth, mac)
    if ret == True:
        click.echo("设置成功")
    else:
        click.echo("设置失败[%s]" % msg)
        
@setmac.command()
def hwaddrget(eth, mac):
    get_local_eth0_mac()

@setmac.command()
def bmcreset():
    if ipmi_set_mac("00:10:f3:32:91:d7")==True:
        click.echo("设置bmc成功")

@setmac.command()
def bmcinfo():
    ret, status =log_os_system("ipmitool lan print 1")
    click.echo(status)
    
@sys.command()
def mem():
    '''get hardware mem slot and size'''
    ret, result = getsysmeminfo()
    if ret == True:
        for item in result:
             click.echo ("      槽位号%s : %s" % (item['slot'], item['size']))

@sys.command()
def memdetail():
    '''get hardware mem message detail'''
    ret , result = getsysmeminfo_detail()
    if ret == True:
        for item in result:
            click.echo("内存槽位:%s"%item["Locator"])
            click.echo("====================================================")
            for v,k in item.items():
                click.echo("%-30s: %s"% (v ,k))
            click.echo("")

@sys.command()
def hwinfo():
    '''get hardware bios'''
    ret , result = gethwsys()
    
    head = ["key","value"]
    if ret == True:
        click.echo(tabulate(result.items(), head, tablefmt="simple"))
    click.echo("")

@sys.command()
def bios():
    '''get hardware bios'''
    ret , result = getsysbios()
    head = ['key','value']
    if ret == True:
        click.echo(tabulate(result.items(), head, tablefmt="simple"))
    click.echo("")

def getFormatHead(HEAD):
    len_t = len(HEAD)
    formatstr = "    "
    headtip = formatstr
    septips = formatstr
    for i in range(len_t):
        formatstr += "%-20s "
        headtip += "%%-%ds "%(20+wide_chars(HEAD[i]))
        septips +="%-20s "
        headtip = headtip % HEAD[i]
        septips = septips % ("-"*20)
    print (headtip)
    print (septips)
    return formatstr
    
def cpld_version_restful(url):   
    if url == "" or len(url) <=0:
        print("invalid url")
        return 
    from rest.rest import DeviceMessage, BMCMessage
    bmc = BMCMessage()
    value = bmc.getBmcValue(url)
    if value == None:
        return None
    json_dicts=json.dumps(value,indent=4)
    return json_dicts

    
@sys.command()
def cpld_version():
    '''get cpld version'''
    if len(CPLDVERSIONS) <=0:
        click.echo("没找到配置文件")
    header = ["名称","日期","版本"]
    formatstr = getFormatHead(header)
    result = []
    for cpld in CPLDVERSIONS:
        dict = {}
        gettype = cpld.get("gettype",None)
        bus = cpld.get("bus",None)
        devno = cpld.get("devno",None)
        url = cpld.get("url",None)
        io_addr = cpld.get("io_addr",None)
        data = ""
        t = True
        ret = None
        if gettype == "lpc":        
            for i in range(4):
                ret = lpc_cpld_rd(i)
                if ret == None:
                    t = False
                    break;
                data += chr(strtoint(ret))
        elif gettype == "io":
            for i in range(4):
                ret = io_rd(io_addr + i)
                if ret == None:
                    t = False
                    break;
                data += chr(strtoint(ret))
        elif gettype == "restful":
            ret = cpld_version_restful(url)
            if ret == None:
                continue
            data_1 = ret.replace("\""," ").strip().split(" ")
            for item in data_1:
                data += chr(strtoint(item))
        else:      
            for i in range(4):
                ind, ret = rji2cget(bus, devno, i)
                if ind == False:
                    t = False
                    break;
                data += chr(strtoint(ret))
        if data == "":
            result.append([ cpld.get('name',None),"NA","NA" ])
        else:
            result.append([ cpld.get('name',None),"%02x%02x%02x" %  (ord(data[1]) ,ord(data[2]) ,ord(data[3])),"%02x" %  (ord(data[0]))])
    for item in result:
        formatstr = "    %%-%ds %%-20s %%-20s "%((20+wide_chars(item[0])))
        print (formatstr%(item[0],item[1],item[2]))
         
    #    print item[0]    
    # click.echo(tabulate(result, header, tablefmt="simple"))
@sys.command()
def mactemp():
    sta, ret = getMacTemp();
    head = ["temp(average)","temp(max)"]
    formatstr = getFormatHead(head)
    print ("    %-20s  %-20s  "%(ret['average'],ret['maximum']))

@sys.command()
def cputemp():
    '''show cpu temp'''
    cputemp =[]
    status.getcputemp(cputemp)
    head = ["name","temperature"]
    formatstr = getFormatHead(head)
    for ctemp in cputemp:
        print (formatstr % (ctemp["name"], str(ctemp["temp"]) + "℃" ))

@sys.command()
def usbinfo():
    '''show usb info'''
    ret , info = getusbinfo();
    if ret == False:
        print (info)
        return 
    click.echo("%s %s"%("-"*6,"-"*20))
    click.echo("{id}    {size}G".format(**info))
    
    
@main.group()
def mac():
    pass
    
@mac.command()
@click.argument('name', required=True)
def getreg(name):
    '''get sdk reg'''
    ret, status = getSdkReg(name)# DMU_PCU_OTP_CONFIG_8
    # click.echo (status) 
    if ret == False:
        click.echo(status)
    click.echo("%s : %s"% (name, status))

@mac.command()
def pressure():
    ''' MAC Voltage regulation '''
    ret = AVSUTIL.mac_adj()
    if ret == False:
        click.echo("调压失败")
    else:
        click.echo("调压成功")
    
@main.group()
def restful():
    pass
@restful.command()
@click.argument('url', required=True)
def get(url):
    if url == "" or len(url) <=0:
        print("invalid url")
        return 
    from faclib.rest import HttpRest
    response = HttpRest().Get(url)
    print (response)

def lpc_cpld_rd(reg_addr):
    try: 
        regaddr = 0
        if type(reg_addr) == int:
            regaddr = reg_addr
        else:
            regaddr = int(reg_addr, 16)
        devfile = "/dev/lpc_cpld"
        fd = os.open(devfile, os.O_RDWR|os.O_CREAT)
        os.lseek(fd, regaddr, os.SEEK_SET)
        str = os.read(fd, 1)
        return "%02x" % ord(str) 
    except ValueError: 
        return None
    except Exception as e:
        print (e)
        return None
    finally:
        os.close(fd)
    return None
    
@main.group()
def io():
    pass

@io.command()
@click.argument('reg_addr', required=True)
@click.argument('len', required=True, default = 1, type = click.INT)
def rd(reg_addr,len):
    val = io_rd(reg_addr, len)
    print (val)
    

@io.command()
@click.argument('reg_addr', required=True)
@click.argument('reg_data', required=True)
def wr(reg_addr, reg_data):
    val = io_wr(reg_addr, reg_data)
    print (val)


@main.group()
def pci():
    pass
    
@pci.command()
@click.argument('pcibus', required=True)
@click.argument('slot', required=True)
@click.argument('fn', required=True)
@click.argument('bar', required=True, type = int)
@click.argument('offset', required=True, type = int)
def rd(pcibus , slot , fn, bar,  offset):
    '''read pci register'''
    if offset % 4 != 0:
        click.echo("offset must be multiple of 4")
        return 
    filename = "/sys/bus/pci/devices/0000:%02x:%02x.%x/resource%d" % (int(pcibus), int(slot), int(fn), int(bar))
    with open(filename, "r+") as file:
        size = os.path.getsize(filename)
        data = mmap.mmap(file.fileno(), size)
        result = data[offset: offset + 4]
        s = result[::-1]
        val = 0
        for i in range(0, len(s)):
            val = val << 8  | ord(s[i])
        click.echo("0x%08x" % val)
        data.close()
    pass

@pci.command()
@click.argument('pcibus', required=True)
@click.argument('slot', required=True)
@click.argument('fn', required=True)
@click.argument('bar', required=True, type = int)
@click.argument('offset', required=True, type = int)
@click.argument('data', required=True)
def wr(pcibus , slot ,fn, bar, offset, data):
    '''write pci register'''
    vl = strtoint(data)
    ret = inttostr(vl, 4)    
    filename = "/sys/bus/pci/devices/0000:%02x:%02x.%x/resource%d" % (int(pcibus), int(slot), int(fn), int(bar))
    with open(filename, "r+") as file:
        size = os.path.getsize(filename)
        data = mmap.mmap(file.fileno(), size)
        data[offset: offset + 4] = ret
        result = data[offset: offset + 4]
        s = result[::-1]
        val = 0
        for i in range(0, len(s)):
            val = val << 8  | ord(s[i])
        click.echo("0x%08x" % val)
        data.close()
    pass

def bmc_version_inner():
    "get bmc version"
    from rest.rest import DeviceMessage, BMCMessage
    BMC_VER_PATH="/xyz/openbmc_project/version/attr/BmcVersion"
    bmc = BMCMessage()
    value = bmc.getBmcValue(BMC_VER_PATH)
    if value == None:
        return -1
    json_dicts=json.dumps(value,indent=4)
    bmc_ver_str =("BMC Version:%s"%json_dicts)
    print("    %-20s\n"%bmc_ver_str)
    return 0


def cpld_version_inner():
    '''get cpld version'''
    if len(CPLDVERSIONS) <=0:
        click.echo("没找到配置文件")
    header = ["名称","日期","版本"]
    result = []
    return_ret = 0
    return_log = "Success"
    for cpld in CPLDVERSIONS:
        dict = {}
        gettype = cpld.get("gettype",None)
        bus = cpld.get("bus",None)
        devno = cpld.get("devno",None)
        url = cpld.get("url",None)
        data = ""
        t = True
        ret = None
        if gettype == "lpc":
            for i in range(4):
                ret = lpc_cpld_rd(i)
                if ret == None:
                    t = False
                    break;
                data += chr(strtoint(ret))
        elif gettype == "restful":
            ret = cpld_version_restful(url)
            if ret == None:
                return_ret = -1
                return_log = "get version failed: restful type cpld"
                continue
            data_1 = ret.replace("\""," ").strip().split(" ")
            for item in data_1:
                data += chr(strtoint(item))
        else:      
            for i in range(4):
                ind, ret = rji2cget(bus, devno, i)
                if ind == False:
                    t = False
                    break;
                data += chr(strtoint(ret))
        result.append([ cpld.get('name',None),"%02x%02x%02x" %  (ord(data[1]) ,ord(data[2]) ,ord(data[3])),"%02x" %  (ord(data[0]))])
    formatstr = getFormatHead(header)
    for item in result:
        formatstr = "    %%-%ds %%-20s %%-20s "%((20+wide_chars(item[0])))
        print (formatstr%(item[0],item[1],item[2]))
    return return_ret,return_log,result

@sys.command()
def show_all_version():
    # ONIE version
    print ("ONIE version\n")
    cmd="grep -rn onie_build_date /host/machine.conf"
    ret, log=log_os_system(cmd)
    cmd="grep -rn onie_version /host/machine.conf"
    ret1, log1=log_os_system(cmd)
    if ret != 0 or ret1 != 0:
        print ("get version failed: ONIE")
        print (log+log1)
    if len(log)<=0 or len(log1)<=0:
       print ("get version failed: ONIE")
    else:
       check_onie_version=log1.split('=')[1].strip()+"_"+log.split('=')[1].strip()
       print ("\tONIE 版本:%s"%(check_onie_version))
       # Check version consistency
       config_onie_version=get_version_config_info("ONIE_VERSION")
       # config_onie_version_test=get_rjconfig_info("ONIE_VERSION_TEST")
       if config_onie_version == None:
           onie_flag=True
       else:
           onie_flag=False
       if not onie_flag :
           if check_onie_version==config_onie_version.strip() :
               print ("\tONIE 版本信息一致: PASS\n")
           else:
               print ("\tONIE 版本信息一致%s: FAILED\n"%(config_onie_version))

    # diag version
    print ("diag version")
    # cmd="show version 2>/dev/null | grep SONiC |awk '{print $4}'"
    # ret, log=log_os_system(cmd)
    cmd1="show version 2>/dev/null"
    ret, log1=log_os_system(cmd1)
    # log_debug("diag version:cmd1:%s"%log1)
    cmd2="echo \"%s\" | grep SONiC"%log1
    ret, log2=log_os_system(cmd2)
    # log_debug("diag version:cmd2:%s"%log2)
    cmd="echo \"%s\" | awk '{print $4}'"%log2
    ret, log=log_os_system(cmd)
    # log_debug("diag version:cmd3:%s"%log)
    if ret != 0:
        print ("get version failed: diag")
        log_debug("diag version:cmd1:%s"%log1)
        log_debug("diag version:cmd2:%s"%log2)
        log_debug("diag version:cmd3:%s"%log)
        # print log
    if len(log)<5:
        print ("get version failed: diag")
        log_debug("diag version:cmd1:%s"%log1)
        log_debug("diag version:cmd2:%s"%log2)
        log_debug("diag version:cmd3:%s"%log)
    else:
       print ("\n\t"+log[6:]+"\n")
       # Check version consistency
       str_diag=get_version_config_info("DIAG_VERSION")
       if str_diag == None:
           diag_flag=True
       else:
           diag_flag=False
       if not diag_flag:
           if str_diag.strip()==log[6:].strip() :
               print ("\tdiag 版本信息一致: PASS")
           else:
               print ("\tdiag 版本信息一致%s: FAILED"%(str_diag))

    restful_url="/xyz/openbmc_project/version"
    try:
        log = restful_get(restful_url)
        # print repr(log)
        rest_t = json.loads(log)
        if rest_t == None:
            print("get version failed:restful获取失败")
            return -1
    except Exception as e:
        print (e)
        return -1
    master_bmc_version_none=rest_t.get("MasterBmcVersion")
    if master_bmc_version_none==None:
        master_bmc_version=""
    else:
        master_bmc_version=master_bmc_version_none.encode('gbk')
    slave_bmc_version_none=rest_t.get("SlaveBmcVersion")
    if slave_bmc_version_none==None:
        slave_bmc_version=""
    else:
        slave_bmc_version=slave_bmc_version_none.encode('gbk')
    # current_bmc_version=rest_t.get("BmcVersion").encode('gbk')

    # BMC
    print ("\nBMC Information\n")
    ret = bmc_version_inner()
    if ret != 0:
        print ("get version failed: bmc")
    # print "\n\t当前BMC版本:%s"%(current_bmc_version)
    # Check version consistency
    print ("\t主BMC版本:%s"%(master_bmc_version))
    config_bmc_master=get_version_config_info("BMC_MASTER_VERSION")
    if config_bmc_master == None:
        master_bmc_flag=True
    else:
        master_bmc_flag=False
    if not master_bmc_flag:
        if config_bmc_master.strip()==master_bmc_version.strip() :
            print ("\n\tBMC 主版本信息一致: PASS")
        else:
            print ("\n\tBMC 主版本信息一致%s: FAILED"%(config_bmc_master))
    print ("\n\t备BMC版本:%s"%(slave_bmc_version))
    config_bmc_slave=get_version_config_info("BMC_SLAVE_VERSION")
    if config_bmc_slave == None:
        slave_bmc_flag=True
    else:
        slave_bmc_flag=False
    if not slave_bmc_flag:
        if config_bmc_slave.strip()==slave_bmc_version.strip() :
            print ("\n\tBMC 备版本信息一致: PASS")
        else:
            print ("\n\tBMC 备版本信息一致%s: FAILED"%(config_bmc_slave))

    # SDK
    print ("\nSDK Information\n")
    temp_sdk_version=get_version_config_info("SDK_VERSION")
    if temp_sdk_version == None:
        sdk_flag=True
    else:
        sdk_flag=False

    # print repr(temp_sdk_version)
    cmd = "bcmcmd \"version\""
    ret , log = log_os_system(cmd)
    if ret != 0:
        print ("get version failed: sdk")
        print (log)
    else:
        version_temp = re.subn("(      \r\n)|(   \r\n\r\r\ndrivshell>)|(version\r\r)","",log)[0]
        version_clean = re.subn("\n","\n\t",version_temp)[0]
        print (version_clean)
        # Check version consistency
        if not sdk_flag:
            sdk_temp1=version_temp.split('\n')[2]
            # print repr(sdk_temp1)
            sdk_version_temp=sdk_temp1.split(' ')
            sdk_vers=sdk_version_temp[1]
            sdk_date=sdk_version_temp[3]
            check_sdk=sdk_vers.strip()+"_"+sdk_date.strip()
            if check_sdk == temp_sdk_version.strip():
                print ("\tSDK 版本信息一致: PASS\n")
            else:
                print ("\tSDK %s版本信息一致%s: FAILED\n"%(check_sdk,temp_sdk_version))

    # BOIS
    cmd = "dmidecode -t bios"
    ret , log = log_os_system(cmd)
    if ret != 0:
        print ("get version failed: bios")
        print (log)
    else:
        version_temp1 = re.subn("[\s\S]*(BIOS Information[\s\S]*)","\g<1>",log)[0]
        version_clean = re.subn("Handle[^\n]*\n","",version_temp1)[0]
        print (version_clean)
        # Check version consistency
        config_bios_master=get_version_config_info("BIOS_MASTER_VERSION")
        if config_bios_master == None:
            master_bios_flag=True
        else:
            master_bios_flag=False
        master_bios_version_none=rest_t.get("MasterBiosVersion")
        if master_bios_version_none==None:
            master_bios_version=""
        else:
            master_bios_version=master_bios_version_none.encode('gbk')
        print ("\t主BIOS版本:%s"%(master_bios_version))
        if not master_bios_flag:
            if config_bios_master.strip()==master_bios_version.strip() :
                print ("\tBIOS 主版本信息一致: PASS\n")
            else:
                print ("\tBIOS %s  %s主版本信息一致: FAILED\n"%(master_bios_version,config_bios_master))
        config_bios_slave=get_version_config_info("BIOS_SLAVE_VERSION")
        if config_bios_slave == None:
            slave_bios_flag=True
        else:
            slave_bios_flag=False
        slave_bios_version_none=rest_t.get("SlaveBiosVersion")
        if slave_bios_version_none==None:
            slave_bios_version=""
        else:
            slave_bios_version=slave_bios_version_none.encode('gbk')
        print ("\t备BIOS版本:%s"%(slave_bios_version))
        if not slave_bios_flag:
            if config_bios_slave.strip()==slave_bios_version.strip() :
                print ("\tBIOS 备版本信息一致: PASS\n")
            else:
                print ("\tBIOS %s  %s备版本信息一致: FAILED\n"%(slave_bios_version,config_bios_slave))

    # CPLD
    print ("\nCPLD Information\n")
    ret,log,tmp= cpld_version_inner()
    if ret != 0:
        print ("get version failed: cpld")
        print (log)
    # Check version consistency
    temp_cpld_version=get_version_config_info("CPLD_VERSION")
    if temp_cpld_version == None:
        cpld_flag=True
    else:
        cpld_flag=False
    if not cpld_flag:
        # print repr(temp_cpld_version)
        dict_cpld_version=eval(temp_cpld_version)
        dict_cpld_keys=dict_cpld_version.keys()
        # print repr(tmp)
        for item in tmp:
            for config_cpld_key in dict_cpld_keys:
                if item[0] == config_cpld_key:
                    item_temp=item[1]+item[2]
                    if item_temp == dict_cpld_version[config_cpld_key]:
                        print ("\n\tCPLD %s版本信息一致: PASS"%(config_cpld_key))
                    else:
                        print ("\n\tCPLD %s 版本信息一致%s: FAILED"%(config_cpld_key,dict_cpld_version[config_cpld_key]))

    # FPGA
    fpga_check=""
    config_fpga=get_version_config_info("FPGA_VERSION")
    if config_fpga == None:
        fpga_flag=True
    else:
        fpga_flag=False
    print ("\nFPGA Information\n")
    cmd = "grtd_test.py pci rd 8 0 0 0  0"
    ret , log = log_os_system(cmd)
    if ret != 0:
        print ("get version failed: fpga")
        print (log)
    else:
        print ("\tversion : %s"%log)
   
        fpga_check=fpga_check+log[2:]

    cmd = "grtd_test.py pci rd 8 0 0 0  4"
    ret , log = log_os_system(cmd)
    if ret != 0:
        print ("get version failed: fpga")
        print (log)
    else:
        print ("\tdate : %s"%log)
        # Check version consistency
        if not fpga_flag:
            fpga_check=fpga_check+"-"+log[2:]

    cmd = "grtd_test.py pci rd 8 0 0 0  12"
    ret , log = log_os_system(cmd)
    if ret != 0:
        print ("get version failed: fpga")
        print (log)
    else:
        print ("\tgolden version : %s"%log)
        # Check version consistency
        if not fpga_flag:
            fpga_check=fpga_check+"-"+log[2:]
            if fpga_check==config_fpga:
                print ("\n\tFPGA 版本信息一致: PASS")
            else:
                print ("\n\rFPGA %s  %s版本信息一致: FAILED"%(config_fpga,fpga_check))

    # TH3/TD3 PCIe
    temp_pcie_version=get_version_config_info("PCIE_VERSION")
    if temp_pcie_version == None:
        pcie_flag=True
    else:
        pcie_flag=False
    # print repr(temp_pcie_version)
    print ("\npciephy fw Information\n")
    cmd = "bcmcmd \"pciephy fw version\""
    ret , log = log_os_system(cmd)
    if ret != 0:
        print ("get version failed: pciephy fw")
        print (log)
    else:
        version_temp = re.subn("(      \r\n)|(   \r\n\r\r\ndrivshell>)|(version\r\r)","",log)[0]
        version_clean = re.subn("(pciephy fw \n)|(\r\r\ndrivshell>)","",version_temp)[0]
        print (version_clean)
        # Check version consistency
        if not pcie_flag:
            # print repr(version_clean)
            version1=version_clean.split('\n')
            # print repr(version1)
            ver_load_tmp=version1[1]
            ver_load=ver_load_tmp[1:len(ver_load_tmp)-1].split(':')[1]
            ver_vers_tmp=version1[2]
            ver_vers=ver_vers_tmp[1:len(ver_vers_tmp)-1].split(':')[1]
            # print repr(ver_load)
            # print repr(ver_vers)

            config_pcie=eval(temp_pcie_version)
            config_pcie_load=config_pcie["PCIE_FW_LOADER"]
            config_pcie_fw=config_pcie["PCIE_FW"]
            if ver_load.strip() == config_pcie_load and ver_vers.strip() == config_pcie_fw:
                print ("\tPCIe 版本信息一致: PASS")
            else:
                print ("\tPCIe %s %s版本信息一致%s %s: FAILED"%(config_pcie_fw,config_pcie_load,ver_vers,ver_load))


    # I210
    config_firm=get_version_config_info("I210_FIRMWARE")
    if config_firm == None:
        i210_flag=True
    else:
        i210_flag=False
    print ("\ni210 fw Information\n")
    cmd = "ethtool -i eth0"
    ret , log = log_os_system(cmd)
    if ret != 0:
        print ("get version failed: 210 fw")
        print (log)
    else:
        version_temp = log.split('\n')
        # print repr(version_temp)
        for i in version_temp:
            print ('\t%s' % i)
        # Check version consistency
        if not i210_flag:
            firm_version=version_temp[2]
            firm_ver=firm_version.split(':')[1].strip()
            firm_check=firm_ver.replace(', ','-')

            if firm_check in config_firm:
                print ("\n\ti210 fw 版本信息一致: PASS\n")
            else:
                print ("\n\ti210 fw %s 版本信息一致 %s: FAILED\n"%(firm_check,config_firm))

    if (RAGILE_PRODUCTNAME == "AS23-128H" or RAGILE_PRODUCTNAME == "AS14-128H") :
        # firmware Information
        firm_81724_ver_temp=get_version_config_info("81724_FIRMWARE")
        if firm_81724_ver_temp == None:
            firm_81724_ver=""
            f81724_flag=True
        else:
            firm_81724_ver=firm_81724_ver_temp
            f81724_flag=False
        print ("\n81724 fw Information\n")
        cmd = "bcmcmd \"phy control ce getee\"|grep fw_version"
        ret , log = log_os_system(cmd)
        if ret != 0:
            print ("get version failed: 81724 fw")
            print (log)
        else:
           # filted_list = re.findall(r".*fw_version=(\S*).*",log.lower())
           print (log)
           filted_list = re.findall(r"\bfailed",log.lower())
           if len(filted_list) > 0 :
               print ("\nthere are %d FAILED."%(len(filted_list)))
               # print("\tversion: %s\n"%filted_list[0])
           if not f81724_flag:
               version_list = re.findall(r".*port=(\S*).*fw_version=(\S*).*",log.lower())
               number_ver=0 
               if len(version_list) > 0:
                   for port,ver in version_list:
                       number_ver+=1
                       if ver.strip() != firm_81724_ver.strip():
                           break

                   if number_ver == len(version_list):
                       print ("81724 fw information 版本信息一致: PASS\n")
                   else:
                       print ("81724 fw information 版本信息一致: FAILED\n")

# Production test master program
if __name__ == '__main__':
    main()
