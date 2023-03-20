#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# asicutil.py
# Platform-specific ASIC status interface for SONiC
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

ASIC_CONFIG = [
    {"attr":"model", "loc":"/etc/sonic/.plugins/asic_model", "gettype":"sysfs"},
    {"attr":"sdk_version", "loc":"/etc/sonic/.plugins/sdk_version", "gettype":"sysfs"},
    {"attr":"vendor", "data":"broadcom", "gettype":"direct_config"},
    {"attr":"phy_version", "data":"NA", "gettype":"direct_config"},
    {"attr":"pcie_firmware_version", "loc":"/etc/sonic/.plugins/pcie_fw_version", "gettype":"sysfs"},
    {
        "attr": "power_core", "loc": "/sys/bus/i2c/devices/43-005b/hwmon/*/power1_input",
        "gettype": "sysfs", "formula": "(%f)/1000000", "decimal_precision": 1, "unit": "W"
    },
    {
        "attr": "power_analog", "loc": "/sys/bus/i2c/devices/43-005b/hwmon/*/power2_input",
        "gettype": "sysfs", "formula": "(%f)/1000000", "decimal_precision": 1, "unit": "W"
    },
]

class AsicUtil(MonBase):
    def __init__(self):
        MonBase.__init__(self)

    def get_info(self):
        plugins = Plugins()
        self.info = plugins.get_data(ASIC_CONFIG, 2)
        return json.dumps(self.info, ensure_ascii = False,indent=4)