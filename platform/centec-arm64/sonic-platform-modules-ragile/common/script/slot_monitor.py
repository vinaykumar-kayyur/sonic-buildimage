#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import sys
import click
import os
import subprocess
import time
from  ragileutil import *
import syslog
import traceback
import json

SLOTMONITORDEBUG = 0 # 1 is open

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
    
def slotwarninglog(s):
    # s = s.decode('utf-8').encode('gb2312')
    syslog.openlog("SLOTMONITOR",syslog.LOG_PID)
    syslog.syslog(syslog.LOG_WARNING,s)

def slotcriticallog(s):
    # s = s.decode('utf-8').encode('gb2312')
    syslog.openlog("SLOTMONITOR",syslog.LOG_PID)
    syslog.syslog(syslog.LOG_CRIT,s)

def sloterror(s):
    # s = s.decode('utf-8').encode('gb2312')
    syslog.openlog("SLOTMONITOR",syslog.LOG_PID)
    syslog.syslog(syslog.LOG_ERR,s)

def slotdebuglog(s):
    # s = s.decode('utf-8').encode('gb2312')
    if SLOTMONITORDEBUG == 1:
        syslog.openlog("SLOTMONITOR",syslog.LOG_PID)
        syslog.syslog(syslog.LOG_DEBUG,s)

