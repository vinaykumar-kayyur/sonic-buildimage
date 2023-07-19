#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @Time    : 2023/6/19 17:01
# @Mail    : yajiang@celestica.com
# @Author  : jiang tao
# @Function: Perform fan PWM PID control according to the CPU temperature provided by the Thermal team

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
CPU_TEMPERATURE = "cat /sys/class/thermal/thermal_zone0/temp"

# PID Defaults Value
PWM_LIST = [35]  # [PWMk-1]
T_LIST = []  # [Tk-2, Tk-1, Tk]
Kp = 2.1
Ki = 0.3
Kd = 0.5
SET_POINT = 96
PWM_MIN = 35
PWM_MAX = 100


class CPUPIDRegulation(object):
    """
    Make a class we can use to capture stdout and sterr in the log
    """
    # static temp var
    _ori_temp = 0
    _new_perc = DUTY_MAX / 2
    syslog = logging.getLogger("[" + FUNCTION_NAME + "]")
    init_fan_temperature = [0, 0]

    def __init__(self, log_file, log_level):
        """Needs a logger and a logger level."""
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

    def get_cpu_temperature(self):
        """
        Get CPU temperature
        """
        try:
            temp = int(os.popen(CPU_TEMPERATURE).read().strip()) / 1000
            return temp
        except Exception as E:
            self.syslog.warning("Can't Get CPU temperature! Cause:%s" % str(E))
            logging.warning("Can't Get CPU temperature! Cause:%s" % str(E))
            return False

    def pid_control(self):
        """
        PID adjustment according to Switch Internal Temperature
        :return: fans pwm
        """
        if len(T_LIST) < 3:
            cpu_temp = self.get_cpu_temperature()
            if cpu_temp:
                T_LIST.append(float(cpu_temp))
                logging.info("Init CPU PID Control T_LIST:%s" % T_LIST)
                return PWM_LIST[0]
            else:
                return DUTY_MAX
        else:
            cpu_temp = self.get_cpu_temperature()
            if cpu_temp:
                T_LIST.append(float(cpu_temp))
            else:
                return DUTY_MAX
            pwm_k = PWM_LIST[0] + Kp * (T_LIST[2] - T_LIST[1]) + \
                Ki * (T_LIST[2] - SET_POINT) + \
                Kd * (T_LIST[2] - 2 * T_LIST[1] + T_LIST[0])
            if pwm_k < PWM_MIN:
                logging.info("CPU PID PWM calculation value < %d, %d will be used"
                             % (PWM_MIN, PWM_MIN))
                pwm_k = PWM_MIN
            elif pwm_k > PWM_MAX:
                logging.info("CPU PID PWM calculation value > %d, %d will be used"
                             % (PWM_MAX, PWM_MAX))
                pwm_k = PWM_MAX
            PWM_LIST[0] = pwm_k
            T_LIST.pop(0)
            logging.info("CPU PID: PWM=%d Temp list=%s" % (pwm_k, T_LIST))
            return pwm_k
