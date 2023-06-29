#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @Time    : 2023/6/19 16:26
# @Mail    : yajiang@celestica.com
# @Author  : jiang tao
# @Function: Perform fan PWM PID control according to the Switch Internal temperature provided by the Thermal team

try:
    import os
    import sys
    import getopt
    import subprocess
    import logging
    import logging.config
    import time  # this is only being used as part of the example
    import signal
    from sonic_platform import platform
except ImportError as e:
    raise ImportError('%s - required module not found' % str(e))

# Defaults
FUNCTION_NAME = 'FanControl'
DUTY_MAX = 100
SWITCH_INTERNAL_PATH = "/sys/devices/platform/fpga_sysfs/getreg"

# PID Defaults Value
PWM_LIST = [35]  # [PWMk-1]
T_LIST = []  # [Tk-2, Tk-1, Tk]
Kp = 3
Ki = 0.3
Kd = 0.5
SET_POINT = 100
PWM_MIN = 35
PWM_MAX = 100


class SwitchInternalPIDRegulation(object):
    """
    Make a class we can use to capture stdout and sterr in the log
    """
    _new_perc = DUTY_MAX / 2
    syslog = logging.getLogger("[" + FUNCTION_NAME + "]")

    def __init__(self, log_file, log_level):
        # Needs a logger and a logger level
        formatter = logging.Formatter('%(name)s %(message)s')
        sys_handler = logging.handlers.SysLogHandler(address='/dev/log')
        sys_handler.setFormatter(formatter)
        sys_handler.ident = 'common'
        self.syslog.setLevel(logging.WARNING)
        self.syslog.addHandler(sys_handler)
        self.platform_chassis_obj = platform.Platform().get_chassis()
        # set up logging to file
        logging.basicConfig(
            filename=log_file,
            filemode='w',
            level=log_level,
            format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )

        # set up logging to console
        if log_level == logging.DEBUG:
            console = logging.StreamHandler()
            console.setLevel(log_level)
            formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
            console.setFormatter(formatter)
            logging.getLogger('').addHandler(console)
        logging.debug('SET. logfile:%s / loglevel:%d' % (log_file, log_level))

    def get_switch_internal_temperature(self):
        """
        Get Switch internal temperature
        """
        try:
            os.popen("echo 0x78 > %s" % SWITCH_INTERNAL_PATH)
            value_1 = os.popen("cat %s" % SWITCH_INTERNAL_PATH).read().strip()
            os.popen("echo 0x80 > %s" % SWITCH_INTERNAL_PATH)
            value_2 = os.popen("cat %s" % SWITCH_INTERNAL_PATH).read().strip()
            freq = int(value_2, 16)
            freq = freq * 256 + int(value_1, 16)
            temp = (434100 - ((12500000 / freq - 1) * 535)) / 1000
            return int(temp)
        except Exception as E:
            self.syslog.warning("Can't Get switch internal temperature! Cause:%s" % str(E))
            logging.warning("Can't Get switch internal temperature! Cause:%s" % str(E))
            return False

    def pid_control(self):
        """
        PID adjustment according to Switch Internal Temperature
        :return: fans pwm
        """
        if len(T_LIST) < 3:
            sw_temp = self.get_switch_internal_temperature()
            if sw_temp:
                T_LIST.append(float(sw_temp))
                self.syslog.debug("Init PID Control T_LIST:%s" % T_LIST)
                logging.info("Init PID Control T_LIST:%s" % T_LIST)
                return PWM_LIST[0]
            else:
                return DUTY_MAX
        else:
            sw_temp = self.get_switch_internal_temperature()
            if sw_temp:
                T_LIST.append(float(sw_temp))
            else:
                return DUTY_MAX
            pwm_k = PWM_LIST[0] + Kp * (T_LIST[2] - T_LIST[1]) + \
                Ki * (T_LIST[2] - SET_POINT) + \
                Kd * (T_LIST[2] - 2 * T_LIST[1] + T_LIST[0])
            if pwm_k < PWM_MIN:
                logging.info("Switch Internal PID PWM calculation value < %d, %d will be used"
                             % (PWM_MIN, PWM_MIN))
                pwm_k = PWM_MIN
            elif pwm_k > PWM_MAX:
                logging.info("Switch Internal PID PWM calculation value > %d, %d will be used"
                             % (PWM_MAX, PWM_MAX))
                pwm_k = PWM_MAX
            PWM_LIST[0] = pwm_k
            T_LIST.pop(0)
            logging.info("Switch Internal PID: PWM=%d" % pwm_k)
            return pwm_k
