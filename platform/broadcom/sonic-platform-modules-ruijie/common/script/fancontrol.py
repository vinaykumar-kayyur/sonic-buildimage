#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import click
import os
import commands
import time
from ruijieutil import *
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
        matches = [x for x in self.list_commands(ctx) if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))


def fanwarninglog(s):
    #s = s.decode('utf-8').encode('gb2312')
    syslog.openlog("FANCONTROL", syslog.LOG_PID)
    syslog.syslog(syslog.LOG_WARNING, s)


def fancriticallog(s):
    #s = s.decode('utf-8').encode('gb2312')
    syslog.openlog("FANCONTROL", syslog.LOG_PID)
    syslog.syslog(syslog.LOG_CRIT, s)


def fanerror(s):
    #s = s.decode('utf-8').encode('gb2312')
    syslog.openlog("FANCONTROL", syslog.LOG_PID)
    syslog.syslog(syslog.LOG_ERR, s)


def fanwarningdebuglog(debuglevel, s):
    #s = s.decode('utf-8').encode('gb2312')
    if FANCTROLDEBUG & debuglevel:
        syslog.openlog("FANCONTROL", syslog.LOG_PID)
        syslog.syslog(syslog.LOG_DEBUG, s)


class FanControl():
    critnum = 0

    def __init__(self):
        self._fan_ok_num = 0
        self._psu_ok_num = 0
        self._intemp     = -100.0
        self._mac_aver   = -100.0
        self._mac_max    = -100.0
        self._pre_intemp = -1000  # previous temperature
        self._outtemp    = -100
        self._boardtemp  = -100
        self._cputemp    = -1000
        pass

    @property
    def fan_ok_num(self):
        return self._fan_ok_num

    @property
    def psu_ok_num(self):
        return self._psu_ok_num

    @property
    def cputemp(self):
        return self._cputemp

    @property
    def intemp(self):
        return self._intemp

    @property
    def outtemp(self):
        return self._outtemp

    @property
    def boardtemp(self):
        return self._boardtemp

    @property
    def mac_aver(self):
        return self._mac_aver

    @property
    def pre_intemp(self):
        return self._pre_intemp

    @property
    def mac_max(self):
        return self._mac_max

    def sort_callback(self, element):
        return element['id']

    def get_current_speed(self):
        try:
            loc = fanloc[0].get("location", "")
            sped = get_sysfs_value(loc)
            value = strtoint(sped)
            return value
        except Exception as e:
            fanerror("%%policy: get current speedlevel error")
            fanerror(str(e))
            return None

    # lower than the latest after speed regulation is the lowest
    def check_current_speed_set(self):
        fanwarningdebuglog(DEBUG_FANCONTROL, "%%policy: lowest rpm regulation")
        value = self.get_current_speed()
        if value is None or value == 0:
            raise Exception("%%policy: get current speed None")
        elif value < MONITOR_CONST.MIN_SPEED:
            self.fan_speed_set(MONITOR_CONST.MIN_SPEED)

    def fan_speed_set(self, level):
        if level >= MONITOR_CONST.MAX_SPEED:
            level = MONITOR_CONST.MAX_SPEED
        for item in fanloc:
            try:
                loc = item.get("location", "")
                write_sysfs_value(loc, "0x%02x" % level)
            except Exception as e:
                fanerror(str(e))
                fanerror("%%policy: config fan run level error")
        self.check_current_speed_set()  # make sure current is the lowest speed

    def fan_speed_set_max(self):
        try:
            self.fan_speed_set(MONITOR_CONST.MAX_SPEED)
        except Exception as e:
            fanerror("%%policy:fanSpeedSetMax failed")
            fanerror(str(e))

    def fan_status_check(self):  # if any errors are detected, turn the fan into the highest speed
        if self.fan_ok_num < MONITOR_CONST.FAN_TOTAL_NUM:
            fanwarninglog("%%FANCONTRL-FAILED_NORMALFAN_NUM : %d" %
                          (self.fan_ok_num))
            self.fan_speed_set_max()
            return False
        return True

    def get_cpu_temp(self, cputemp):
        for i, item in enumerate(cputemp):
            if item["name"] == "Physical id 0":
                self._cputemp = float(item["temp"])
        fanwarningdebuglog(DEBUG_COMMON, "cputemp:%f" % self._cputemp)

    def get_cpu_status(self):
        try:
            cputemp = []
            status.getcputemp(cputemp)
            self.get_cpu_temp(cputemp)
            fanwarningdebuglog(DEBUG_COMMON, "%%policy:getCpuStatus success")
            return 0
        except AttributeError as e:
            fanerror(str(e))
        except Exception as e:
            fanerror(str(e))
        return -1

    def set_fan_attr(self, val):
        """set the state of each fan"""
        for item in val:
            fanid = item.get("id")
            fanattr = fanid + "status"
            fanstatus = item.get("errmsg")
            setattr(FanControl, fanattr, fanstatus)
            fanwarningdebuglog(DEBUG_COMMON,
                               "fanattr:%s,fanstatus:%s" % (fanattr, fanstatus))

    def get_fan_present_num(self, cur_fan_status):
        fanoknum = 0
        for i, item in enumerate(cur_fan_status):
            if item["errcode"] == 0:
                fanoknum += 1
        self._fan_ok_num = fanoknum
        fanwarningdebuglog(DEBUG_COMMON, "fanOKNum = %d" % self._fan_ok_num)

    def get_fan_status(self):
        try:
            cur_fan_status = []
            status.checkFan(cur_fan_status)
            cur_fan_status.sort(key=self.sort_callback)
            self.set_fan_attr(cur_fan_status)
            self.get_fan_present_num(cur_fan_status)
            fanwarningdebuglog(DEBUG_COMMON, "%%policy:getFanStatus success")
            return 0
        except AttributeError as e:
            fanerror(str(e))
        except Exception as e:
            fanerror(str(e))
        return -1

    def get_psu_ok_num(self, cur_psu_status):
        psuoknum = 0
        for i, item in enumerate(cur_psu_status):
            if item["errcode"] == 0:
                psuoknum += 1
        self._psu_ok_num = psuoknum
        fanwarningdebuglog(DEBUG_COMMON, "psuOKNum = %d" % self._psu_ok_num)

    def get_psu_status(self):
        try:
            cur_psu_status = []
            status.getPsu(cur_psu_status)
            cur_psu_status.sort(key=self.sort_callback)
            self.get_psu_ok_num(cur_psu_status)
            fanwarningdebuglog(DEBUG_COMMON, "%%policy:getPsuStatus success")
            return 0
        except AttributeError as e:
            fanerror(str(e))
        except Exception as e:
            fanerror(str(e))
        return -1

    def get_monitor_intemp(self, temp):
        for i, item in enumerate(temp):
            if item["id"] == "lm75in":
                self._intemp = float(item["temp1_input"])
            if item["id"] == "lm75out":
                self._outtemp = float(item["temp1_input"])
            if item["id"] == "lm75hot":
                self._boardtemp = float(item["temp1_input"])
        fanwarningdebuglog(
            DEBUG_COMMON, "intemp:%f, outtemp:%f, boadrtemp:%f" %
            (self._intemp, self._outtemp, self._boardtemp))

    def get_temp_status(self):
        try:
            monitortemp = []
            status.getTemp(monitortemp)
            monitortemp.sort(key=self.sort_callback)
            self.get_monitor_intemp(monitortemp)
            fanwarningdebuglog(DEBUG_COMMON, "%%policy:getTempStatus success")
            return 0
        except AttributeError as e:
            fanerror(str(e))
        except Exception as e:
            fanerror(str(e))
        return -1

    def get_mac_status(self):
        try:
            sta, ret = get_MAC_temp()
            if sta == True:
                self._mac_aver = float(ret["average"])
                self._mac_max = float(ret["maximum"])
                fanwarningdebuglog(DEBUG_COMMON,
                        "mac_aver:%f, mac_max:%f" % (self.mac_aver, self._mac_max))
            else:
                fanwarningdebuglog(DEBUG_COMMON, "%%policy:getMacStatus failed")
            return 0
        except AttributeError as e:
            fanerror(str(e))
        return -1

    def set_slot_attr(self, val):
        """set line-card state"""
        for item in val:
            slotid = item.get("id")
            slotattr = slotid + "status"
            slotstatus = item.get("errmsg")
            setattr(FanControl, slotattr, slotstatus)
            fanwarningdebuglog(DEBUG_COMMON,
                "slotattr:%s,slotstatus:%s" % (slotattr, slotstatus))

    def get_slot_status(self):
        try:
            cur_slot_status = []
            if hasattr(status, 'checkSlot'):
                status.checkSlot(cur_slot_status)
                cur_slot_status.sort(key=self.sort_callback)
                self.set_slot_attr(cur_slot_status)
                fanwarningdebuglog(DEBUG_COMMON, "%%policy:getSlotStatus success")
            else:
                pass
        except AttributeError as e:
            fanerror(str(e))
        return 0

    def fanctrol(self):
        try:
            if self.pre_intemp <= -1000:
                self.pre_intemp = self.intemp
            fanwarningdebuglog(DEBUG_FANCONTROL,
                    "%%policy:previous temp [%.2f] , current temp [%.2f]" % (self.pre_intemp, self.intemp))
            if self.intemp < MONITOR_CONST.TEMP_MIN:
                fanwarningdebuglog(DEBUG_FANCONTROL,
                        "%%policy:inlet %.2f min temp: %.2f" % (self.intemp, MONITOR_CONST.TEMP_MIN))
                self.fan_speed_set(MONITOR_CONST.DEFAULT_SPEED)
            elif self.intemp >= MONITOR_CONST.TEMP_MIN and self.intemp > self.pre_intemp:
                fanwarningdebuglog(DEBUG_FANCONTROL, "%%policy: temp rised")
                self.policy_speed(self.intemp)
            elif self.intemp >= MONITOR_CONST.TEMP_MIN and ( self.pre_intemp - self.intemp) > MONITOR_CONST.MONITOR_FALL_TEMP:
                fanwarningdebuglog(DEBUG_FANCONTROL,
                        "%%policy: temp drops by more then %d degrees" % MONITOR_CONST.MONITOR_FALL_TEMP)
                self.policy_speed(self.intemp)
                pass
            else:
                speed = self.get_current_speed()  # feed watchdog with current rpm
                if speed is not None:
                    self.fan_speed_set(speed)
                fanwarningdebuglog(DEBUG_FANCONTROL, "%%policy: nothing changed")
        except Exception as e:
            fanerror("%%policy: fancontrol error")

    def start_fan_ctrol(self):
        if self.fan_status_check() == True:
            self.check_dev_error()
            self.check_crit()
            if self.critnum == 0:
                if self.check_warning() == False:
                    self.fanctrol()
        fanwarningdebuglog(DEBUG_FANCONTROL,
                "%%policy: speed regulated:  %0x" % (self.get_current_speed()))

    def policy_speed(self, temp):  # policy of fan regulation
        fanwarningdebuglog(DEBUG_FANCONTROL, "%%policy: speed regulate with formula")
        sped_level = MONITOR_CONST.DEFAULT_SPEED + MONITOR_CONST.K * (temp - MONITOR_CONST.TEMP_MIN)
        self.fan_speed_set(sped_level)
        self.pre_intemp = self.intemp

    def get_board_monitor_msg(self, ledcontrol=False):
        ret_t = 0
        try:
            ret_t += self.get_fan_status()  # number of fans in normal status
            ret_t += self.get_temp_status() # inlet, outlet and highest temperatures
            ret_t += self.get_cpu_status()  # CPU's temperature
            ret_t += self.get_mac_status()  # MAC's highest & avg temperatures
            if ledcontrol == True:
                ret_t += self.get_slot_status() # line-card state
                ret_t += self.get_psu_status()  # numbers of psu
            if ret_t == 0:
                return True
        except Exception as e:
            fanerror(str(e))
        return False

    # error policy    Tmac-Tin≥50℃ or Tmac-Tin≤-50℃
    def check_dev_error(self):
        try:
            if (self.mac_aver - self.intemp) >= MONITOR_CONST.MAC_UP_TEMP \
            or (self.mac_aver - self.intemp) <= MONITOR_CONST.MAC_LOWER_TEMP:
                fanwarninglog("%%FANCONTRL-0-MAC_TEMP_ERROR: %.2f  %.2f" %
                              (self.mac_aver, self.intemp))
                value = self.get_current_speed()
                if MONITOR_CONST.MAC_ERROR_SPEED >= value:
                    self.fan_speed_set(MONITOR_CONST.MAC_ERROR_SPEED)
                else:
                    self.fan_speed_set_max()
                    pass
            else:
                pass
        except Exception as e:
            fanerror("%%policy: checkDevError failed")
            fanerror(str(e))

    def check_temp_warn(self):
        """exceeded the normal threshold"""
        try:
            if self._mac_aver >= MONITOR_CONST.MAC_WARNING_THRESHOLD \
            or self._outtemp >= MONITOR_CONST.OUTTEMP_WARNING_THRESHOLD \
            or self._boardtemp >= MONITOR_CONST.BOARDTEMP_WARNING_THRESHOLD \
            or self._cputemp>=MONITOR_CONST.CPUTEMP_WARNING_THRESHOLD \
            or self._intemp >=MONITOR_CONST.INTEMP_WARNING_THRESHOLD:
                fanwarningdebuglog(DEBUG_COMMON, "temp alarm: normal")
                return True
        except Exception as e:
            fanerror("%%policy: checkTempWarning failed")
            fanerror(str(e))
        return False

    def check_temp_crit(self):
        """exceeded the critical threshold"""
        try:
            if self._mac_aver >= MONITOR_CONST.MAC_CRITICAL_THRESHOLD \
            or ( self._outtemp >= MONITOR_CONST.OUTTEMP_CRITICAL_THRESHOLD \
            and self._boardtemp >= MONITOR_CONST.BOARDTEMP_CRITICAL_THRESHOLD \
            and self._cputemp>= MONITOR_CONST.CPUTEMP_CRITICAL_THRESHOLD \
            and self._intemp >= MONITOR_CONST.INTEMP_CRITICAL_THRESHOLD):
                fanwarningdebuglog(DEBUG_COMMON, "temp alarm: critical")
                return True
        except Exception as e:
            fanerror("%%policy: checkTempCrit failed")
            fanerror(str(e))
        return False

    def check_fan_status(self):
        for item in MONITOR_FAN_STATUS:
            maxoknum = item.get('maxOkNum')
            minoknum = item.get('minOkNum')
            status = item.get('status')
            if self.fan_ok_num >= minoknum and self.fan_ok_num <= maxoknum:
                fanwarningdebuglog(
                    DEBUG_COMMON, "checkFanStatus:fanOKNum:%d,status:%s" %
                    (self.fan_ok_num, status))
                return status
        fanwarningdebuglog(DEBUG_COMMON,
                           "checkFanStatus Error:fanOKNum:%d" % (self.fan_ok_num))
        return None

    def check_psu_status(self):
        for item in MONITOR_PSU_STATUS:
            maxoknum = item.get('maxOkNum')
            minoknum = item.get('minOkNum')
            status = item.get('status')
            if self.psu_ok_num >= minoknum and self.psu_ok_num <= maxoknum:
                fanwarningdebuglog(
                    DEBUG_COMMON, "checkPsuStatus:psuOKNum:%d,status:%s" %
                    (self.psu_ok_num, status))
                return status
        fanwarningdebuglog(DEBUG_COMMON,
                           "checkPsuStatus Error:psuOKNum:%d" % (self.psu_ok_num))
        return None

    def deal_sys_led_status(self):
        """set sys led with temperature, fans and psu status"""
        try:
            fanstatus = self.check_fan_status()
            psustatus = self.check_psu_status()
            if self.check_temp_crit() == True \
            or fanstatus == "red" \
            or psustatus == "red":
                status = "red"
            elif self.check_temp_warn() == True \
            or fanstatus == "yellow" \
            or psustatus == "yellow":
                status = "yellow"
            else:
                status = "green"
            self.set_sys_led(status)
            fanwarningdebuglog(DEBUG_LEDCONTROL,
                "%%ledcontrol:dealSysLedStatus success, status:%s," % status)
        except Exception as e:
            fanerror(str(e))

    def deal_sys_fan_led_status(self):
        """set sys fans led"""
        try:
            status = self.check_fan_status()
            if status is not None:
                self.set_sys_fan_led(status)
                fanwarningdebuglog(DEBUG_LEDCONTROL,
                    "%%ledcontrol:dealSysFanLedStatus success, status:%s," % status)
        except Exception as e:
            fanerror("%%ledcontrol:dealSysLedStatus error")
            fanerror(str(e))

    def deal_psu_led_status(self):
        """set psu led"""
        try:
            status = self.check_psu_status()
            if status is not None:
                self.set_sys_psu_led(status)
            fanwarningdebuglog(DEBUG_LEDCONTROL,
                "%%ledcontrol:dealPsuLedStatus success, status:%s," % status)
        except Exception as e:
            fanerror("%%ledcontrol:dealPsuLedStatus error")
            fanerror(str(e))

    def deal_loc_fan_led_status(self):
        """set fan led"""
        for item in MONITOR_FANS_LED:
            try:
                index = MONITOR_FANS_LED.index(item) + 1
                fanattr = "fan%dstatus" % index
                val_t = getattr(FanControl, fanattr, None)
                if val_t == "NOT OK":
                    rji2cset(item["bus"], item["devno"], item["addr"],
                             item["red"])
                elif val_t == "OK":
                    rji2cset(item["bus"], item["devno"], item["addr"],
                             item["green"])
                else:
                    pass
                fanwarningdebuglog(
                    DEBUG_LEDCONTROL,
                    "%%ledcontrol:dealLocFanLed success.fanattr:%s, status:%s" %
                    (fanattr, val_t))
            except Exception as e:
                fanerror("%%ledcontrol:dealLocFanLedStatus error")
                fanerror(str(e))

    def deal_slot_led_status(self):
        """set line-card led"""
        slot_led_list = DEV_LEDS.get("SLOTLED", [])
        for item in slot_led_list:
            try:
                index = slot_led_list.index(item) + 1
                slotattr = "slot%dstatus" % index
                val_t = getattr(FanControl, slotattr, None)
                if val_t == "PRESENT":
                    rji2cset(item["bus"], item["devno"], item["addr"],
                             item["green"])
                fanwarningdebuglog(
                    DEBUG_LEDCONTROL,
                    "%%ledcontrol:dealSlotLedStatus success.slotattr:%s, status:%s"
                    % (slotattr, val_t))
            except Exception as e:
                fanerror("%%ledcontrol:dealSlotLedStatus error")
                fanerror(str(e))

    def deal_bmc_led_status(self, val):
        pass

    def deal_lct_led_status(self, val):
        pass

    def set_sys_led(self, color):
        for item in MONITOR_SYS_LED:
            if item.get('type', 'i2c') == 'sysfs':
                rjsysset(item["cmdstr"], item.get(color))
            else:
                rji2cset(item["bus"], item["devno"], item["addr"],
                         item.get(color))

    def set_sys_fan_led(self, color):
        for item in MONITOR_SYS_FAN_LED:
            if item.get('type', 'i2c') == 'sysfs':
                rjsysset(item["cmdstr"], item.get(color))
            else:
                rji2cset(item["bus"], item["devno"], item["addr"],
                         item.get(color))

    def set_sys_psu_led(self, color):
        for item in MONITOR_SYS_PSU_LED:
            if item.get('type', 'i2c') == 'sysfs':
                rjsysset(item["cmdstr"], item.get(color))
            else:
                rji2cset(item["bus"], item["devno"], item["addr"],
                         item.get(color))

    def check_warning(self):
        try:
            if self.check_temp_warn() == True:
                fanwarningdebuglog(DEBUG_FANCONTROL, "start anti-jitter")
                time.sleep(MONITOR_CONST.SHAKE_TIME)
                fanwarningdebuglog(DEBUG_FANCONTROL, "stop anti-jitter")
                self.get_board_monitor_msg()  # read twice for anti-jitter
                if self.check_temp_warn() == True:
                    fanwarninglog("%%FANCONTROL-0-SYS_WARNING")
                    self.fan_speed_set_max()  # regulate the fan to max speed
                    return True
        except Exception as e:
            fanerror("%%policy: checkWarning failed")
            fanerror(str(e))
        return False

    def check_crit(self):
        try:
            if self.check_temp_crit() == True:
                fanwarningdebuglog(DEBUG_FANCONTROL, "start anti-jitter")
                time.sleep(MONITOR_CONST.SHAKE_TIME)
                fanwarningdebuglog(DEBUG_FANCONTROL, "stop anti-jitter")
                self.get_board_monitor_msg()
                if self.check_temp_crit() == True:
                    fancriticallog("%%FANCONTROL-0-SYS_CRIT")
                    self.fan_speed_set_max()
                    self.critnum += 1
                    if self.critnum >= MONITOR_CONST.CRITICAL_NUM:
                        os.system("reboot")
                    fanwarningdebuglog(DEBUG_FANCONTROL, "crit num:%d" % self.critnum)
                else:
                    self.critnum = 0
            else:
                self.critnum = 0
        except Exception as e:
            fanerror("%%policy: checkCrit failed")
            fanerror(str(e))


