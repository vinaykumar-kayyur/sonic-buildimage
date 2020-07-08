#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import click
import os
import commands
import time
import mmap
from  ruijieconfig import *
from  ruijieutil   import rjpciwr

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

class AliasedGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx)
                   if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))
   
def log_os_system(cmd):
    u'''执行shell命令'''
    status, output = commands.getstatusoutput(cmd)
    if status:
        print output
    return  status, output

def write_sysfs_value(reg_name, value):
    u'''写sysfs文件'''
    retval = 'ERR'
    mb_reg_file = "/sys/bus/i2c/devices/" + reg_name
    if (not os.path.isfile(mb_reg_file)):
        print mb_reg_file,  'not found !'
        return False
    try:
        with open(mb_reg_file, 'w') as fd:
            fd.write(value)
    except Exception as error:
        return False
    return True

def check_driver():
    u'''判断是否存在rg开头的驱动'''
    status, output = log_os_system("lsmod | grep rg | wc -l")
    #系统执行错误
    if status: 
        return False
    if output.isdigit() and int(output) > 0:
        return True
    else:
        return False

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

def startAvscontrol():
    cmd = "nohup avscontrol.py start >/dev/null 2>&1 &"
    rets = getPid("avscontrol.py")
    if len(rets) == 0:
        os.system(cmd)
    pass

def startFanctrol():
    if STARTMODULE['fancontrol'] == 1:
        cmd = "nohup fancontrol.py start >/dev/null 2>&1 &"
        rets = getPid("fancontrol.py")
        if len(rets) == 0:
            os.system(cmd)

def starthal_fanctrl():
    if STARTMODULE.get('hal_fanctrl',0) == 1:
        cmd = "nohup hal_fanctrl.py start >/dev/null 2>&1 &"
        rets = getPid("hal_fanctrl.py")
        if len(rets) == 0:
            os.system(cmd)

def starthal_ledctrl():
    if STARTMODULE.get('hal_ledctrl',0) == 1:
        cmd = "nohup hal_ledctrl.py start >/dev/null 2>&1 &"
        rets = getPid("hal_ledctrl.py")
        if len(rets) == 0:
            os.system(cmd)

def startDevmonitor():
    if STARTMODULE.get('dev_monitor',0) == 1:
        cmd = "nohup dev_monitor.py start >/dev/null 2>&1 &"
        rets = getPid("dev_monitor.py")
        if len(rets) == 0:
            os.system(cmd)

def startSlotmonitor():
    if STARTMODULE.get('slot_monitor',0) == 1:
        cmd = "nohup slot_monitor.py start >/dev/null 2>&1 &"
        rets = getPid("slot_monitor.py")
        if len(rets) == 0:
            os.system(cmd)

def stopFanctrol():
    u'''关闭风扇定时服务'''
    if STARTMODULE['fancontrol'] == 1:
        rets = getPid("fancontrol.py")  #
        for ret in rets:
            cmd = "kill "+ ret
            os.system(cmd)
        return True

def stophal_fanctrl():
    if STARTMODULE.get('hal_fanctrl',0) == 1:
        rets = getPid("hal_fanctrl.py")
        for ret in rets:
            cmd = "kill "+ ret
            os.system(cmd)
        return True

def stophal_ledctrl():
    if STARTMODULE.get('hal_ledctrl',0) == 1:
        rets = getPid("hal_ledctrl.py")
        for ret in rets:
            cmd = "kill "+ ret
            os.system(cmd)
        return True


def stopDevmonitor():
    u'''关闭风扇定时服务'''
    if STARTMODULE.get('dev_monitor',0) == 1:
        rets = getPid("dev_monitor.py")  #
        for ret in rets:
            cmd = "kill "+ ret
            os.system(cmd)
        return True

def stopSlotmonitor():
    u'''关闭slot定时服务'''
    if STARTMODULE.get('slot_monitor',0) == 1:
        rets = getPid("slot_monitor.py")  #
        for ret in rets:
            cmd = "kill "+ ret
            os.system(cmd)
        return True

def removeDev(bus, loc):
    cmd = "echo  0x%02x > /sys/bus/i2c/devices/i2c-%d/delete_device" % (loc, bus)
    devpath = "/sys/bus/i2c/devices/%d-%04x"%(bus, loc)
    if os.path.exists(devpath):
        log_os_system(cmd)
        
def addDev(name, bus, loc):
    if name == "lm75":
        time.sleep(0.1)
    pdevpath = "/sys/bus/i2c/devices/i2c-%d/" % (bus)
    for i in range(1, 100):#等待母bus生成，最多等待10s
        if os.path.exists(pdevpath) == True: 
            break
        time.sleep(0.1)
        if i % 10 == 0:
            click.echo("%%DEVICE_I2C-INIT: %s not found, wait 0.1 second ! i %d " % (pdevpath,i))
            
    cmd = "echo  %s 0x%02x > /sys/bus/i2c/devices/i2c-%d/new_device" % (name, loc, bus)
    devpath = "/sys/bus/i2c/devices/%d-%04x"%(bus, loc)
    if os.path.exists(devpath) == False:
        os.system(cmd)
    
def removeQSFP():
    u'''根据全部配置添加SFP'''
    qsfpconfig = GLOBALCONFIG["QSFP"]
    for bus in range(qsfpconfig["endbus"], qsfpconfig["startbus"] - 1, -1):
        removeDev(bus , 0x50)
        removeDev(bus , 0x51)
        
def addQSFP():
    qsfpconfig = GLOBALCONFIG["QSFP"]
    for bus in range(qsfpconfig["startbus"], qsfpconfig["endbus"] + 1):
        addDev("rg_sff", bus , 0x50)
        addDev("rg_sff", bus , 0x51)
        
