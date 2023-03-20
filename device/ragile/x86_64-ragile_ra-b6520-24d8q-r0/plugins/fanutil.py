#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# fanutil.py
# Platform-specific FAN status interface for SONiC
#

import os
import sys
import collections
import json

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from baseutil import *

try:
    from sonic_mon.mon_base import MonBase
except ImportError as e:
    raise ImportError (str(e) + "- required module not found")

FAN_CONFIG = {
    "num":6,
    "attr_list":[
        [   {"attr":"name","data":"fan1", "gettype":"direct_config"},
            {"attr":"presence", "loc":"/sys_switch/fan/fan1/status", "gettype":"sysfs", "ok_val":[1,2], "na_display_determinant":1},
            {"attr":"model", "loc":"/sys_switch/fan/fan1/model_name", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"serial", "loc":"/sys_switch/fan/fan1/serial_number", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"status", "loc":"/sys_switch/fan/fan1/status", "gettype":"sysfs", "ok_val":1, "display_na_affected":1},
            {"attr":"direction", "loc":"/sys_switch/fan/fan1/direction", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed1", "loc":"/sys_switch/fan/fan1/motor1/speed", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_tolerance1", "loc":"/sys_switch/fan/fan1/motor1/speed_tolerance", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_target1", "loc":"/sys_switch/fan/fan1/motor1/speed_target", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_ratio", "loc":"/sys_switch/fan/fan1/ratio", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed2", "loc":"/sys_switch/fan/fan1/motor2/speed", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_tolerance2", "loc":"/sys_switch/fan/fan1/motor2/speed_tolerance", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_target2", "loc":"/sys_switch/fan/fan1/motor2/speed_target", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"led_status", "loc":"/sys_switch/fan/fan1/led_status", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"firmware_version", "loc":"/sys_switch/fan/fan1/hardware_version", "gettype":"sysfs", "display_na_affected":1},
        ],
        [   {"attr":"name","data":"fan2", "gettype":"direct_config"},
            {"attr":"presence", "loc":"/sys_switch/fan/fan2/status", "gettype":"sysfs", "ok_val":[1,2], "na_display_determinant":1},
            {"attr":"model", "loc":"/sys_switch/fan/fan2/model_name", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"serial", "loc":"/sys_switch/fan/fan2/serial_number", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"status", "loc":"/sys_switch/fan/fan2/status", "gettype":"sysfs", "ok_val":1, "display_na_affected":1},
            {"attr":"direction", "loc":"/sys_switch/fan/fan2/direction", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed1", "loc":"/sys_switch/fan/fan2/motor1/speed", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_tolerance1", "loc":"/sys_switch/fan/fan2/motor1/speed_tolerance", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_target1", "loc":"/sys_switch/fan/fan2/motor1/speed_target", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_ratio", "loc":"/sys_switch/fan/fan2/ratio", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed2", "loc":"/sys_switch/fan/fan2/motor2/speed", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_tolerance2", "loc":"/sys_switch/fan/fan2/motor2/speed_tolerance", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_target2", "loc":"/sys_switch/fan/fan2/motor2/speed_target", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"led_status", "loc":"/sys_switch/fan/fan2/led_status", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"firmware_version", "loc":"/sys_switch/fan/fan2/hardware_version", "gettype":"sysfs", "display_na_affected":1},
        ],
        [   {"attr":"name","data":"fan3", "gettype":"direct_config"},
            {"attr":"presence", "loc":"/sys_switch/fan/fan3/status", "gettype":"sysfs", "ok_val":[1,2], "na_display_determinant":1},
            {"attr":"model", "loc":"/sys_switch/fan/fan3/model_name", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"serial", "loc":"/sys_switch/fan/fan3/serial_number", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"status", "loc":"/sys_switch/fan/fan3/status", "gettype":"sysfs", "ok_val":1, "display_na_affected":1},
            {"attr":"direction", "loc":"/sys_switch/fan/fan3/direction", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed1", "loc":"/sys_switch/fan/fan3/motor1/speed", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_tolerance1", "loc":"/sys_switch/fan/fan3/motor1/speed_tolerance", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_target1", "loc":"/sys_switch/fan/fan3/motor1/speed_target", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_ratio", "loc":"/sys_switch/fan/fan3/ratio", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed2", "loc":"/sys_switch/fan/fan3/motor2/speed", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_tolerance2", "loc":"/sys_switch/fan/fan3/motor2/speed_tolerance", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_target2", "loc":"/sys_switch/fan/fan3/motor2/speed_target", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"led_status", "loc":"/sys_switch/fan/fan3/led_status", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"firmware_version", "loc":"/sys_switch/fan/fan3/hardware_version", "gettype":"sysfs", "display_na_affected":1},
        ],
        [   {"attr":"name","data":"fan4", "gettype":"direct_config"},
            {"attr":"presence", "loc":"/sys_switch/fan/fan4/status", "gettype":"sysfs", "ok_val":[1,2], "na_display_determinant":1},
            {"attr":"model", "loc":"/sys_switch/fan/fan4/model_name", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"serial", "loc":"/sys_switch/fan/fan4/serial_number", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"status", "loc":"/sys_switch/fan/fan4/status", "gettype":"sysfs", "ok_val":1, "display_na_affected":1},
            {"attr":"direction", "loc":"/sys_switch/fan/fan4/direction", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed1", "loc":"/sys_switch/fan/fan4/motor1/speed", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_tolerance1", "loc":"/sys_switch/fan/fan4/motor1/speed_tolerance", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_target1", "loc":"/sys_switch/fan/fan4/motor1/speed_target", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_ratio", "loc":"/sys_switch/fan/fan4/ratio", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed2", "loc":"/sys_switch/fan/fan4/motor2/speed", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_tolerance2", "loc":"/sys_switch/fan/fan4/motor2/speed_tolerance", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_target2", "loc":"/sys_switch/fan/fan4/motor2/speed_target", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"led_status", "loc":"/sys_switch/fan/fan4/led_status", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"firmware_version", "loc":"/sys_switch/fan/fan4/hardware_version", "gettype":"sysfs", "display_na_affected":1},
        ],
        [   {"attr":"name","data":"fan5", "gettype":"direct_config"},
            {"attr":"presence", "loc":"/sys_switch/fan/fan5/status", "gettype":"sysfs", "ok_val":[1,2], "na_display_determinant":1},
            {"attr":"model", "loc":"/sys_switch/fan/fan5/model_name", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"serial", "loc":"/sys_switch/fan/fan5/serial_number", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"status", "loc":"/sys_switch/fan/fan5/status", "gettype":"sysfs", "ok_val":1, "display_na_affected":1},
            {"attr":"direction", "loc":"/sys_switch/fan/fan5/direction", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed1", "loc":"/sys_switch/fan/fan5/motor1/speed", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_tolerance1", "loc":"/sys_switch/fan/fan5/motor1/speed_tolerance", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_target1", "loc":"/sys_switch/fan/fan5/motor1/speed_target", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_ratio", "loc":"/sys_switch/fan/fan5/ratio", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed2", "loc":"/sys_switch/fan/fan5/motor2/speed", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_tolerance2", "loc":"/sys_switch/fan/fan5/motor2/speed_tolerance", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_target2", "loc":"/sys_switch/fan/fan5/motor2/speed_target", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"led_status", "loc":"/sys_switch/fan/fan5/led_status", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"firmware_version", "loc":"/sys_switch/fan/fan5/hardware_version", "gettype":"sysfs", "display_na_affected":1},
        ],
        [   {"attr":"name","data":"fan6", "gettype":"direct_config"},
            {"attr":"presence", "loc":"/sys_switch/fan/fan6/status", "gettype":"sysfs", "ok_val":[1,2], "na_display_determinant":1},
            {"attr":"model", "loc":"/sys_switch/fan/fan6/model_name", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"serial", "loc":"/sys_switch/fan/fan6/serial_number", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"status", "loc":"/sys_switch/fan/fan6/status", "gettype":"sysfs", "ok_val":1, "display_na_affected":1},
            {"attr":"direction", "loc":"/sys_switch/fan/fan6/direction", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed1", "loc":"/sys_switch/fan/fan6/motor1/speed", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_tolerance1", "loc":"/sys_switch/fan/fan6/motor1/speed_tolerance", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_target1", "loc":"/sys_switch/fan/fan6/motor1/speed_target", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_ratio", "loc":"/sys_switch/fan/fan6/ratio", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed2", "loc":"/sys_switch/fan/fan6/motor2/speed", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_tolerance2", "loc":"/sys_switch/fan/fan6/motor2/speed_tolerance", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"speed_target2", "loc":"/sys_switch/fan/fan6/motor2/speed_target", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"led_status", "loc":"/sys_switch/fan/fan6/led_status", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"firmware_version", "loc":"/sys_switch/fan/fan6/hardware_version", "gettype":"sysfs", "display_na_affected":1},
        ],
    ],
}

class FanUtil(MonBase):
    def __init__(self):
        MonBase.__init__(self)

    def get_info(self):
        plugins = Plugins()
        self.info = plugins.get_data(FAN_CONFIG, 1)
        return json.dumps(self.info, ensure_ascii = False,indent=4)

    def get_fan_num(self):
        num = 0
        node = "/sys_switch/fan/number"
        try:
            with open(node, 'r') as fans_num:
                num = int(fans_num.read().strip())
        except IOError:
            return 0
        return num

    def get_fan_presence(self, index):
        if index is None:
            return False

        status = 0
        node = "/sys_switch/fan/fan%s/status" % str(index)
        try:
            with open(node, 'r') as presence_status:
                status = int(presence_status.read().strip())
        except IOError:
            return False

        if status == 0:
            return False
        else:
            return True

    def get_fan_sn(self, index):
        if index is None:
            return "index is None"

        sn = ""
        node = "/sys_switch/fan/fan%s/serial_number" % str(index)
        try:
            with open(node, 'r') as f:
                sn = f.read().strip()
        except IOError:
            return "Fan {} sn read failed IOError".format(index)
        return sn

    def get_fan_type(self, index):
        if index is None:
            return "index is None"

        type = ""
        node = "/sys_switch/fan/fan%s/model_name" % str(index)
        try:
            with open(node, 'r') as f:
                type = f.read().strip()
        except IOError:
            return "Fan {} model read failed IOError".format(index)
        return type