def callback():
    pass


def do_fan_ctrol(fanctrol):
    ret = fanctrol.get_board_monitor_msg()
    if ret == True:
        fanwarningdebuglog(DEBUG_FANCONTROL, "%%policy:startFanCtrol")
        fanctrol.start_fan_ctrol()
    else:
        fanctrol.fan_speed_set_max()
        fanwarningdebuglog(DEBUG_FANCONTROL, "%%policy:getBoardMonitorMsg error")


def do_led_ctrol(fanctrol):
    fanctrol.get_board_monitor_msg(ledcontrol=True) # get system status
    fanctrol.deal_sys_led_status()                  # turn on sys led
    fanctrol.deal_sys_fan_led_status()              # turn on sys fan led
    fanctrol.deal_loc_fan_led_status()              # turn on fan led
    fanctrol.deal_psu_led_status()                  # turn on psu led
    fanctrol.deal_slot_led_status()                 # turn on line-card led
    fanwarningdebuglog(DEBUG_LEDCONTROL, "%%ledcontrol:doLedCtrol success")


def run(interval, fanctrol):
    loop = 0
    while True:
        try:
            if loop % MONITOR_CONST.MONITOR_INTERVAL == 0:  # fan regulation
                fanwarningdebuglog(DEBUG_FANCONTROL, "%%policy:fanCtrol")
                do_fan_ctrol(fanctrol)
            else:
                fanwarningdebuglog(DEBUG_LEDCONTROL, "%%ledcontrol:start ledctrol")  # led control
                do_led_ctrol(fanctrol)
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
    fanctrol = FanControl()
    interval = MONITOR_CONST.MONITOR_INTERVAL / 30
    run(interval, fanctrol)


@main.command()
def stop():
    '''stop fan control '''
    fanwarninglog("stop")


##device_i2c operation
if __name__ == '__main__':
    main()
