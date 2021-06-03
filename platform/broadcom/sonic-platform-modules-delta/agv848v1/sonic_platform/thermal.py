#!/usr/bin/env python
#
# Name: thermal.py, version: 1.0
#
# Description: Module contains the definitions of SONiC platform APIs
#

try:
    import os
    from sonic_platform_base.thermal_base import ThermalBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

class Thermal(ThermalBase):

    def __init__(self, index):
        self.__index = index
        #thermal name list
        self.thermal_name_list =  ["System Board 1",
                                     "System Board 2",
                                     "CPU Board",
                                     "Fan control Board",
                                     "PSU1",
                                     "PSU2"]

        self.thermal_path = ["/sys/bus/i2c/drivers/lm75/4-004d/hwmon/",
                    "/sys/bus/i2c/drivers/lm75/4-004e/hwmon/",
                    "/sys/bus/i2c/drivers/lm75/4-004f/hwmon/",
                    "/sys/bus/i2c/drivers/lm75/27-004f/hwmon/",
                    "/sys/bus/i2c/devices/6-0058/",
                    "/sys/bus/i2c/devices/7-0058/"]

        self.PSU_START = 5
        self.thermal_temp = "{}/temp1_input"
        self.thermal_psutemp = "temp1_input"
        self.thermal_temp_max_hyst = "{}/temp1_max_hyst"
        self.thermal_temp_max = "{}/temp1_max"

##############################################
# Device methods
##############################################

    def get_name(self):
        """
        Retrieves the name of the device

        Returns:
            string: The name of the device
        """
        return self.thermal_name_list[self.__index] or "Unknown"

    def get_model(self):
        """
        Retrieves the model number (or part number) of the device

        Returns:
            string: Model/part number of device
        """
        return "N/A"

    def get_serial(self):
        """
        Retrieves the serial number of the device

        Returns:
            string: Serial number of device
        """
        return "N/A"

    def get_status(self):
        """
        Retrieves the operational status of the device

        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        return self.get_presence()

##############################################
# THERMAL methods
##############################################
    def get_temp_label(self):
        return

    def get_temperature(self):
        """
        Retrieves current temperature reading from thermal

        Returns:
            A float number of current temperature in Celsius up to nearest thousandth
            of one degree Celsius, e.g. 30.125
        """
        if self.__index < self.PSU_START-1:
            FileList = os.listdir(self.thermal_path[self.__index])
            temp1_path = self.thermal_temp.format(FileList[0])
        else:
            temp1_path = self.thermal_psutemp
        try:
            with open(os.path.join(self.thermal_path[self.__index], temp1_path), 'r') as file_to_read:
                 return_value = int(file_to_read.read())
        except IOError:
            return None
        return float("{:.3f}".format(return_value/1000))

    def get_high_threshold(self):
        """
        Retrieves the high threshold temperature of thermal

        Returns:
            A float number, the high threshold temperature of thermal in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        if self.__index < self.PSU_START-1:
           FileList = os.listdir(self.thermal_path[self.__index])
           temp1_path = self.thermal_temp_max_hyst.format(FileList[0])
           try:
               with open(os.path.join(self.thermal_path[self.__index], temp1_path), 'r') as file_to_read:
                    return_value = int(file_to_read.read())
           except IOError:
               return None
        else:
           return None
        return float("{:.3f}".format(return_value/1000))

    def get_low_threshold(self):
        """
        Retrieves the low threshold temperature of thermal

        Returns:
            A float number, the low threshold temperature of thermal in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        raise NotImplementedError

    def get_high_critical_threshold(self):
        """
        Retrieves the high critical threshold temperature of thermal
        Returns:
            A float number, the high critical threshold temperature of
            thermal in Celsius up to nearest thousandth of one degree
            Celsius, e.g. 30.125
        """
        if self.__index < self.PSU_START-1:
           FileList = os.listdir(self.thermal_path[self.__index])
           temp1_path = self.thermal_temp_max.format(FileList[0])
           try:
               with open(os.path.join(self.thermal_path[self.__index], temp1_path), 'r') as file_to_read:
                    return_value = int(file_to_read.read())
           except IOError:
               return None
        else:
           return None
        return float("{:.3f}".format(return_value/1000))

    def set_high_threshold(self, temperature):
        """
        Sets the high threshold temperature of thermal

        Args :
            temperature: A float number up to nearest thousandth of one degree Celsius,
            e.g. 30.125

        Returns:
            A boolean, True if threshold is set successfully, False if not
        """
        # Thermal threshold values are pre-defined based on HW.
        return False

    def set_low_threshold(self, temperature):
        """
        Sets the low threshold temperature of thermal

        Args :
            temperature: A float number up to nearest thousandth of one degree Celsius,
            e.g. 30.125

        Returns:
            A boolean, True if threshold is set successfully, False if not
        """
        # Thermal threshold values are pre-defined based on HW.
        return False
