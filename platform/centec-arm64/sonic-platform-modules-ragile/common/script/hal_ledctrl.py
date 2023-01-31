#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import inspect
import os
import sys
import json
import time
import syslog
import traceback
from plat_hal.interface import *
from plat_hal.baseutil import baseutil

SWITCH_TEMP     = "SWITCH_TEMP"
INLET_TEMP      = "INLET_TEMP"
BOARD_TEMP      = "BOARD_TEMP"
OUTLET_TEMP     = "OUTLET_TEMP"
CPU_TEMP        = "CPU_TEMP"

FRONT_SYS_LED   = "FRONT_SYS_LED"
BACK_SYS_LED    = "BACK_SYS_LED"
FRONT_BMC_LED   = "FRONT_BMC_LED"
BACK_BMC_LED    = "BACK_BMC_LED"
FRONT_PSU_LED   = "FRONT_PSU_LED"
FRONT_FAN_LED   = "FRONT_FAN_LED"

LEDCTROL_DEBUG_FILE = "/etc/.ledcontrol_debug_flag"

LEDCTROLERROR   = 1
LEDCTROLDEBUG   = 2

debuglevel = 0

def ledcontrol_debug(s):
    if LEDCTROLDEBUG & debuglevel:
        syslog.openlog("LEDCONTROL", syslog.LOG_PID)
        syslog.syslog(syslog.LOG_DEBUG, s)

def ledcontrol_error(s):
    if LEDCTROLERROR & debuglevel:
        syslog.openlog("LEDCONTROL", syslog.LOG_PID)
        syslog.syslog(syslog.LOG_ERR, s)

