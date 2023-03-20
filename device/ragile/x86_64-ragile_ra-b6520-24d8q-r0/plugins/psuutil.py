#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# psuutil.py
# Platform-specific PSU status interface for SONiC
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

PSU_CONFIG = {
    "num":2,
    "attr_list":[
        [   {"attr":"name","data":"psu1", "gettype":"direct_config"},
            {"attr":"presence", "loc":"/sys_switch/psu/psu1/present", "gettype":"sysfs", "ok_val":1, "na_display_determinant":1},
            {"attr":"model", "loc":"/sys_switch/psu/psu1/model_name", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"serial", "loc":"/sys_switch/psu/psu1/serial_number", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"status", "loc":"/sys_switch/psu/psu1/out_status", "gettype":"sysfs", "ok_val":1, "display_na_affected":1},
            {"attr":"in_type", "loc":"/sys_switch/psu/psu1/type", "gettype":"sysfs", "display_na_affected":1, "decode": {"0": "DC", "1": "AC"}},
            {"attr":"fan_speed", "loc":"/sys_switch/psu/psu1/fan_speed", "gettype":"sysfs", "unit":"RPM", "display_na_affected":1},
            {
                "attr":"temp", "loc":"/sys_switch/psu/psu1/temp1/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C", "display_na_affected":1
            },
            {
                "attr":"in_vol", "loc":"/sys_switch/psu/psu1/in_vol", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"V", "display_na_affected":1
            },
            {
                "attr":"in_power", "loc":"/sys_switch/psu/psu1/in_power", "gettype":"sysfs",
                "formula": "(%f)/1000000", "decimal_precision":1, "unit":"W", "display_na_affected":1
            },
            {
                "attr":"in_curr", "loc":"/sys_switch/psu/psu1/in_curr", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"A", "display_na_affected":1
            },
            {
                "attr":"out_vol", "loc":"/sys_switch/psu/psu1/out_vol", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"V", "display_na_affected":1
            },
            {
                "attr":"out_power", "loc":"/sys_switch/psu/psu1/out_power", "gettype":"sysfs",
                "formula": "(%f)/1000000", "decimal_precision":1, "unit":"W", "display_na_affected":1
            },
            {
                "attr":"out_curr", "loc":"/sys_switch/psu/psu1/out_curr", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"A", "display_na_affected":1
            },
            {"attr":"led_status", "loc":"/sys_switch/psu/psu1/led_status", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"firmware_version", "loc":"/sys_switch/psu/psu1/hardware_version", "gettype":"sysfs", "display_na_affected":1},
        ],
        [   {"attr":"name","data":"psu2", "gettype":"direct_config"},
            {"attr":"presence", "loc":"/sys_switch/psu/psu2/present", "gettype":"sysfs", "ok_val":1, "na_display_determinant":1},
            {"attr":"model", "loc":"/sys_switch/psu/psu2/model_name", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"serial", "loc":"/sys_switch/psu/psu2/serial_number", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"status", "loc":"/sys_switch/psu/psu2/out_status", "gettype":"sysfs", "ok_val":1, "display_na_affected":1},
            {"attr":"in_type", "loc":"/sys_switch/psu/psu2/type", "gettype":"sysfs", "display_na_affected":1, "decode": {"0": "DC", "1": "AC"}},
            {"attr":"fan_speed", "loc":"/sys_switch/psu/psu2/fan_speed", "gettype":"sysfs", "unit":"RPM", "display_na_affected":1},
            {
                "attr":"temp", "loc":"/sys_switch/psu/psu2/temp1/value", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"C", "display_na_affected":1
            },
            {
                "attr":"in_vol", "loc":"/sys_switch/psu/psu2/in_vol", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"V", "display_na_affected":1
            },
            {
                "attr":"in_power", "loc":"/sys_switch/psu/psu2/in_power", "gettype":"sysfs",
                "formula": "(%f)/1000000", "decimal_precision":1, "unit":"W", "display_na_affected":1
            },
            {
                "attr":"in_curr", "loc":"/sys_switch/psu/psu2/in_curr", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"A", "display_na_affected":1
            },
            {
                "attr":"out_vol", "loc":"/sys_switch/psu/psu2/out_vol", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"V", "display_na_affected":1
            },
            {
                "attr":"out_power", "loc":"/sys_switch/psu/psu2/out_power", "gettype":"sysfs",
                "formula": "(%f)/1000000", "decimal_precision":1, "unit":"W", "display_na_affected":1
            },
            {
                "attr":"out_curr", "loc":"/sys_switch/psu/psu2/out_curr", "gettype":"sysfs",
                "formula": "(%f)/1000", "decimal_precision":1, "unit":"A", "display_na_affected":1
            },
            {"attr":"led_status", "loc":"/sys_switch/psu/psu2/led_status", "gettype":"sysfs", "display_na_affected":1},
            {"attr":"firmware_version", "loc":"/sys_switch/psu/psu2/hardware_version", "gettype":"sysfs", "display_na_affected":1},
        ],
    ],
}

class PsuUtil(MonBase):
    def __init__(self):
        MonBase.__init__(self)

    def get_info(self):
        plugins = Plugins()
        self.info = plugins.get_data(PSU_CONFIG, 1)
        return json.dumps(self.info, ensure_ascii = False,indent=4)

    def get_num_psus(self):
        num = 0
        node = "/sys_switch/psu/number"
        try:
            with open(node, 'r') as psus_num:
                num = int(psus_num.read().strip())
        except IOError:
            return 0
        return num

    def get_psu_status(self, index):
        if index is None:
            return False

        node = "/sys_switch/psu/psu" + str(index) + "/out_status"
        try:
            with open(node, 'r') as sysfs_status:
                status = int(sysfs_status.read().strip())
            if status == 1:
                return True
        except IOError:
            pass
        return False

    def get_psu_presence(self, index):
        if index is None:
            return False

        node = "/sys_switch/psu/psu" + str(index) + "/present"
        try:
            with open(node, 'r') as sysfs_status:
                status = int(sysfs_status.read().strip())
            if status == 1:
                return True
        except IOError:
            pass
        return False

    def get_psu_sn(self, index):
        if index is None:
            return "index is None"

        sn = ""
        node = "/sys_switch/psu/psu" + str(index) + "/serial_number"
        try:
            with open(node, 'r') as f:
                sn = f.read().strip()
        except IOError:
            return "Psu {} sn read failed IOError".format(index)
        return sn

    def get_psu_type(self, index):
        if index is None:
            return "index is None"

        type = ""
        node = "/sys_switch/psu/psu" + str(index) + "/model_name"
        try:
            with open(node, 'r') as f:
                type = f.read().strip()
        except IOError:
            return "Psu {} model read failed IOError".format(index)
        return type