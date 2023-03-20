#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# memoryutil.py
# Platform-specific MEMORY status interface for SONiC
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

MEMORY_CONFIG = {
    "num":"4",
    "attr_list":[
        [   {"attr":"name","data":"memory1", "gettype":"direct_config"},
            {"attr":"model", "cmd":"cat /etc/sonic/.plugins/memory_info |grep -A 10 *-bank:0 |grep -B 10 *-bank:1 |grep product |cut -d : -f 2", "gettype":"cmd"},
            {"attr":"vendor", "cmd":"cat /etc/sonic/.plugins/memory_info |grep -A 10 *-bank:0 | grep -B 10 *-bank:1 |grep vendor |cut -d : -f 2", "gettype":"cmd"},
            {"attr":"size", "cmd":"cat /etc/sonic/.plugins/memory_info |grep -A 10 *-bank:0 | grep -B 10 *-bank:1 |grep size |cut -d : -f 2", "gettype":"cmd"},
            {"attr":"description", "cmd":"cat /etc/sonic/.plugins/memory_info |grep -A 10 *-bank:0 | grep -B 10 *-bank:1 |grep description |cut -d : -f 2", "gettype":"cmd"},
        ],
        [   {"attr":"name","data":"memory2", "gettype":"direct_config"},
            {"attr":"model", "cmd":"cat /etc/sonic/.plugins/memory_info |grep -A 10 *-bank:1 |grep -B 10 *-bank:2 |grep product |cut -d : -f 2", "gettype":"cmd"},
            {"attr":"vendor", "cmd":"cat /etc/sonic/.plugins/memory_info |grep -A 10 *-bank:1 | grep -B 10 *-bank:2 |grep vendor |cut -d : -f 2", "gettype":"cmd"},
            {"attr":"size", "cmd":"cat /etc/sonic/.plugins/memory_info |grep -A 10 *-bank:1 | grep -B 10 *-bank:2 |grep size |cut -d : -f 2", "gettype":"cmd"},
            {"attr":"description", "cmd":"cat /etc/sonic/.plugins/memory_info |grep -A 10 *-bank:1 | grep -B 10 *-bank:2 |grep description |cut -d : -f 2", "gettype":"cmd"},
        ],
        [   {"attr":"name","data":"memory3", "gettype":"direct_config"},
            {"attr":"model", "cmd":"cat /etc/sonic/.plugins/memory_info |grep -A 10 *-bank:2 |grep -B 10 *-bank:3 |grep product |cut -d : -f 2", "gettype":"cmd"},
            {"attr":"vendor", "cmd":"cat /etc/sonic/.plugins/memory_info |grep -A 10 *-bank:2 | grep -B 10 *-bank:3 |grep vendor |cut -d : -f 2", "gettype":"cmd"},
            {"attr":"size", "cmd":"cat /etc/sonic/.plugins/memory_info |grep -A 10 *-bank:2 | grep -B 10 *-bank:3 |grep size |cut -d : -f 2", "gettype":"cmd"},
            {"attr":"description", "cmd":"cat /etc/sonic/.plugins/memory_info |grep -A 10 *-bank:2 | grep -B 10 *-bank:3 |grep description |cut -d : -f 2", "gettype":"cmd"},
        ],
        [   {"attr":"name","data":"memory4", "gettype":"direct_config"},
            {"attr":"model", "cmd":"cat /etc/sonic/.plugins/memory_info |grep -A 10 *-bank:3 |grep -B 10 *-cache:0 |grep product |cut -d : -f 2", "gettype":"cmd"},
            {"attr":"vendor", "cmd":"cat /etc/sonic/.plugins/memory_info |grep -A 10 *-bank:3 | grep -B 10 *-cache:0 |grep vendor |cut -d : -f 2", "gettype":"cmd"},
            {"attr":"size", "cmd":"cat /etc/sonic/.plugins/memory_info |grep -A 10 *-bank:3 | grep -B 10 *-cache:0 |grep size |cut -d : -f 2", "gettype":"cmd"},
            {"attr":"description", "cmd":"cat /etc/sonic/.plugins/memory_info |grep -A 10 *-bank:3 | grep -B 10 *-cache:0 |grep description |cut -d : -f 2", "gettype":"cmd"},
        ],
    ],
}

class MemoryUtil(MonBase):
    def __init__(self):
        MonBase.__init__(self)

    def get_info(self):
        plugins = Plugins()
        self.info = plugins.get_data(MEMORY_CONFIG, 1)
        return json.dumps(self.info, ensure_ascii = False,indent=4)