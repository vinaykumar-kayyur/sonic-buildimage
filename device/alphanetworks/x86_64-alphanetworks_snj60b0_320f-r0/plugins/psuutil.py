#!/usr/bin/env python

#############################################################################
# Alphanetworks
#
# Module contains an implementation of SONiC PSU Base API and
# provides the PSUs status which are available in the platform
#
#############################################################################

import os.path

try:
    from sonic_psu.psu_base import PsuBase
    from sonic_eeprom import eeprom_base
except ImportError as e:
    raise ImportError (str(e) + "- required module not found")

class PsuUtil(PsuBase):
    """Platform-specific PSUutil class"""

    def __init__(self):
        PsuBase.__init__(self)

        self.psu_path = "/sys/bus/i2c/devices/"
        self.psu_presence = {
            1: "/psu1_present",
            2: "/psu2_present",
        }
        self.psu_oper_status = {
            1: "/psu1_power_good",
            2: "/psu2_power_good",
        }
        self.psu_model_name = "/psu_model_name"
        self.psu_mfr_id = "/psu_mfr_id"
        self.psu_serial_num = "/psu_serial_num"
        self.psu_v_out = "/psu_v_out"
        self.psu_i_out = "/psu_i_out"
        self.psu_fan1_speed_rpm = "/psu_fan1_speed_rpm"

        self._PSU_EEPROM_SERIAL_NUM_OFFSET = 0x35
        self._PSU_EEPROM_SERIAL_NUM_LENGTH = 19

        self.psu_mapping = "0-005e"
        if not os.path.exists(self.psu_path + self.psu_mapping):
            self.psu_mapping = "1-005e"

        if  os.path.exists(self.psu_path + "9-0050"):
            self.psu_eeprom_mapping = {
                1: "9-0050",
                2: "10-0051",
            }
            self.psu_pmbus_mapping = {
                1: "9-0058",
                2: "10-0059",
            }
            self.psu_serial_num = "/eeprom"
        else:
            self.psu_eeprom_mapping = {
                1: "32-0050",
                2: "33-0051",
            }
            self.psu_pmbus_mapping = {
                1: "32-0058",
                2: "33-0059",
            }
        
    def get_num_psus(self):
        return len(self.psu_presence)

    def get_psu_status(self, index):
        if index is None:
            return False

        status = 0
        node = self.psu_path + self.psu_mapping+self.psu_oper_status[index]
        try:
            with open(node, 'r') as power_status:
                status = int(power_status.read())
        except IOError:
            return False

        return status == 1

    def get_psu_presence(self, index):
        if index is None:
            return False

        status = 0
        node = self.psu_path + self.psu_mapping + self.psu_presence[index]
        try:
            with open(node, 'r') as presence_status:
                status = int(presence_status.read())
        except IOError:
            return False

        return status == 1

    def get_powergood_status(self, index):
        if index is None:
            return False

        status = 0
        node = self.psu_path + self.psu_mapping + self.psu_oper_status[index]
        try:
            with open(node, 'r') as powergood_status:
                status = int(powergood_status.read())
        except IOError:
            return False

        return status == 1

    def get_model(self, index):
        if index is None:
            return None

        model = ""
        node = self.psu_path + self.psu_pmbus_mapping[index] + self.psu_model_name
        try:
            with open(node, 'r') as model_name:
                model = model_name.read()
        except IOError:
            return None

        return model.rstrip()

    def get_mfr_id(self, index):
        if index is None:
            return None

        mfr = ""
        node = self.psu_path + self.psu_pmbus_mapping[index] + self.psu_mfr_id
        try:
            with open(node, 'r') as mfr_id:
                mfr = mfr_id.read()
        except IOError:
            return None

        return mfr.rstrip()

    def get_serial(self, index):
        if index is None:
            return None

        serial = ""
        node = self.psu_path + self.psu_eeprom_mapping[index] + self.psu_serial_num

        if self.psu_serial_num == "/eeprom":
            try:
                psu_eeprom = eeprom_base.EepromDecoder(node, None, 0, '', True)
                serial = psu_eeprom.read_eeprom_bytes(self._PSU_EEPROM_SERIAL_NUM_LENGTH, self._PSU_EEPROM_SERIAL_NUM_OFFSET)
                if len(serial) != self._PSU_EEPROM_SERIAL_NUM_LENGTH:
                    return None
            except IOError:
                return None
        else:
            try:
                with open(node, 'r') as serial_num:
                    serial = serial_num.read()
            except IOError:
                return None

        return serial.rstrip()

    def get_output_voltage(self, index):
        if index is None:
            return 0.0

        vout = 0.0
        node = self.psu_path + self.psu_pmbus_mapping[index] + self.psu_v_out
        try:
            with open(node, 'r') as v_out:
                vout = float(v_out.read())
        except IOError:
            return 0

        # vout is in milli volts
        return float(vout/1000)

    def get_output_current(self, index):
        if index is None:
            return 0.0

        iout = 0.0
        node = self.psu_path + self.psu_pmbus_mapping[index] + self.psu_i_out
        try:
            with open(node, 'r') as i_out:
                iout = float(i_out.read())
        except IOError:
            return 0.0

        # iout in milli amps
        return float(iout/1000)

    def get_fan_rpm(self, index, fan_idx):
        if index is None or fan_idx is None:
            return 0

        if fan_idx!=1: # only 1 psu_fan
            return 0
        
        rpm = 0
        node = self.psu_path + self.psu_pmbus_mapping[index] + self.psu_fan1_speed_rpm
        try:
            with open(node, 'r') as speed_rpm:
                rpm = int(speed_rpm.read())
        except IOError:
            return 0

        return rpm

    def get_direction(self, index):
        # yesm1300am not support.

        return "EXHAUST"

    def get_output_power(self, index):
        # yesm1300am not support.

        return 0.0
