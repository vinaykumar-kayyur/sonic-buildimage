#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# platform_miscutil.py
# Platform-specific PLATFORM_MISC status interface for SONiC
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

PLATFORM_MISC_CONFIG = [
    {"attr":"bios_vendor", "cmd":"cat /etc/sonic/.plugins/bios_info |grep Vendor |cut -d : -f 2", "gettype":"cmd"},
    {"attr":"bios_version", "cmd":"cat /etc/sonic/.plugins/bios_info |grep Version |cut -d : -f 2", "gettype":"cmd"},
    {"attr":"bmc_model", "data":"AST 2520", "gettype":"direct_config"},
    {"attr":"bmc_version", "cmd":"ipmitool mc info |grep \"Firmware Revision\" |cut -d : -f 2", "gettype":"cmd"},
    {"attr":"onie_version", "cmd":"cat /etc/sonic/.plugins/machine.conf |grep onie_version |cut -d = -f 2", "gettype":"cmd"},
    {"attr":"cpu_model", "cmd":"cat /etc/sonic/.plugins/processor_info |grep Version |cut -d : -f 2", "gettype":"cmd"},
    {"attr":"cpu_core", "cmd":"cat /etc/sonic/.plugins/processor_info |grep \"Core Count\" |cut -d : -f 2", "gettype":"cmd"},
    {"attr":"cpu_thread", "cmd":"cat /etc/sonic/.plugins/processor_info |grep \"Thread Count\" |cut -d : -f 2", "gettype":"cmd"},
    {"attr":"nic_model", "data":"I210", "gettype":"direct_config"},
    {"attr":"nic_vendor", "data":"INTEL", "gettype":"direct_config"},
    {"attr":"nic_firmware_version", "loc":"/etc/sonic/.plugins/mgmt_version", "gettype":"sysfs"},
    {"attr":"cpu_bmc_switch_model", "cmd":"cat /etc/sonic/.plugins/bcm5387_info |grep \"Device Model\"|cut -d : -f 2", "gettype":"cmd"},
    {"attr":"cpu_bmc_switch_version", "cmd":"cat /etc/sonic/.plugins/bcm5387_info |grep \"Hardware Version\"|cut -d : -f 2", "gettype":"cmd"},
]

class Platform_MiscUtil(MonBase):
    def __init__(self):
        MonBase.__init__(self)

    def get_info(self):
        plugins = Plugins()
        self.info = plugins.get_data(PLATFORM_MISC_CONFIG, 2)
        return json.dumps(self.info, ensure_ascii = False,indent=4)