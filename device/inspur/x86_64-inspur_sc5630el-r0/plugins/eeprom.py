#!/usr/bin/env python
#
# eeprom.py
#
# Platform-specific board EEPROM utility for SONiC
#

# ----------------------------------------------------------------------------
# import modules
# ----------------------------------------------------------------------------
import os.path
try:
    import binascii
    import time
    import optparse
    import warnings
    import os
    import sys
    from sonic_eeprom import eeprom_tlvinfo
    import subprocess

except ImportError as e:
    raise ImportError (str(e) + "- required module not found")

# ----------------------------------------------------------------------------
# Global variables
# ----------------------------------------------------------------------------
DEBUG_EN = False
#DEBUG_EN = True

# ----------------------------------------------------------------------------
# Debug messages
# ----------------------------------------------------------------------------
def DEG_MSG(msg):
    """
    Output debug message on the console
    """

    if DEBUG_EN == True:
        print "[DEBMSG]: %s" % msg

# ----------------------------------------------------------------------------
# Check if file path existing or not
# ----------------------------------------------------------------------------
def file_path_exist(file_path):
    if os.path.exists(file_path):
        return True
    else:
        return False

# ----------------------------------------------------------------------------
# Class declaration
# ----------------------------------------------------------------------------
class board(eeprom_tlvinfo.TlvInfoDecoder):
    _TLV_INFO_MAX_LEN = 256

    def __init__(self, name, path, cpld_root, ro):
        # Replace ipmi with i2c
        #self.eeprom_path = "/sys/bus/i2c/devices/0-006f/cpu_eeprom"
        self.eeprom_path = "/sys/bus/i2c/devices/17-0050/eeprom"
        if not os.path.exists(self.eeprom_path):
            print("Error: %s not existed" % self.eeprom_path)

        super(board, self).__init__(self.eeprom_path, 0, '', True)

