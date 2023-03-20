#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# cpldutil.py
# Platform-specific CPLD status interface for SONiC
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

CPLD_CONFIG = {
    "num":5,
    "attr_list":[
        [   {"attr":"name","data":"cpld1", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/cpld/cpld1/type", "gettype":"sysfs"},
            {"attr":"vendor","data":"LATTICE", "gettype":"direct_config"},
            {"attr":"alias", "loc":"/sys_switch/cpld/cpld1/alias", "gettype":"sysfs"},
            {"attr":"hardware_version", "loc":"/sys_switch/cpld/cpld1/board_version", "gettype":"sysfs"},
            {"attr":"firmware_version", "loc":"/sys_switch/cpld/cpld1/firmware_version", "gettype":"sysfs"},
        ],
        [   {"attr":"name","data":"cpld2", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/cpld/cpld2/type", "gettype":"sysfs"},
            {"attr":"vendor","data":"LATTICE", "gettype":"direct_config"},
            {"attr":"alias", "loc":"/sys_switch/cpld/cpld2/alias", "gettype":"sysfs"},
            {"attr":"hardware_version", "loc":"/sys_switch/cpld/cpld2/board_version", "gettype":"sysfs"},
            {"attr":"firmware_version", "loc":"/sys_switch/cpld/cpld2/firmware_version", "gettype":"sysfs"},
        ],
        [   {"attr":"name","data":"cpld3", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/cpld/cpld3/type", "gettype":"sysfs"},
            {"attr":"vendor","data":"LATTICE", "gettype":"direct_config"},
            {"attr":"alias", "loc":"/sys_switch/cpld/cpld3/alias", "gettype":"sysfs"},
            {"attr":"hardware_version", "loc":"/sys_switch/cpld/cpld3/board_version", "gettype":"sysfs"},
            {"attr":"firmware_version", "loc":"/sys_switch/cpld/cpld3/firmware_version", "gettype":"sysfs"},
        ],
        [   {"attr":"name","data":"cpld4", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/cpld/cpld4/type", "gettype":"sysfs"},
            {"attr":"vendor","data":"LATTICE", "gettype":"direct_config"},
            {"attr":"alias", "loc":"/sys_switch/cpld/cpld4/alias", "gettype":"sysfs"},
            {"attr":"hardware_version", "loc":"/sys_switch/cpld/cpld4/board_version", "gettype":"sysfs"},
            {"attr":"firmware_version", "loc":"/sys_switch/cpld/cpld4/firmware_version", "gettype":"sysfs"},
        ],
        [   {"attr":"name","data":"cpld5", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/cpld/cpld5/type", "gettype":"sysfs"},
            {"attr":"vendor","data":"LATTICE", "gettype":"direct_config"},
            {"attr":"alias", "loc":"/sys_switch/cpld/cpld5/alias", "gettype":"sysfs"},
            {"attr":"hardware_version", "loc":"/sys_switch/cpld/cpld5/board_version", "gettype":"sysfs"},
            {"attr":"firmware_version", "loc":"/sys_switch/cpld/cpld5/firmware_version", "gettype":"sysfs"},
        ],
    ],
}

class CpldUtil(MonBase):
    def __init__(self):
        MonBase.__init__(self)

    def get_info(self):
        plugins = Plugins()
        self.info = plugins.get_data(CPLD_CONFIG, 1)
        return json.dumps(self.info, ensure_ascii = False,indent=4)