def removedevs():
    devs = GLOBALCONFIG["DEVS"]
    for index in range(len(devs)-1, -1, -1 ):
        removeDev(devs[index]["bus"] , devs[index]["loc"])
        
def adddevs():
    devs = GLOBALCONFIG["DEVS"]
    for dev in range(0, devs.__len__()):
        addDev(devs[dev]["name"], devs[dev]["bus"] , devs[dev]["loc"])

def checksignaldriver(name):
    modisexistcmd = "lsmod | grep %s | wc -l" % name
    status, output = log_os_system(modisexistcmd)
    #系统执行错误
    if status: 
        return False
    if output.isdigit() and int(output) > 0:
        return True
    else:
        return False

def adddriver(name, delay):
    cmd = "modprobe %s" % name
    if delay != 0:
        time.sleep(delay)
    if checksignaldriver(name) != True:
        log_os_system(cmd)

def removedriver(name, delay):
    realname = name.lstrip().split(" ")[0];
    cmd = "rmmod -f %s" % realname
    if checksignaldriver(realname):
        log_os_system(cmd)

def removedrivers():
    u'''卸载所有驱动'''
    if GLOBALCONFIG == None:
        click.echo("%%DEVICE_I2C-INIT: load global config failed.")
        return
    drivers = GLOBALCONFIG.get("DRIVERLISTS", None)
    if drivers == None:
        click.echo("%%DEVICE_I2C-INIT: load driver list failed.")
        return 
    for index in range(len(drivers)-1, -1, -1 ):
        delay = 0
        name = ""
        if type(drivers[index]) == dict and drivers[index].has_key("delay"):
            name = drivers[index].get("name")
            delay = drivers[index]["delay"]
        else:
            name = drivers[index]
        removedriver(name, delay)

def adddrivers():
    u'''添加驱动'''
    if GLOBALCONFIG == None:
        click.echo("%%DEVICE_I2C-INIT: load global config failed.")
        return
    drivers = GLOBALCONFIG.get("DRIVERLISTS", None)
    if drivers == None:
        click.echo("%%DEVICE_I2C-INIT: load driver list failed.")
        return 
    for index in range(0 ,len(drivers)):
        delay = 0
        name = ""
        if type(drivers[index]) == dict and drivers[index].has_key("delay"):
            name = drivers[index].get("name")
            delay = drivers[index]["delay"]
        else:
            name = drivers[index]
        adddriver(name, delay)

def otherinit():
    for index in GLOBALINITPARAM:
        write_sysfs_value(index["loc"], index["value"])

    for index in GLOBALINITCOMMAND:
        log_os_system(index)
    
def unload_driver():
    u'''卸载设备和驱动'''
    stopDevmonitor() # 停止可拔插设备驱动监控
    stopFanctrol()  # 停止风扇控制服务
    removeQSFP()    # 卸载光模块
    removedevs()    # 卸载其他设备
    removedrivers() # 卸载驱动

def reload_driver():
    u'''重新加载设备和驱动'''
    removedevs()    # 卸载其他设备
    removedrivers() # 卸载驱动
    time.sleep(1)
    adddrivers()
    adddevs()


def i2c_check(bus,retrytime = 6):
    try:
        i2cpath = "/sys/bus/i2c/devices/" + bus
        while retrytime and not os.path.exists(i2cpath):
            click.echo("%%DEVICE_I2C-HA: i2c bus abnormal, last bus %s is not exist." % i2cpath)
            reload_driver()
            retrytime -= 1
            time.sleep(1)
    except Exception as e:
        click.echo("%%DEVICE_I2C-HA: %s" % str(e))
    return 

def MacLedSet(data):
    '''write pci register'''
    pcibus = MAC_LED_RESET.get("pcibus")
    slot = MAC_LED_RESET.get("slot")
    fn = MAC_LED_RESET.get("fn")
    bar = MAC_LED_RESET.get("bar")
    offset = MAC_LED_RESET.get("offset")
    val = MAC_LED_RESET.get(data, None)
    if val == None:
        click.echo("%%DEVICE_I2C-INIT: MacLedSet wrong input")
        return
    rjpciwr(pcibus, slot, fn, bar, offset, val)

def load_driver():
    u'''加载设备和驱动'''
    adddrivers();
    adddevs();
    if STARTMODULE.get("i2ccheck",0) == 1: #i2c HA
        busend = i2ccheck_params.get("busend")
        retrytime = i2ccheck_params.get("retrytime")
        i2c_check(busend,retrytime)
    addQSFP()       # 添加光模块eeprom
    startFanctrol() # 打开风扇
    starthal_fanctrl() # 打开风扇控制
    starthal_ledctrl() # 打开LED控制
    if STARTMODULE['avscontrol'] == 1:
        startAvscontrol() # avs调压
    startDevmonitor() # 可插拔设备驱动监控
    startSlotmonitor() # 线卡插拔初始化监控
    otherinit();    # 其他初始化 光模块初始化
    if STARTMODULE.get("macledreset",0) == 1:
        MacLedSet("reset")
    
@click.group(cls=AliasedGroup, context_settings=CONTEXT_SETTINGS)
def main():
    '''device operator'''
    pass


@main.command()
def start():
    '''load device '''
    if check_driver():
        unload_driver()
    load_driver()

@main.command()
def stop():
    '''stop device '''
    unload_driver()

@main.command()
def restart():
    '''restart device'''
    unload_driver()
    load_driver()

if __name__ == '__main__':
    u'''device_i2c operation'''
    main()
