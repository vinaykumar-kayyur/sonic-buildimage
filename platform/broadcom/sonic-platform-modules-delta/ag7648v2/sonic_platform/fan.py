#!/usr/bin/env pythonsr/local/lib/python3.7/dist-packages/sonic_platform/fan.py
#
# Name: fan.py, version: 1.0
#
# Description: Module contains the definitions of SONiC platform APIs
#

try:
    import math
    import os
    import logging
    from sonic_platform_base.fan_base import FanBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

class Fan(FanBase):

    def __init__(self, fantray_index=1, index=1, is_psu_fan=False):
        self.index = index+1
        self.fantrayindex = fantray_index
        self.__is_psu_fan = is_psu_fan

        if self.__is_psu_fan:
            self.Base_bus_number = 5
            self.psu_path = "/sys/bus/i2c/devices/{}-0058/"
            self.psu_fan_rpm="fan1_input"
        else:
            self.num_of_fan = 5
            self.eeprom_base_bus_num = 21
            self.fan_eeprom  = "/sys/bus/i2c/devices/{}-0050/eeprom".format(self.fantrayindex + self.eeprom_base_bus_num)
            self.fan_path = "/sys/bus/i2c/drivers/emc2305/26-002c/"
            self.fan_rpath = "/sys/bus/i2c/drivers/emc2305/26-002d/"
            self.fan_path_eeprom = "/sys/bus/i2c/devices/{}-0050/eeprom"
            self.fan_speed = "fan{}_input"
            self.fan_percentage_speed = "fan{}_input_percentage"

    def _read_file(self,file_path, file_pattern):
        return_value = 0
        try:
            with open(os.path.join(file_path,file_pattern), 'r') as file_to_read:
                return_value = int(file_to_read.read())
        except IOError:
            print("Read file {} failed".format(fan_path + file_pattern))
            return return_value

        return return_value
##############################################
# Device methods
##############################################
    def get_name(self):
        """
        Retrieves the name of the device

        Returns:
            string: The name of the device
        """
        return "FanTray{}-Fan{}".format(self.fantrayindex+1, self.index)

    def get_presence(self):
        """
        Retrieves the presence of the device

        Returns:
            bool: True if device is present, False if not
        """
        if (not os.path.isfile(self.fan_eeprom)):
            return False
        return True

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
# FAN methods
##############################################
    def get_direction(self):
        """
        Retrieves the direction of fan

        Returns:
            A string, either FAN_DIRECTION_INTAKE or FAN_DIRECTION_EXHAUST
            depending on fan direction
        """
        return self.FAN_DIRECTION_EXHAUST

    def get_speed(self):
        """
        Retrieves the speed of fan as a percentage of full speed

        Returns:
            An integer, the percentage of full fan speed
        """
        if self.__is_psu_fan:
            speed = self._read_file(self.psu_path.format(self.index-1+self.Base_bus_number),self.psu_fan_rpm)
        else:
            if self.index == 1:
                speed = self._read_file(self.fan_path,self.fan_speed.format(self.fantrayindex+1))
            else:
                speed = self._read_file(self.fan_rpath,self.fan_speed.format(self.fantrayindex+1))

        return speed


    def get_speed_rpm(self):
        """
        Retrieves the speed of fan as a percentage of full speed

        Returns:
            An integer, the percentage of full fan speed
        """
        if self.__is_psu_fan:
            speed = self._read_file(self.psu_path.format(self.index-1+self.Base_bus_number),self.psu_fan_rpm)
        else:
            if self.index == 1:
                speed = self._read_file(self.fan_path,self.fan_speed.format(self.fantrayindex+1))
            else:
                speed = self._read_file(self.fan_rpath,self.fan_speed.format(self.fantrayindex+1))

        return speed

    def get_target_speed(self):
        """
        Retrieves the target (expected) speed of the fan

        Returns:
            An integer, the percentage of full fan speed, in the range 0 (off)
                 to 100 (full speed)
        """
        raise NotImplementedError

    def get_speed_tolerance(self):
        """
        Retrieves the speed tolerance of the fan

        Returns:
            An integer, the percentage of variance from target speed which is
                 considered tolerable
        """
        raise NotImplementedError

    def set_speed(self, speed):
        """
        Sets the fan speed

        Args:
            speed: An integer, the percentage of full fan speed to set fan to,
                   in the range 0 (off) to 100 (full speed)

        Returns:
            A boolean, True if speed is set successfully, False if not
        """
        status = True
        try:
            if self.index == 1 :
                path=self.fan_path
            else:
                path=self.fan_rpath

            with open(os.path.join(path, self.fan_percentage_speed.format(self.fantrayindex+1)), 'w') as fan_percentage:
                                fan_percentage.write(str(speed))
        except (ValueError, IOError):
            log_err("Read file {} failed".format(self.fan_path + self.fan_percentage_speed.format(self.fantrayindex+1)))
            status = False

        return status