#!/usr/bin/env python

import os.path
import sys, traceback
sys.path.append('/usr/share/sonic/platform/plugins')
import pddfparse
import json

try:
    import time
    from ctypes import create_string_buffer
    from sonic_sfp.sfputilbase import SfpUtilBase
except ImportError, e:
    raise ImportError (str(e) + "- required module not found")

class SfpUtil(SfpUtilBase):
    """Platform generic PDDF SfpUtil class"""

    _port_to_eeprom_mapping = {}
    _port_start = 0
    _port_end = 0
    _port_to_type_mapping = {}
    _qsfp_ports = []
    _sfp_ports = []

    def __init__(self):
        SfpUtilBase.__init__(self)
        global pddf_obj
        global plugin_data
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)) + '/../pddf/pd-plugin.json')) as pd:
            plugin_data = json.load(pd)

        pddf_obj = pddfparse.PddfParse()
        self.platform = pddf_obj.get_platform()
        self._port_start = 0
        self._port_end = self.get_num_ports()

        for port_num in range(self._port_start, self._port_end):
            device = "PORT" + "%d"%(port_num+1)
            port_eeprom_path = pddf_obj.get_path(device,"eeprom")
            self._port_to_eeprom_mapping[port_num] = port_eeprom_path
            port_type = pddf_obj.get_device_type(device)
            self._port_to_type_mapping[port_num] = port_type
            ret = self.populate_port_type(port_num)

    def get_num_ports(self):
        return int(self.platform['num_ports'])

    def is_valid_port(self, port_num):
        if port_num < self._port_start or port_num > self._port_end:
            return False
        else:
            return True

    def get_presence(self, port_num):
        if port_num < self._port_start or port_num > self._port_end:
            return False

        status = 0
        device = "PORT" + "%d"%(port_num+1)
        port_ps = pddf_obj.get_path(device,"xcvr_present")
        #print "port_ps value is : %s"%port_ps
        try:
            reg_file = open(port_ps, 'r')
        except IOError as e:
            print "Error: unable to open file: %s" % str(e)
            return False

        reg_value = reg_file.readline().rstrip()
        #print "%s: Presence Status %d"%(device, int(reg_value))
        if reg_value == '1':
            return True

        return False

    def populate_port_type(self, port):
        if self._port_to_type_mapping[port] == 'QSFP':
            self._qsfp_ports.append(port)
        elif self._port_to_type_mapping[port] == 'SFP':
            self._sfp_ports.append(port)

    @property
    def port_start(self):
        return self._port_start

    @property
    def port_end(self):
        return (self._port_end - 1)

    @property
    def port_to_eeprom_mapping(self):
        return self._port_to_eeprom_mapping

    @property
    def qsfp_ports(self):
        return self._qsfp_ports

    def reset(self, port_num):
        if port_num < self._port_start or port_num > self._port_end:
            return False

        device = "PORT" + "%d"%(port_num+1)
        port_ps = pddf_obj.get_path(device,"xcvr_reset")
        #print "port_ps value is : %s"%port_ps
        try:
            reg_file = open(port_ps, 'w')
        except IOError as e:
            print "Error: unable to open file: %s" % str(e)
            return False

        #toggle reset
        reg_file.seek(0)
        reg_file.write('1')
        time.sleep(1)
        reg_file.seek(0)
        reg_file.write('0')
        reg_file.close()
        return True
        #raise NotImplementedError

    def get_low_power_mode(self, port_num):
        # Check for invalid port_num
        if port_num < self._port_start or port_num > self._port_end:
            return False

        device = "PORT" + "%d"%(port_num+1)
        port_ps = pddf_obj.get_path(device,"xcvr_lpmode")
        #print "port_ps value is : %s"%port_ps
        try:
            reg_file = open(port_ps, 'w')
        except IOError as e:
            if not self.get_presence(port_num):
                return False
            if port_num not in self.qsfp_ports:
                return False # Read from eeprom only for QSFP ports
            try:
                eeprom = None
                eeprom = open(self.port_to_eeprom_mapping[port_num], "rb")
                eeprom.seek(93)
                lpmode = ord(eeprom.read(1))
                
                if ((lpmode & 0x3) == 0x3):
                    return True # Low Power Mode if "Power override" bit is 1 and "Power set" bit is 1
                else:
                    return False # High Power Mode if one of the following conditions is matched:
                                 # 1. "Power override" bit is 0
                                 # 2. "Power override" bit is 1 and "Power set" bit is 0
            except IOError as e:
                print "Error: unable to open file: %s" % str(e)
                return False
            finally:
                if eeprom is not None:
                    eeprom.close()
                    time.sleep(0.01)
        #raise NotImplementedError

    def set_low_power_mode(self, port_num, lpmode):
        # Check for invalid port_num
        if port_num < self._port_start or port_num > self._port_end:
            return False

        device = "PORT" + "%d"%(port_num+1)
        port_ps = pddf_obj.get_path(device,"xcvr_lpmode")
        try:
            reg_file = open(port_ps, 'w')
        except IOError as e:
            if not self.get_presence(port_num):
                return False # Port is not present, unable to set the eeprom
            if port_num not in self.qsfp_ports:
                return False # Read from eeprom only for QSFP ports
            try:
                eeprom = None
                # Fill in write buffer
                regval = 0x3 if lpmode else 0x1 # 0x3:Low Power Mode, 0x1:High Power Mode
                buffer = create_string_buffer(1)
                buffer[0] = chr(regval)
                
                # Write to eeprom
                eeprom = open(self.port_to_eeprom_mapping[port_num], "r+b")
                eeprom.seek(93)
                eeprom.write(buffer[0])
                return True
            except IOError as e:
                print "Error: unable to open file: %s" % str(e)
                return False
            finally:
                if eeprom is not None:
                    eeprom.close()
                    time.sleep(0.01)
        #raise NotImplementedError

    def get_transceiver_change_event(self):
        """
        TODO: This function need to be implemented
        when decide to support monitoring SFP(Xcvrd)
        on this platform.
        """
        raise NotImplementedError


    def dump_sysfs(self):
        return pddf_obj.cli_dump_dsysfs('xcvr')
