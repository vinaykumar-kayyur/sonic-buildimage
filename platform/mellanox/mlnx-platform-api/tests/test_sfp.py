import os
import sys

test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
sys.path.insert(0, modules_path)

from sonic_py_common import device_info
from sonic_platform.sfp import SFP
from sonic_platform.chassis import Chassis


def mock_get_platform():
    return 'x86_64-mlnx_msn2410-r0'


def mock_read_eeprom_specific_bytes(self, offset, num_bytes):
    return None


def mock_get_sdk_handle(self):
    if not self.sdk_handle:
        self.sdk_handle = 1
    return self.sdk_handle

device_info.get_platform = mock_get_platform
SFP._read_eeprom_specific_bytes = mock_read_eeprom_specific_bytes
Chassis.get_sdk_handle = mock_get_sdk_handle



