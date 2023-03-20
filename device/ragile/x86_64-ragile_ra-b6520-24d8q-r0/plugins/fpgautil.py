#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# fpgautil.py
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

FPGA_CONFIG = {
    "num":1,
    "attr_list":[
        [   {"attr":"name","data":"fpga1", "gettype":"direct_config"},
            {"attr":"model", "loc":"/sys_switch/fpga/fpga1/type", "gettype":"sysfs"},
            {"attr":"vendor","data":"XILINX", "gettype":"direct_config"},
            {"attr":"alias", "loc":"/sys_switch/fpga/fpga1/alias", "gettype":"sysfs"},
            {"attr":"hardware_version", "loc":"/sys_switch/fpga/fpga1/board_version", "gettype":"sysfs"},
            {"attr":"firmware_version", "loc":"/sys_switch/fpga/fpga1/firmware_version", "gettype":"sysfs"},
        ],
    ]
}

class FpgaUtil(MonBase):
    def __init__(self):
        MonBase.__init__(self)

    def get_info(self):
        plugins = Plugins()
        self.info = plugins.get_data(FPGA_CONFIG, 1)
        return json.dumps(self.info, ensure_ascii = False,indent=4)