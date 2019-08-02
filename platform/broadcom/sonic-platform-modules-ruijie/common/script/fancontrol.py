#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import sys
import click
import os
import commands
import time
from  ruijieutil import * 
import syslog
from monitor import status
import traceback

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

DEBUG_COMMON     = 0x01
DEBUG_LEDCONTROL = 0x02
DEBUG_FANCONTROL = 0x04



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
    
def fanwarninglog(s):
    #s = s.decode('utf-8').encode('gb2312')
    syslog.openlog("FANCONTROL",syslog.LOG_PID)
    syslog.syslog(syslog.LOG_WARNING,s)
    
def fancriticallog(s):
    #s = s.decode('utf-8').encode('gb2312')
    syslog.openlog("FANCONTROL",syslog.LOG_PID)
    syslog.syslog(syslog.LOG_CRIT,s)
    
def fanerror(s):
    #s = s.decode('utf-8').encode('gb2312')
    syslog.openlog("FANCONTROL",syslog.LOG_PID)
    syslog.syslog(syslog.LOG_ERR,s)
    
def fanwarningdebuglog(debuglevel,s):
    #s = s.decode('utf-8').encode('gb2312')
    if FANCTROLDEBUG & debuglevel:
        syslog.openlog("FANCONTROL",syslog.LOG_PID)
        syslog.syslog(syslog.LOG_DEBUG,s)
 