class SlotMonitor():
    def __init__(self):
        self.preSlotStatus = []

    def checkslot(self,ret):
        '''Obtain the status of the subcard'''
        slots_conf = SLOT_MONITOR_PARAM.get('slots', None)
        slotpresent = MONITOR_DEV_STATUS_DECODE.get('slotpresent',None)

        if slots_conf is None or slotpresent is None:
            return False
        for item_slot in slots_conf:
            totalerr = 0
            try:
                ret_t = {}
                ret_t["id"] = item_slot.get('name')
                ret_t["status"] = ""
                presentattr = item_slot.get('present')
                gettype = presentattr.get('gettype')
                presentbit = presentattr.get('presentbit')
                if gettype == "io":
                    io_addr = presentattr.get('io_addr')
                    val = io_rd(io_addr)
                    if val is not None:
                        retval = val
                    else:
                        totalerr -= 1
                        sloterror(" %s  %s" % (item_slot.get('name'), "lpc读取失败"))
                else:
                    bus = presentattr.get('bus')
                    loc = presentattr.get('loc')
                    offset = presentattr.get('offset')
                    ind, val = rji2cget(bus, loc,offset)
                    if ind == True:
                        retval = val
                    else:
                        totalerr -= 1
                        sloterror(" %s  %s" % (item_slot.get('name'), "i2c读取失败"))
                if totalerr < 0 :
                    ret_t["status"] = "NOT OK"
                    ret.append(ret_t)
                    continue
                val_t = (int(retval,16) & (1<< presentbit)) >> presentbit
                slotdebuglog("%s present:%s" % (item_slot.get('name'),slotpresent.get(val_t)))
                if val_t != slotpresent.get('okval'):
                    ret_t["status"] = "ABSENT"
                else:
                    ret_t["status"] = "PRESENT"
            except Exception as e:
                ret_t["status"] = "NOT OK"
                totalerr -= 1
                sloterror("checkslot error")
                sloterror(str(e))
            ret.append(ret_t)
        return True

    def dealslotplugin(self, name):
        slotdebuglog("enter dealslotplugin %s" % name)
        # wait for slot stable
        time.sleep(5)
        slots_conf = SLOT_MONITOR_PARAM.get('slots', None)
        if slots_conf is None:
            return False
        for item_slot in slots_conf:
            try:
                slotdebuglog("name %s, item_slot.get('name') %s" % (name, item_slot.get('name')))
                if (name == item_slot.get('name')):
                    actattr = item_slot.get('act')
                    for item_act in actattr:
                        gettype = item_act.get('gettype')
                        if gettype == "io":
                            io_addr = item_act.get('io_addr')
                            value = item_act.get('value')
                            mask = item_act.get('mask')
                            val = io_rd(io_addr)
                            if val is None:
                                sloterror(" %s  %s" % (name, "lpc读取失败"))
                                continue
                            set_val = (int(val, 16) & mask) | value
                            ret = io_wr(io_addr, set_val)
                            if ret != True:
                                sloterror(" %s %s" % (name, "lpc设置失败"))
                                continue
                            slotdebuglog("io set io_addr:0x%x value:0x%x success" % (io_addr, set_val))
                        elif gettype == "i2c":
                            bus = item_act.get('bus')
                            loc = item_act.get('loc')
                            offset = item_act.get('offset')
                            value = item_act.get('value')
                            ret, log = rji2cset(bus, loc, offset, value)
                            if ret != True:
                                sloterror(" %s %s %s" % (name, "i2c设置失败", log))
                                continue
                            slotdebuglog("i2c set bus:%d loc:0x%x offset:0x%x value:0x%x success" % (bus, loc, offset, value))
                        else:
                            sloterror("gettype error")
                    break
            except Exception as e:
                sloterror("dealslotplugin failed")
                sloterror(str(e))
                return False
        return True

    def updateSlotStatus(self):
        '''
        Only two status: PRESENT and ABSENT
        '''
        curSlotStatus = []
        self.checkslot(curSlotStatus)
        slotdebuglog('curSlotStatus: {}\n preSlotStatus: {}'.format(curSlotStatus, self.preSlotStatus))
        if cmp(self.preSlotStatus, curSlotStatus) != 0:
            if len(self.preSlotStatus) == 0:
                # first time
                for i,item in enumerate(curSlotStatus):
                    if cmp(item['status'], 'PRESENT') == 0:
                        slotdebuglog('SLOT_PLUG_IN: %s'%(item['id']))
                    elif cmp(item['status'], 'ABSENT') == 0:
                        slotdebuglog('SLOT_ABSENT: %s'%(item['id']))
                    else:
                        slotdebuglog('SLOT_FAILED: %s status %s not support yet'%(item['id'], item['status']))
                    self.preSlotStatus.append(item)
            else:
                for i,item in enumerate(curSlotStatus):
                    if cmp(item['status'], self.preSlotStatus[i]['status']) == 0:
                        continue
                    else:
                        if cmp(item['status'], 'PRESENT') == 0 and cmp(self.preSlotStatus[i]['status'], 'ABSENT') == 0:
                            self.dealslotplugin(item['id'])
                            slotwarninglog('SLOT_PLUG_IN: %s'%(item['id']))
                        elif cmp(item['status'], 'ABSENT') == 0 and cmp(self.preSlotStatus[i]['status'], 'PRESENT') == 0:
                            slotwarninglog('SLOT_PLUG_OUT: %s'%(item['id']))
                        else:
                            slotwarninglog('SLOT_PLUG_OUT: %s status change from %s to %s not support'%(item['id'], self.preSlotStatus[i]['status'], item['status']))
                        self.preSlotStatus.remove(self.preSlotStatus[i])
                        self.preSlotStatus.insert(i, item)

    def slotmonitor(self):
        self.updateSlotStatus()
        return 0

def doSlotMonitor(slotMonitor):
    slotMonitor.slotmonitor()

def run(interval, slotMonitor):
    # slotMonitor.devattrinit()
    while True:
        try:
            doSlotMonitor(slotMonitor)
        except Exception as e:
            traceback.print_exc()
            sloterror(str(e))
        time.sleep(interval)

@click.group(cls=AliasedGroup, context_settings=CONTEXT_SETTINGS)
def main():
    '''slot monitor operator'''
    pass
    
@main.command()
def start():
    '''start slot monitor'''
    slotwarninglog("slot_monitor start")
    slotMonitor = SlotMonitor()
    interval =  SLOT_MONITOR_PARAM.get('polling_time', 1)# The polling time in the configuration file is 1s by default
    run(interval, slotMonitor)

@main.command()
def stop():
    '''stop slot monitor '''
    slotwarninglog("stop")

# device_i2c operation
if __name__ == '__main__':
    main()

