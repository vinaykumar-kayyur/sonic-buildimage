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
from algorithm.pid import pid
from algorithm.openloop import openloop

SWITCH_TEMP     = "SWITCH_TEMP"
INLET_TEMP      = "INLET_TEMP"
BOARD_TEMP      = "BOARD_TEMP"
OUTLET_TEMP     = "OUTLET_TEMP"
CPU_TEMP        = "CPU_TEMP"

FANCTROL_DEBUG_FILE = "/etc/.fancontrol_debug_flag"

FANCTROLERROR   = 1
FANCTROLDEBUG   = 2

debuglevel = 0

def fancontrol_debug(s):
    if FANCTROLDEBUG & debuglevel:
        syslog.openlog("FANCONTROL", syslog.LOG_PID)
        syslog.syslog(syslog.LOG_DEBUG, s)

def fancontrol_error(s):
    if FANCTROLERROR & debuglevel:
        syslog.openlog("FANCONTROL", syslog.LOG_PID)
        syslog.syslog(syslog.LOG_ERR, s)

class fancontrol(object):
    __int_case = None

    __pwm = 0x80
    __critnum = 0

    def __init__(self):
        self.int_case = interface()
        self.__config = baseutil.get_monitor_config()
        self.__pid_config = self.__config["pid"]
        self.__temps_threshold_config = self.__config["temps_threshold"]
        for temp_threshold in self.__temps_threshold_config.values():
            temp_threshold['temp'] = 0
            temp_threshold['fail_num'] = 0

        self.__fancontrol_para = self.__config["fancontrol_para"]
        self.__interval = self.__fancontrol_para.get("interval")
        self.__max_pwm = self.__fancontrol_para.get("max_pwm")
        self.__min_pwm = self.__fancontrol_para.get("min_pwm")
        self.__abnormal_pwm = self.__fancontrol_para.get("abnormal_pwm")
        self.__temp_fail_num = self.__fancontrol_para.get("temp_fail_num")
        self.__check_temp_fail = self.__fancontrol_para.get("check_temp_fail")
        self.__inlet_mac_diff = self.__fancontrol_para.get("inlet_mac_diff")
        self.__check_crit_reboot_num = self.__fancontrol_para.get("check_crit_reboot_num")
        self.__check_crit_sleep_time = self.__fancontrol_para.get("check_crit_sleep_time")
        self.__psu_absent_fullspeed_num = self.__fancontrol_para.get("psu_absent_fullspeed_num")
        self.__fan_absent_fullspeed_num = self.__fancontrol_para.get("fan_absent_fullspeed_num")
        self.__rotor_error_fullspeed_num = self.__fancontrol_para.get("rotor_error_fullspeed_num")
        self.openloop = openloop()
        self.pid = pid()

        self.__pwm = self.__min_pwm

    def debug_init(self):
        global debuglevel
        if os.path.exists(FANCTROL_DEBUG_FILE):
            debuglevel = debuglevel | FANCTROLDEBUG | FANCTROLERROR
        else:
            debuglevel = debuglevel & ~(FANCTROLDEBUG | FANCTROLERROR)

    def get_para(self, type):
        para = self.__pid_config.get(type)
        return para

    def get_monitor_temp(self):
        sensorlist = self.int_case.get_temp_info()

        for temp_threshold in self.__temps_threshold_config.values():
            sensor = sensorlist.get(temp_threshold['name'])
            if sensor["Value"] == None:
                temp_threshold['fail_num'] += 1
                fancontrol_error("get %s failed, fail_num = %d" % (temp_threshold['name'], temp_threshold['fail_num']))
            else:
                temp_threshold['fail_num'] = 0
                temp_threshold.setdefault('fix', 0)
                temp_threshold['temp'] = sensor["Value"] + temp_threshold['fix']
            fancontrol_debug("%s = %d" % (temp_threshold['name'], temp_threshold['temp']))
            fancontrol_debug("warning = %d, critical = %d" % (temp_threshold['warning'], temp_threshold['critical']))

    def is_temp_warning(self):
        warning_flag = False
        for temp_threshold in self.__temps_threshold_config.values():
            if temp_threshold['temp'] >= temp_threshold['warning']:
                warning_flag = True
                fancontrol_debug("%s is over warning" % temp_threshold['name'])
                fancontrol_debug("%s = %d, warning = %d" % (temp_threshold['name'], temp_threshold['temp'], temp_threshold['warning']))
        return warning_flag

    def checkTempWarning(self):
        try:
            if self.is_temp_warning():
                fancontrol_debug("temp is over warning")
                return True
        except Exception as e:
            fancontrol_error("%%policy: checkTempWarning failed")
            fancontrol_error(str(e))
        return False

    def is_temp_critical(self):
        critical_flag = False
        for temp_threshold in self.__temps_threshold_config.values():
            temp_threshold['critical_flag'] = False
            if temp_threshold['temp'] >= temp_threshold['critical']:
                critical_flag = True
                temp_threshold['critical_flag'] = True
                fancontrol_debug("%s is over critical" % temp_threshold['name'])
                fancontrol_debug("%s = %d, critical = %d" % (temp_threshold['name'], temp_threshold['temp'], temp_threshold['critical']))
        return critical_flag

    def checkTempCrit(self):
        try:
            if self.is_temp_critical():
                temp_dict = dict(self.__temps_threshold_config)
                tmp = temp_dict.get(SWITCH_TEMP)
                if tmp['critical_flag'] == True:
                    fancontrol_debug("temp is over critical")
                    return True

                del temp_dict[SWITCH_TEMP]
                for temp_items in temp_dict.values():
                    if temp_items['critical_flag'] == False:
                        return False

                fancontrol_debug("temp is over critical")
                return True
        except Exception as e:
            fancontrol_error("%%policy: checkTempCrit failed")
            fancontrol_error(str(e))
        return False

    def checkCritReboot(self):
        try:
            if self.checkTempCrit() == True:
                time.sleep(self.__check_crit_sleep_time)
                self.get_monitor_temp()# Read it again
                if self.checkTempCrit() == True:
                    fancontrol_debug("The temperature of device is over critical value.")
                    self.__critnum += 1 # Image stabilization
                    if self.__critnum >= self.__check_crit_reboot_num:
                        print("The temperature of device is over critical value.")
                        print("The system is going to reboot now.")
                        time.sleep(3)
                        os.system("reboot")
                    fancontrol_debug("critnum:%d" % self.__critnum)
                else:
                    self.__critnum = 0
            else:
                self.__critnum = 0
        except Exception as e:
            fancontrol_error("%%policy: checkCritReboot failed")
            fancontrol_error(str(e))

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

    def checkFanPresence(self):
        absent_num = 0
        fan_num = self.get_fan_total_number()
        for i in range(fan_num):
            fan_name = "FAN" + str(i + 1)
            status = self.get_fan_presence(fan_name)
            if status == False:
                absent_num = absent_num + 1
                fancontrol_debug("%s absent" % fan_name)
            else:
                fancontrol_debug("%s presence" % fan_name)
        return absent_num

    def checkFanRotorStatus(self):
        err_num = 0
        fan_num = self.get_fan_total_number()
        for i in range(fan_num):
            fan_name = "FAN" + str(i + 1)
            rotor_num = self.get_rotor_number(fan_name)
            for j in range(rotor_num):
                rotor_name = "Rotor" + str(j + 1)
                status = self.get_fan_rotor_status(fan_name, rotor_name)
                if status == False:
                    err_num = err_num + 1
                    fancontrol_debug("%s %s error" % (fan_name, rotor_name))
                else:
                    fancontrol_debug("%s %s ok" % (fan_name, rotor_name))
        return err_num

    def checkPsuPresence(self):
        absent_num = 0
        psu_num = self.get_psu_total_number()
        for i in range(psu_num):
            psu_name = "PSU" + str(i + 1)
            status = self.get_psu_presence(psu_name)
            if status == False:
                absent_num = absent_num + 1
                fancontrol_debug("%s absent" % psu_name)
            else:
                fancontrol_debug("%s presence" % psu_name)
        return absent_num

    def checkPsuStatus(self):
        err_num = 0
        psu_num = self.get_psu_total_number()
        for i in range(psu_num):
            psu_name = "PSU" + str(i + 1)
            status = self.get_psu_input_output_status(psu_name)
            if status == False:
                err_num = err_num + 1
                fancontrol_debug("%s error" % psu_name)
            else:
                fancontrol_debug("%s ok" % psu_name)
        return err_num

    def checkDevError(self):
        pwm = self.__min_pwm
        switchtemp = self.__temps_threshold_config.get(SWITCH_TEMP)['temp']
        inlettemp = self.__temps_threshold_config.get(INLET_TEMP)['temp']
        temp_diff = abs(switchtemp - inlettemp)
        fancontrol_debug("|switchtemp - inlettemp| = %d" % temp_diff)
        if temp_diff >= self.__inlet_mac_diff:
            fancontrol_debug("temp_diff is over than inlet_mac_diff(%d)" % self.__inlet_mac_diff)
            if self.__pwm > self.__abnormal_pwm:
                pwm = self.__max_pwm
            else:
                pwm = self.__abnormal_pwm
        return pwm

    def checktempfail(self):
        pwm = self.__min_pwm
        for temp in self.__check_temp_fail:
            temp_name = temp.get("temp_name")
            temp_fail_num = self.__temps_threshold_config.get(temp_name)['fail_num']
            if temp_fail_num >= self.__temp_fail_num:
                pwm = self.__abnormal_pwm
                fancontrol_debug("%s temp_fail_num = %d" % (temp_name, temp_fail_num))
                fancontrol_debug("self.__temp_fail_num = %d" % self.__temp_fail_num)
        return pwm

    def abnormal_check(self):
        pwm_list = []
        pwm_min = self.__min_pwm
        pwm_list.append(pwm_min)
        status = self.checkTempCrit()
        if status == True:
            over_crit_pwm = self.__max_pwm
            pwm_list.append(over_crit_pwm)
            fancontrol_debug("over_crit_pwm = 0x%x" % over_crit_pwm)
            # do reset check
            self.checkCritReboot()

        status = self.checkTempWarning()
        if status == True:
            over_warn_pwm = self.__max_pwm
            pwm_list.append(over_warn_pwm)
            fancontrol_debug("over_warn_pwm = 0x%x" % over_warn_pwm)

        fan_absent_num = self.checkFanPresence()
        if fan_absent_num >= self.__fan_absent_fullspeed_num:
            fan_absent_pwm = self.__max_pwm
            pwm_list.append(fan_absent_pwm)
            fancontrol_debug("fan_absent_pwm = 0x%x" % fan_absent_pwm)

        rotor_err_num = self.checkFanRotorStatus()
        if rotor_err_num >= self.__rotor_error_fullspeed_num:
            rotor_err_pwm = self.__max_pwm
            pwm_list.append(rotor_err_pwm)
            fancontrol_debug("rotor_err_pwm = 0x%x" % rotor_err_pwm)

        psu_absent_num = self.checkPsuPresence()
        if psu_absent_num >= self.__psu_absent_fullspeed_num:
            psu_absent_pwm = self.__max_pwm
            pwm_list.append(psu_absent_pwm)
            fancontrol_debug("psu_absent_pwm = 0x%x" % psu_absent_pwm)

        dev_err_pwm = self.checkDevError()
        pwm_list.append(dev_err_pwm)
        fancontrol_debug("dev_err_pwm = 0x%x" % dev_err_pwm)

        temp_fail_pwm = self.checktempfail()
        pwm_list.append(temp_fail_pwm)
        fancontrol_debug("temp_fail_pwm = 0x%x" % temp_fail_pwm)

        pwm = max(pwm_list)
        return pwm


    def do_fancontrol(self):
        pwm_list = []
        pwm_min = self.__min_pwm
        pwm_list.append(pwm_min)

        self.get_monitor_temp()
        fancontrol_debug("last_pwm = 0x%x" % self.__pwm)
        # openloop
        inlettemp = self.__temps_threshold_config.get(INLET_TEMP)['temp']
        linear_value = self.openloop.linear_cacl(inlettemp)
        if linear_value == None:
            linear_value = self.__min_pwm
        pwm_list.append(linear_value)
        fancontrol_debug("linear_value = 0x%x" % linear_value)

        curve_value = self.openloop.curve_cacl(inlettemp)
        if curve_value == None:
            curve_value = self.__min_pwm
        pwm_list.append(curve_value)
        fancontrol_debug("curve_value = 0x%x" % curve_value)

        # pid
        for pid_index in self.__pid_config.values():
            temp_name = pid_index['name']
            tmp_temp = self.__temps_threshold_config.get(temp_name)['temp']
            pid_value = self.pid.cacl(self.__pwm, temp_name, tmp_temp)
            if pid_value == None:
                pid_value = self.__min_pwm
            pwm_list.append(pid_value)
            fancontrol_debug("%s pid_value = 0x%x" % (temp_name, pid_value))

        # abnormal
        abnormal_value = self.abnormal_check()
        pwm_list.append(abnormal_value)
        fancontrol_debug("abnormal_value = 0x%x" % abnormal_value)

        self.__pwm = max(pwm_list)
        fancontrol_debug("__pwm = 0x%x\n" % self.__pwm)
        self.set_all_fan_speed_pwm(self.__pwm)

    def run(self):
        while True:
            try:
                self.debug_init()
                self.do_fancontrol()
                time.sleep(self.__interval)
            except Exception as e:
                traceback.print_exc()
                fancontrol_error(str(e))

    def set_all_fan_speed_pwm(self, pwm):
        self.fan_set_speed_pwm(pwm);
        self.set_psu_fan_speed_pwm(pwm);

    def get_fans(self):
        return self.int_case.get_fans()

    def get_speed(self, fan_name, rotor_index):
        return self.int_case.get_fan_speed(fan_name, rotor_index)

    def get_speed_pwm(self, fan_name, rotor_index):
        return self.int_case.get_fan_speed_pwm(fan_name, rotor_index)

    def fan_get_speed_pwm(self):
        fans = self.get_fans()
        for fan in  fans:
            rotor_len = self.get_rotor_number(fan.name)
            for i in range(rotor_len):
                fancontrol_debug("%s rotor%d: %d" % (fan.name, i + 1, self.get_speed_pwm(fan.name, i + 1)))

    def fan_set_speed_pwm(self, pwm):
        duty = round(pwm * 100 / 255)
        fans = self.get_fans()
        for fan in fans:
            rotor_len = self.get_rotor_number(fan.name)
            for i in range(rotor_len):
                val = self.int_case.set_fan_speed_pwm(fan.name, i + 1, duty)
                if val != 0:
                    fancontrol_error("%s rotor%d: %d" % (fan.name, i + 1, val))

    def set_psu_fan_speed_pwm(self, pwm):
        duty = round(pwm * 100 / 255)
        psu_num = self.get_psu_total_number()
        for i in range(psu_num):
            psu_name = "PSU" + str(i + 1)
            status = self.int_case.set_psu_fan_speed_pwm(psu_name, int(duty))
            if status != True:
                fancontrol_error("set %s speed fail" % psu_name)


if __name__ == '__main__':
    fancontrol_debug("enter main")
    fan_control = fancontrol()
    fan_control.run()