class FanControl():
    critnum = 0
    def __init__(self):
        self._fanOKNum = 0
        self._psuOKNum = 0
        self._intemp = -100.0
        self._mac_aver = -100.0
        self._mac_max = -100.0
        self._preIntemp = -1000 # 上一时刻温度
        self._outtemp = -100
        self._boardtemp = -100
        self._cputemp = -1000
        pass

    @property
    def fanOKNum(self):
        return self._fanOKNum;

    @property
    def psuOKNum(self):
        return self._psuOKNum;

    @property
    def cputemp(self):
        return self._cputemp;
 
    @property
    def intemp(self):
        return self._intemp;
        
    @property
    def outtemp(self):
        return self._outtemp;
        
    @property
    def boardtemp(self):
        return self._boardtemp;

    @property
    def mac_aver(self):
        return self._mac_aver;

    @property
    def preIntemp(self):
        return self._preIntemp;

    @property
    def mac_max(self):
        return self._mac_max;

    def sortCallback(self, element):
        return element['id']

    def getCurrentSpeed(self):
        try:
            loc = fanloc[0].get("location","")
            sped = get_sysfs_value(loc)
            value = strtoint(sped)
            return value
        except Exception as e:
            fanerror("%%policy: get current speedlevel error")
            fanerror(str(e))
            return None

    # 调速后低于最新则为最低
    def checkCurrentSpeedSet(self):
        fanwarningdebuglog(DEBUG_FANCONTROL,"%%policy:调速后保证最低转速运行")
        value =  self.getCurrentSpeed()
        if value is None or value == 0:
            raise Exception("%%policy: getCurrentSpeed None")
        elif value < MONITOR_CONST.MIN_SPEED:
            self.fanSpeedSet(MONITOR_CONST.MIN_SPEED)
        
    
    def fanSpeedSet(self, level):        
        if level >= MONITOR_CONST.MAX_SPEED:
            level = MONITOR_CONST.MAX_SPEED
        for item in fanloc:
            try:
                loc = item.get("location","")
                write_sysfs_value(loc, "0x%02x"% level )
            except Exception as e:
                fanerror(str(e))
                fanerror("%%policy: config fan runlevel error")
        self.checkCurrentSpeedSet() # 保证最低
    
    def fanSpeedSetMax(self):
        try:
            self.fanSpeedSet(MONITOR_CONST.MAX_SPEED)
        except Exception as e:
            fanerror("%%policy:fanSpeedSetMax failed")
            fanerror(str(e))
    
    def fanStatusCheck(self): # 风扇状态检测，有风扇异常直接全速转
        if self.fanOKNum < MONITOR_CONST.FAN_TOTAL_NUM:
            fanwarninglog("%%FANCONTRL-FAILED_NORMALFAN_NUM : %d" % (self.fanOKNum))
            self.fanSpeedSetMax()
            return False
        return True

    def getCpuTemp(self, cputemp):
        for i,item in enumerate(cputemp):
            if item["name"] == "Physical id 0":
                self._cputemp = float(item["temp"])
        fanwarningdebuglog(DEBUG_COMMON,"cputemp:%f"% self._cputemp )

    def getCpuStatus(self):
        try:
           cputemp =[]
           status.getcputemp(cputemp)
           self.getCpuTemp(cputemp)
           fanwarningdebuglog(DEBUG_COMMON,"%%policy:getCpuStatus success" )
           return 0
        except AttributeError as e:
            fanerror(str(e))
        except Exception as e:
            fanerror(str(e))
        return -1

    def setFanAttr(self,val):
        u'''设置每个风扇的状态'''
        for item in val:
            fanid = item.get("id")
            fanattr = fanid + "status"
            fanstatus = item.get("errmsg")
            setattr(FanControl,fanattr,fanstatus)
            fanwarningdebuglog(DEBUG_COMMON,"fanattr:%s,fanstatus:%s"% (fanattr,fanstatus))

    def getFanPresentNum(self,curFanStatus):
        fanoknum = 0;
        for i,item in enumerate(curFanStatus):
            if item["errcode"] == 0:
                fanoknum += 1
        self._fanOKNum = fanoknum
        fanwarningdebuglog(DEBUG_COMMON,"fanOKNum = %d"% self._fanOKNum)

    def getFanStatus(self):
        try:
            curFanStatus = []
            status.checkFan(curFanStatus)
            curFanStatus.sort(key = self.sortCallback)
            self.setFanAttr(curFanStatus) 
            self.getFanPresentNum(curFanStatus)
            fanwarningdebuglog(DEBUG_COMMON,"%%policy:getFanStatus success" )
            return 0
        except AttributeError as e:
            fanerror(str(e))
        except Exception as e:
            fanerror(str(e))
        return -1

    def getPsuOkNum(self,curPsuStatus):
        psuoknum = 0;
        for i,item in enumerate(curPsuStatus):
            if item["errcode"] == 0:
                psuoknum += 1
        self._psuOKNum = psuoknum
        fanwarningdebuglog(DEBUG_COMMON,"psuOKNum = %d"% self._psuOKNum)

    def getPsuStatus(self):
        try:
            curPsuStatus = []
            status.getPsu(curPsuStatus)
            curPsuStatus.sort(key = self.sortCallback)
            self.getPsuOkNum(curPsuStatus)
            fanwarningdebuglog(DEBUG_COMMON,"%%policy:getPsuStatus success" )
            return 0
        except AttributeError as e:
            fanerror(str(e))
        except Exception as e:
            fanerror(str(e))
        return -1

    def getMonitorInTemp(self, temp):
        for i,item in enumerate(temp):
            if item["id"] == "lm75in":
                self._intemp = float(item["temp1_input"])
            if item["id"] == "lm75out":
                self._outtemp = float(item["temp1_input"])
            if item["id"] == "lm75hot":
                self._boardtemp = float(item["temp1_input"])
        fanwarningdebuglog(DEBUG_COMMON,"intemp:%f, outtemp:%f, boadrtemp:%f"% (self._intemp,self._outtemp,self._boardtemp))

    def getTempStatus(self):
        try:
            monitortemp =[]
            status.getTemp(monitortemp)
            monitortemp.sort(key = self.sortCallback)
            self.getMonitorInTemp(monitortemp)
            fanwarningdebuglog(DEBUG_COMMON,"%%policy:getTempStatus success" )
            return 0
        except AttributeError as e:
            fanerror(str(e))
        except Exception as e:
            fanerror(str(e))
        return -1

    def getMacStatus(self):
        try:
            sta, ret = getMacTemp()
            if sta == True:
                self._mac_aver = float(ret["average"])
                self._mac_max  = float(ret["maximum"])
                fanwarningdebuglog(DEBUG_COMMON,"mac_aver:%f, mac_max:%f" % (self.mac_aver,self._mac_max))
            else:
                fanwarningdebuglog(DEBUG_COMMON,"%%policy:getMacStatus failed" )
            return 0
        except AttributeError as e:
            fanerror(str(e))
        return -1

    def settSlotAttr(self,val):
        u'''设置每个子卡的在位状态属性'''
        for item in val:
            slotid = item.get("id")
            slotattr = slotid + "status"
            slotstatus = item.get("errmsg")
            setattr(FanControl,slotattr,slotstatus)
            fanwarningdebuglog(DEBUG_COMMON,"slotattr:%s,slotstatus:%s"% (slotattr,slotstatus))

    def getSlotStatus(self):
        try:
            curSlotStatus = []
            if hasattr(status, 'checkSlot'):
                status.checkSlot(curSlotStatus)
                curSlotStatus.sort(key = self.sortCallback)
                self.settSlotAttr(curSlotStatus)
                fanwarningdebuglog(DEBUG_COMMON,"%%policy:getSlotStatus success" )
            else:
                pass 
        except AttributeError as e:
            fanerror(str(e))
        return 0

    def fanctrol(self): #风扇调速
        try:
            if self.preIntemp <= -1000:
                self.preIntemp = self.intemp
            fanwarningdebuglog(DEBUG_FANCONTROL,"%%policy:前次温度[%.2f] , 本次温度[%.2f]" % (self.preIntemp,self.intemp))
            if self.intemp < MONITOR_CONST.TEMP_MIN:
                fanwarningdebuglog(DEBUG_FANCONTROL,"%%policy:入风口  %.2f  最小温度: %.2f" %(self.intemp,MONITOR_CONST.TEMP_MIN))
                self.fanSpeedSet(MONITOR_CONST.DEFAULT_SPEED) # 默认等级
            elif self.intemp >=  MONITOR_CONST.TEMP_MIN and self.intemp > self.preIntemp:
                fanwarningdebuglog(DEBUG_FANCONTROL,"%%policy:温度上升")
                self.policySpeed(self.intemp)
            elif self.intemp >=  MONITOR_CONST.TEMP_MIN and (self.preIntemp - self.intemp) > MONITOR_CONST.MONITOR_FALL_TEMP:
                fanwarningdebuglog(DEBUG_FANCONTROL,"%%policy:温度下降%d度以上" % MONITOR_CONST.MONITOR_FALL_TEMP)
                self.policySpeed(self.intemp)
                pass
            else:
                speed = self.getCurrentSpeed()# 读取当前转速进行设置，防止风扇狗叫
                if speed is not None:
                    self.fanSpeedSet(speed)
                fanwarningdebuglog(DEBUG_FANCONTROL,"%%policy:不做任何改变")
        except Exception as e:
            fanerror("%%policy: fancontrol error")

    # 开始调速
    def startFanCtrol(self):
        if self.fanStatusCheck() == True:
            self.checkDevError()
            self.checkCrit()
            if self.critnum == 0:
                if self.checkWarning() == False:
                    self.fanctrol()
        fanwarningdebuglog(DEBUG_FANCONTROL,"%%policy:调速完转速 %0x" % (self.getCurrentSpeed()))

    def policySpeed(self, temp): # 风扇调速策略
        fanwarningdebuglog(DEBUG_FANCONTROL,"%%policy:扇调速公式调速")
        sped_level = MONITOR_CONST.DEFAULT_SPEED + MONITOR_CONST.K * (temp - MONITOR_CONST.TEMP_MIN)
        self.fanSpeedSet(sped_level)
        self.preIntemp = self.intemp

    def getBoardMonitorMsg(self,ledcontrol = False):
        ret_t = 0
        try:
            ret_t += self.getFanStatus()  # 获取风扇状态，得到OK的风扇个数
            ret_t += self.getTempStatus() # 获取入风口，出风口，最热点温度
            ret_t += self.getCpuStatus()  # 获取CPU温度
            ret_t += self.getMacStatus()  # 获取MAC最高温和平均温,待确认返回值
            if ledcontrol == True:
                ret_t += self.getSlotStatus() # 获取子卡在位状态
                ret_t += self.getPsuStatus()  # 获取OK电源数
            if ret_t == 0:
                return True
        except Exception as e:
            fanerror(str(e))
        return False
    
    # 器件失败策略    Tmac-Tin≥50℃，或者Tmac-Tin≤-50℃
    def checkDevError(self):
        try:
            if (self.mac_aver - self.intemp) >= MONITOR_CONST.MAC_UP_TEMP or (self.mac_aver - self.intemp) <= MONITOR_CONST.MAC_LOWER_TEMP:
                fanwarninglog("%%FANCONTRL-0-MAC_TEMP_ERROR: %.2f  %.2f" % (self.mac_aver, self.intemp))
                value =  self.getCurrentSpeed()
                if MONITOR_CONST.MAC_ERROR_SPEED >= value:
                    self.fanSpeedSet(MONITOR_CONST.MAC_ERROR_SPEED)
                else:
                    self.fanSpeedSetMax()
                    pass
            else:
                pass
        except Exception as e:
            fanerror("%%policy:checkDevError failed")
            fanerror(str(e))

    def checkTempWarning(self):
        u'''判断温度是否出现普通告警'''
        try:
            if self._mac_aver >= MONITOR_CONST.MAC_WARNING_THRESHOLD \
            or self._outtemp >= MONITOR_CONST.OUTTEMP_WARNING_THRESHOLD \
            or self._boardtemp >= MONITOR_CONST.BOARDTEMP_WARNING_THRESHOLD \
            or self._cputemp>=MONITOR_CONST.CPUTEMP_WARNING_THRESHOLD \
            or self._intemp >=MONITOR_CONST.INTEMP_WARNING_THRESHOLD:
                fanwarningdebuglog(DEBUG_COMMON,"温度超过普通告警值")
                return True
        except Exception as e:
            fanerror("%%policy: checkTempWarning failed")
            fanerror(str(e))
        return False

    def checkTempCrit(self):
        u'''判断温度是否出现严重告警'''
        try:
            if self._mac_aver >= MONITOR_CONST.MAC_CRITICAL_THRESHOLD \
            or ( self._outtemp >= MONITOR_CONST.OUTTEMP_CRITICAL_THRESHOLD \
            and self._boardtemp >= MONITOR_CONST.BOARDTEMP_CRITICAL_THRESHOLD \
            and self._cputemp>= MONITOR_CONST.CPUTEMP_CRITICAL_THRESHOLD \
            and self._intemp >= MONITOR_CONST.INTEMP_CRITICAL_THRESHOLD):
                fanwarningdebuglog(DEBUG_COMMON,"温度超过严重告警值")
                return True
        except Exception as e:
            fanerror("%%policy: checkTempCrit failed")
            fanerror(str(e))
        return False

    def checkFanStatus(self):
        u'''检测风扇状态'''
        for item in MONITOR_FAN_STATUS:
            maxoknum = item.get('maxOkNum')
            minoknum = item.get('minOkNum')
            status = item.get('status')
            if self.fanOKNum >= minoknum and self.fanOKNum <= maxoknum :
                fanwarningdebuglog(DEBUG_COMMON,"checkFanStatus:fanOKNum:%d,status:%s" % (self.fanOKNum,status))
                return status
        fanwarningdebuglog(DEBUG_COMMON,"checkFanStatus Error:fanOKNum:%d" % (self.fanOKNum))
        return None

    def checkPsuStatus(self):
        u'''检测电源状态'''
        for item in MONITOR_PSU_STATUS:
            maxoknum = item.get('maxOkNum')
            minoknum = item.get('minOkNum')
            status = item.get('status')
            if self.psuOKNum >= minoknum and self.psuOKNum <= maxoknum :
                fanwarningdebuglog(DEBUG_COMMON,"checkPsuStatus:psuOKNum:%d,status:%s" % (self.psuOKNum,status))
                return status
        fanwarningdebuglog(DEBUG_COMMON,"checkPsuStatus Error:psuOKNum:%d" % (self.psuOKNum))
        return None

    def dealSysLedStatus(self):
        u'''根据温度，风扇和电源状态设置SYSLED'''
        try:
            fanstatus = self.checkFanStatus()
            psustatus = self.checkPsuStatus()
            if self.checkTempCrit() == True or fanstatus == "red" or psustatus == "red":
                status = "red"
            elif self.checkTempWarning() == True or fanstatus == "yellow" or psustatus == "yellow":
                status = "yellow"
            else:
                status = "green"
            self.setSysLed(status)
            fanwarningdebuglog(DEBUG_LEDCONTROL,"%%ledcontrol:dealSysLedStatus success, status:%s," % status)
        except Exception as e:
            fanerror(str(e))

    def dealSysFanLedStatus(self):
        u'''根据状态点面板风扇灯'''
        try:
            status = self.checkFanStatus()
            if status is not None:
                self.setSysFanLed(status)
                fanwarningdebuglog(DEBUG_LEDCONTROL,"%%ledcontrol:dealSysFanLedStatus success, status:%s," % status)
        except Exception as e:
            fanerror("%%ledcontrol:dealSysLedStatus error")
            fanerror(str(e))

    def dealPsuLedStatus(self):
        u'''根据电源状态设置PSU-LED'''
        try:
            status = self.checkPsuStatus()
            if status is not None:
                self.setSysPsuLed(status)
            fanwarningdebuglog(DEBUG_LEDCONTROL,"%%ledcontrol:dealPsuLedStatus success, status:%s," % status)
        except Exception as e:
            fanerror("%%ledcontrol:dealPsuLedStatus error")
            fanerror(str(e))

    def dealLocFanLedStatus(self):
        u'''根据风扇状态点风扇本体灯'''
        for item in MONITOR_FANS_LED:
            try:
                index = MONITOR_FANS_LED.index(item) + 1
                fanattr = "fan%dstatus" % index
                val_t = getattr(FanControl,fanattr,None)
                if val_t == "NOT OK":
                    rji2cset(item["bus"],item["devno"],item["addr"], item["red"])
                elif val_t == "OK":
                    rji2cset(item["bus"],item["devno"],item["addr"], item["green"])
                else:
                    pass
                fanwarningdebuglog(DEBUG_LEDCONTROL,"%%ledcontrol:dealLocFanLed success.fanattr:%s, status:%s"% (fanattr,val_t))
            except Exception as e:
                fanerror("%%ledcontrol:dealLocFanLedStatus error")
                fanerror(str(e))

    def dealSlotLedStatus(self):
        u'''根据子卡在位状态点子卡状态灯'''
        slotLedList = DEV_LEDS.get("SLOTLED",[])
        for item in slotLedList:
            try:
                index = slotLedList.index(item) + 1
                slotattr = "slot%dstatus" % index
                val_t = getattr(FanControl,slotattr,None)
                if val_t == "PRESENT":
                    rji2cset(item["bus"],item["devno"],item["addr"], item["green"])
                fanwarningdebuglog(DEBUG_LEDCONTROL,"%%ledcontrol:dealSlotLedStatus success.slotattr:%s, status:%s"% (slotattr,val_t))
            except Exception as e:
                fanerror("%%ledcontrol:dealSlotLedStatus error")
                fanerror(str(e))

    def dealBmcLedstatus(self,val):
        pass

    def dealLctLedstatus(self,val):
        pass

    def setSysLed(self,color):
        for item in MONITOR_SYS_LED:
            if item.get('type', 'i2c') == 'sysfs':
                rjsysset(item["cmdstr"], item.get(color))
            else :
                rji2cset(item["bus"],item["devno"],item["addr"], item.get(color))

    def setSysFanLed(self,color):
        for item in MONITOR_SYS_FAN_LED:
            if item.get('type', 'i2c') == 'sysfs':
                rjsysset(item["cmdstr"], item.get(color))
            else :
                rji2cset(item["bus"],item["devno"],item["addr"], item.get(color))

    def setSysPsuLed(self,color):
        for item in MONITOR_SYS_PSU_LED:
            if item.get('type', 'i2c') == 'sysfs':
                rjsysset(item["cmdstr"], item.get(color))
            else :
                rji2cset(item["bus"],item["devno"],item["addr"], item.get(color))

    def checkWarning(self):
        try:
            if self.checkTempWarning() == True:
                fanwarningdebuglog(DEBUG_FANCONTROL,"防抖开始")
                time.sleep(MONITOR_CONST.SHAKE_TIME)
                fanwarningdebuglog(DEBUG_FANCONTROL,"防抖结束")
                self.getBoardMonitorMsg()# 再读一次
                if self.checkTempWarning() == True:
                    fanwarninglog("%%FANCONTROL-0-SYS_WARNING")
                    self.fanSpeedSetMax()  # 风扇全速
                    return True
        except Exception as e:
            fanerror("%%policy: checkWarning failed")
            fanerror(str(e))
        return False

    def checkCrit(self):
        try:
            if self.checkTempCrit() == True:
                fanwarningdebuglog(DEBUG_FANCONTROL,"防抖开始")
                time.sleep(MONITOR_CONST.SHAKE_TIME)
                fanwarningdebuglog(DEBUG_FANCONTROL,"防抖结束")
                self.getBoardMonitorMsg()# 再读一次
                if self.checkTempCrit() == True:
                    fancriticallog("%%FANCONTROL-0-SYS_CRIT")
                    self.fanSpeedSetMax()  # 风扇全速
                    self.critnum += 1 # 防抖
                    if self.critnum >= MONITOR_CONST.CRITICAL_NUM:
                       os.system("reboot")
                    fanwarningdebuglog(DEBUG_FANCONTROL,"crit次数:%d" % self.critnum)
                else:
                    self.critnum = 0
            else:
                self.critnum = 0
        except Exception as e:
            fanerror("%%policy: checkCrit failed")
            fanerror(str(e))
            

