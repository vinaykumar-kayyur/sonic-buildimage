#!/usr/bin/env python

#############################################################################
#
# Module contains an implementation of SONiC Platform Base API and
# provides the thermal status which are available in the platform
#
#############################################################################

import glob
import os.path

try:
    from sonic_platform_base.thermal_base import ThermalBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

class Alpha_Thermal(ThermalBase):
    """Platform-specific Thermal class"""

    temp_node_map = {
        1: "/sys/bus/i2c/devices/0-004f/hwmon/",
        2: "/sys/bus/i2c/devices/3-004d/hwmon/",
        3: "/sys/bus/i2c/devices/4-004c/hwmon/"
    }

    temp_name_map = {
        1: "lm75-i2c-0-004f",
        2: "lm75-i2c-3-004d",
        3: "lm75-i2c-4-004c"
    }

    _high_crital_threshold = 75
    _high_threshold = 60
    _low_threshold = 50

    def __init__(self, temp_index):
        self.index = temp_index + 1

        if os.path.exists("/sys/bus/i2c/devices/3-004d/hwmon/") == False:
            self.temp_node_map = {
                1: "/sys/bus/i2c/devices/0-004f/hwmon/",
                2: "/sys/bus/i2c/devices/18-004d/hwmon/",
                3: "/sys/bus/i2c/devices/19-004c/hwmon/"
            }

            self.temp_name_map = {
                1: "lm75-i2c-0-004f",
                2: "lm75-i2c-18-004d",
                3: "lm75-i2c-19-004c"
            }

        ThermalBase.__init__(self)

    def get_name(self):
        """
        Retrieves the name of the device

        Returns:
            string: The name of the device
        """
        return self.temp_name_map[self.index]

    def get_status(self):
        """
        Retrieves the operational status of the device

        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        if self.get_temperature() == -255:
            return False
        return True

    def get_presence(self):
        """
        Retrieves the presence of the device

        Returns:
            bool: True if device is present, False if not
        """
        node = glob.glob(self.temp_node_map[self.index] + "hwmon*")
        if len(node) == 0:
            return False
        node = node[0] + "/temp1_input"
        if os.path.exists(node):
            return True
        return False

    def get_temperature(self):
        """
        Retrieves current temperature reading from thermal

        Returns:
            A float number of current temperature in Celsius up to nearest thousandth
            of one degree Celsius, e.g. 30.125 
        """
        temp = 0
        node = glob.glob(self.temp_node_map[self.index] + "hwmon*")
        if len(node) == 0:
            return -255
        node = node[0] + "/temp1_input"
        try:
            with open(node, 'r') as fp:
                temp = float(fp.read()) / 1000
        except IOError:
            temp = -255
        return temp

    def get_high_threshold(self):
        """
        Retrieves the high threshold temperature of thermal

        Returns:
            A float number, the high threshold temperature of thermal in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        return self._high_threshold

    def get_low_threshold(self):
        """
        Retrieves the low threshold temperature of thermal

        Returns:
            A float number, the low threshold temperature of thermal in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        return self._low_threshold

    def set_high_threshold(self, temperature):
        """
        Sets the high threshold temperature of thermal

        Args : 
            temperature: A float number up to nearest thousandth of one degree Celsius, 
            e.g. 30.125

        Returns:
            A boolean, True if threshold is set successfully, False if not
        """
        self._high_threshold = temperature
        return True

    def set_low_threshold(self, temperature):
        """
        Sets the low threshold temperature of thermal

        Args : 
            temperature: A float number up to nearest thousandth of one degree Celsius,
            e.g. 30.125

        Returns:
            A boolean, True if threshold is set successfully, False if not
        """
        self._low_threshold = temperature
        return True

    def get_high_critical_threshold(self):
        """
        Retrieves the high critical threshold temperature of thermal

        Returns:
            A float number, the high critical threshold temperature of thermal in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        return self._high_crital_threshold
    
    def get_low_critical_threshold(self):
        """
        Retrieves the low critical threshold temperature of thermal

        Returns:
            A float number, the low critical threshold temperature of thermal in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        return 0