class ledcontrol(object):
    __int_case = None

    __interval = 30

    __temps_threshold_config = None

    def __init__(self):
        self.__fanerrnum = 0
        self.__psuerrnum = 0
        self.int_case = interface()

        self.__config = baseutil.get_monitor_config()
        self.__temps_threshold_config = self.__config["temps_threshold"]
        for temp_threshold in self.__temps_threshold_config.values():
            temp_threshold['temp'] = 0
            temp_threshold['fail_num'] = 0
        self.__ledcontrol_para = self.__config["ledcontrol_para"]
        self.__interval = self.__ledcontrol_para.get("interval")
        self.__checkpsu = self.__ledcontrol_para.get("checkpsu", 0)
        self.__checkfan = self.__ledcontrol_para.get("checkfan", 0)
        self.__psu_yellow_num = self.__ledcontrol_para.get("psu_yellow_num")
        self.__fan_yellow_num = self.__ledcontrol_para.get("fan_yellow_num")
        self.__board_sys_led = self.__ledcontrol_para.get("board_sys_led")
        self.__board_psu_led = self.__ledcontrol_para.get("board_psu_led")
        self.__board_fan_led = self.__ledcontrol_para.get("board_fan_led")

    @property
    def fanerrnum(self):
        return self.__fanerrnum

    @fanerrnum.setter
    def fanerrnum(self, value):
        self.__fanerrnum = value

    @property
    def psuerrnum(self):
        return self.__psuerrnum

    @psuerrnum.setter
    def psuerrnum(self, value):
        self.__psuerrnum = value

    def debug_init(self):
        global debuglevel
        if os.path.exists(LEDCTROL_DEBUG_FILE):
            debuglevel = debuglevel | LEDCTROLDEBUG | LEDCTROLERROR
        else:
            debuglevel = debuglevel & ~(LEDCTROLDEBUG | LEDCTROLERROR)

    def get_monitor_temp(self):
        sensorlist = self.int_case.get_temp_info()

        for temp_threshold in self.__temps_threshold_config.values():
            sensor = sensorlist.get(temp_threshold['name'])
            if sensor["Value"] == None:
                temp_threshold['fail_num'] += 1
                ledcontrol_error("get %s failed, fail_num = %d" % (temp_threshold['name'], temp_threshold['fail_num']))
            else:
                temp_threshold['fail_num'] = 0
                temp_threshold.setdefault('fix', 0)
                temp_threshold['temp'] = sensor["Value"] + temp_threshold['fix']
            ledcontrol_debug("%s = %d" % (temp_threshold['name'], temp_threshold['temp']))
            ledcontrol_debug("warning = %d, critical = %d" % (temp_threshold['warning'], temp_threshold['critical']))

    def is_temp_warning(self):
        warning_flag = False
        for temp_threshold in self.__temps_threshold_config.values():
            if temp_threshold['temp'] >= temp_threshold['warning']:
                warning_flag = True
                ledcontrol_debug("%s is over warning" % temp_threshold['name'])
                ledcontrol_debug("%s = %d, warning = %d" % (temp_threshold['name'], temp_threshold['temp'], temp_threshold['warning']))
        return warning_flag

    def checkTempWarning(self):
        try:
            if self.is_temp_warning():
                ledcontrol_debug("temp is over warning")
                return True
        except Exception as e:
            ledcontrol_error("%%policy: checkTempWarning failed")
            ledcontrol_error(str(e))
        return False

    def is_temp_critical(self):
        critical_flag = False
        for temp_threshold in self.__temps_threshold_config.values():
            temp_threshold['critical_flag'] = False
            if temp_threshold['temp'] >= temp_threshold['critical']:
                critical_flag = True
                temp_threshold['critical_flag'] = True
                ledcontrol_debug("%s is over critical" % temp_threshold['name'])
                ledcontrol_debug("%s = %d, critical = %d" % (temp_threshold['name'], temp_threshold['temp'], temp_threshold['critical']))
        return critical_flag

    def checkTempCrit(self):
        try:
            if self.is_temp_critical():
                temp_dict = dict(self.__temps_threshold_config)
                tmp = temp_dict.get(SWITCH_TEMP)
                if tmp['critical_flag'] == True:
                    ledcontrol_debug("temp is over critical")
                    return True

                del temp_dict[SWITCH_TEMP]
                for temp_items in temp_dict.values():
                    if temp_items['critical_flag'] == False:
                        return False

                ledcontrol_debug("temp is over critical")
                return True
        except Exception as e:
            ledcontrol_error("%%policy: checkTempCrit failed")
            ledcontrol_error(str(e))
        return False

    def set_led_color(self, led_name, color, blink=False):
            return self.int_case.set_led_color(led_name, color, blink)

    def set_fan_led(self, fan_name, color, blink=False):
        return self.int_case.set_fan_led(fan_name, color, blink)

    def get_fan_total_number(self):
        return self.int_case.get_fan_total_number()

    def get_rotor_number(self, fan_name):
        return self.int_case.get_fan_rotor_number(fan_name)

    def get_fan_presence(self, fan_name):
        return self.int_case.get_fan_presence(fan_name)

    def get_fan_rotor_status(self, fan_name, rotor_name):
        return self.int_case.get_fan_rotor_status(fan_name, rotor_name)

    def get_psu_total_number(self):
        return self.int_case.get_psu_total_number()

    def get_psu_presence(self, psu_name):
        return self.int_case.get_psu_presence(psu_name)

    def get_psu_input_output_status(self, psu_name):
        return self.int_case.get_psu_input_output_status(psu_name)

    def get_monitor_fan(self):
        try:
            fanerrnum = 0
            fan_num = self.get_fan_total_number()
            for i in range(fan_num):
                fan_name = "FAN" + str(i + 1)
                present_status = self.get_fan_presence(fan_name)
                if present_status == False:
                    fanerrnum += 1
                    ledcontrol_debug("%s absent" % fan_name)
                    continue
                ledcontrol_debug("%s presence" % fan_name)
                rotor_num = self.get_rotor_number(fan_name)
                color = "green"
                err_motor_num = 0
                for j in range(rotor_num):
                    rotor_name = "Rotor" + str(j + 1)
                    roll_status = self.get_fan_rotor_status(fan_name, rotor_name)
                    if roll_status == False:
                        err_motor_num += 1
                        color = "red"
                        ledcontrol_debug("%s %s error" % (fan_name, rotor_name))
                    else:
                        ledcontrol_debug("%s %s ok" % (fan_name, rotor_name))
                self.set_fan_led(fan_name, color)
                ledcontrol_debug("set %s led success, color:%s," % (fan_name, color))
                if err_motor_num > 0:
                    fanerrnum += 1
            self.fanerrnum = fanerrnum
            ledcontrol_debug("fan error number:%d" % self.fanerrnum)
        except Exception as e:
            ledcontrol_error("%%policy: get_monitor_fan failed")
            ledcontrol_error(str(e))

    def get_monitor_psu(self):
        try:
            psuerrnum = 0
            psu_num = self.get_psu_total_number()
            for i in range(psu_num):
                psu_name = "PSU" + str(i + 1)
                present = self.get_psu_presence(psu_name)
                status = self.get_psu_input_output_status(psu_name)
                ledcontrol_debug("%s present:%s, status:%s" % (psu_name, present, status))
                if present == False or status == False:
                    psuerrnum += 1
            self.psuerrnum = psuerrnum
            ledcontrol_debug("psu error number:%d" % self.psuerrnum)
        except Exception as e:
            ledcontrol_error("%%policy: get_monitor_psu failed")
            ledcontrol_error(str(e))

    def dealSysLedStatus(self):
        try:
            if ((self.checkTempCrit() == True) or 
                (self.__checkfan and (self.fanerrnum > self.__fan_yellow_num)) or 
                (self.__checkpsu and (self.psuerrnum > self.__psu_yellow_num))):
                color = "red"
            elif ((self.checkTempWarning() == True) or
                (self.__checkfan and (self.fanerrnum > 0)) or 
                (self.__checkpsu and (self.psuerrnum > 0))):
                color = "yellow"
            else:
                color = "green"
            for led in self.__board_sys_led:
                led_name = led.get("led_name")
                self.set_led_color(led_name, color)
                ledcontrol_debug("deal %s success, color:%s," % (led_name, color))
        except Exception as e:
            ledcontrol_error(str(e))

    def dealFanLedStatus(self):
        try:
            if self.fanerrnum == 0:
                color = "green"
            elif self.fanerrnum <= self.__fan_yellow_num:
                color = "yellow"
            else:
                color = "red"
            for led in self.__board_fan_led:
                led_name = led.get("led_name")
                self.set_led_color(led_name, color)
                ledcontrol_debug("deal %s success, color:%s," % (led_name, color))
        except Exception as e:
            ledcontrol_error(str(e))

    def dealPsuLedStatus(self):
        try:
            if self.psuerrnum == 0:
                color = "green"
            elif self.psuerrnum <= self.__psu_yellow_num:
                color = "yellow"
            else:
                color = "red"
            for led in self.__board_psu_led:
                led_name = led.get("led_name")
                self.set_led_color(led_name, color)
                ledcontrol_debug("deal %s success, color:%s," % (led_name, color))
        except Exception as e:
            ledcontrol_error(str(e))

    def do_ledcontrol(self):
        self.get_monitor_temp()
        self.get_monitor_psu()
        self.get_monitor_fan()
        self.dealSysLedStatus()
        self.dealFanLedStatus()
        self.dealPsuLedStatus()

    def run(self):
        while True:
            try:
                self.debug_init()
                self.do_ledcontrol()
                time.sleep(self.__interval)
            except Exception as e:
                traceback.print_exc()
                ledcontrol_error(str(e))


if __name__ == '__main__':
    ledcontrol_debug("enter main")
    led_control = ledcontrol()
    led_control.run()


