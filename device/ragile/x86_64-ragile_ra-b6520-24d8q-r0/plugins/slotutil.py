#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# slotutil.py
# Platform-specific SLOT status interface for SONiC
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

SLOT_CONFIG = {
    "num":0,
    "attr_list":[
    ],
}

class SlotUtil(MonBase):
    def __init__(self):
        MonBase.__init__(self)

    def get_info(self):
        plugins = Plugins()
        self.info = plugins.get_data(SLOT_CONFIG, 1)
        return json.dumps(self.info, ensure_ascii = False,indent=4)