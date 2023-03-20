#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# diskutil.py
# Platform-specific DISK status interface for SONiC
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

DISK_CONFIG = {
    "num":1,
    "attr_list":[
        [   {"attr":"name","data":"disk1", "gettype":"direct_config"},
            {"attr":"model", "cmd":"cat /etc/sonic/.plugins/ssd_info |grep \"Device Model\" |cut -d : -f 2", "gettype":"cmd"},
            {"attr":"vendor", "data":"NA", "gettype":"direct_config"},
            {"attr":"size", "cmd":"cat /etc/sonic/.plugins/ssd_info |grep \"User Capacity\" |cut -d [ -f 2 | cut -d ] -f 1", "gettype":"cmd"},
            {"attr":"firmware_version", "cmd":"cat /etc/sonic/.plugins/ssd_info |grep \"Firmware Version\" |cut -d : -f 2", "gettype":"cmd"},
        ],
    ],
}

class DiskUtil(MonBase):
    def __init__(self):
        MonBase.__init__(self)

    def get_info(self):
        plugins = Plugins()
        self.info = plugins.get_data(DISK_CONFIG, 1)
        return json.dumps(self.info, ensure_ascii = False,indent=4)