def callback():
    pass

def doFanCtrol(fanCtrol):
    ret = fanCtrol.getBoardMonitorMsg()
    if ret==True:
        fanwarningdebuglog(DEBUG_FANCONTROL,"%%policy:startFanCtrol")
        fanCtrol.startFanCtrol()
    else:
        fanCtrol.fanSpeedSetMax()
        fanwarningdebuglog(DEBUG_FANCONTROL,"%%policy:getBoardMonitorMsg error")
    
def doLedCtrol(fanCtrol):
    fanCtrol.getBoardMonitorMsg(ledcontrol = True) # 获取状态
    fanCtrol.dealSysLedStatus()        # 点系统灯
    fanCtrol.dealSysFanLedStatus()     # 点面板风扇灯
    fanCtrol.dealLocFanLedStatus()     # 点风扇本体灯
    fanCtrol.dealPsuLedStatus()        # 点面板PSU灯
    fanCtrol.dealSlotLedStatus()       # 点子卡状态灯
    fanwarningdebuglog(DEBUG_LEDCONTROL,"%%ledcontrol:doLedCtrol success")

def run(interval, fanCtrol):
    loop = 0
    while True:
        try:
            if loop % MONITOR_CONST.MONITOR_INTERVAL ==0: # 风扇调速
                fanwarningdebuglog(DEBUG_FANCONTROL,"%%policy:fanCtrol")
                doFanCtrol(fanCtrol)
            else:
                fanwarningdebuglog(DEBUG_LEDCONTROL,"%%ledcontrol:start ledctrol")# LED控制
                doLedCtrol(fanCtrol)
            time.sleep(interval)
            loop += interval
        except Exception as e:
            traceback.print_exc()
            fanerror(str(e))

@click.group(cls=AliasedGroup, context_settings=CONTEXT_SETTINGS)
def main():
    '''device operator'''
    pass
    
@main.command()
def start():
    '''start fan control'''
    fanwarninglog("FANCTROL start")
    fanCtrol = FanControl()
    interval = MONITOR_CONST.MONITOR_INTERVAL /30
    run(interval, fanCtrol)

@main.command()
def stop():
    '''stop fan control '''
    fanwarninglog("stop")

##device_i2c operation
if __name__ == '__main__':
    main()
