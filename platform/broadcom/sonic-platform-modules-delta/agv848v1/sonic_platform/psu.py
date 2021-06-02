#!/usr/bin/env python
#
# Name: psu.py, version: 1.0
#
# Description: Module contains the definitions of SONiC platform APIs
#

try:
    import os
    from sonic_platform_base.psu_base import PsuBase
    from sonic_platform.fan import Fan
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

class Psu(PsuBase):

    def __init__(self, index):
        self.__num_of_fans = 1
        self.__index = index
        self.Base_bus_number = 5
        self.psu_eeprom  = "/sys/bus/i2c/devices/{}-0050/eeprom".format(self.__index + self.Base_bus_number)
        self.psu_path = "/sys/bus/i2c/devices/{}-0058/"
        self.psu_oper_status = "in1_input"
        self.psu_oper_status2 = "in2_input"
        self.psu_presence = "i2cget -y {} 0x50 0x00"
        self.psu_mfr_model = "psu_mfr_model"
        self.psu_mfr_serial = "psu_mfr_serial"
        self.psu_mfr_id = "psu_mfr_id"
        self.psu_output_vol="in2_input"
        self.psu_output_curr="curr2_input"
        self.psu_output_power="power2_input"
        self.psu_fan_rpm="fan1_input"

        # Overriding _fan_list class variable defined in PsuBase, to make it unique per Psu object
        self._fan_list = []

        # Initialize FAN
        for x in range(1, self.__num_of_fans + 1):
            fan = Fan(x, True, self.__index)
            self._fan_list.append(fan)

    def _read_file(self,file_path, file_pattern, index=0):
        return_value = 0
        try:
            with open(os.path.join(file_path.format(index+self.Base_bus_number), file_pattern), 'r') as file_to_read:
                return_value = (file_to_read.read())
        except IOError:
            log_err("Read file {} failed".format(self.fan_path + file_pattern.format(index)))
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
        return "PSU{}".format(self.__index)

    def get_presence(self):
        """
        Retrieves the presence of the device

        Returns:
            bool: True if device is present, False if not
        """
        if (not os.path.isfile(self.psu_eeprom)):
            return False
        return True

    def get_model(self):
        """
        Retrieves the model number (or part number) of the device

        Returns:
            string: Model/part number of device
        """
        model = self._read_file(self.psu_path,self.psu_mfr_model, self.__index)
        return model


    def get_serial(self):
        """
        Retrieves the serial number of the device

        Returns:
            string: Serial number of device
        """
        serial = self._read_file(self.psu_path,self.psu_mfr_serial, self.__index)
        return serial

    def get_mfr_id(self):
        return "N/A"

    def get_status(self):
        """
        Retrieves the operational status of the device

        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        status = 0
        try:
            with open(self.psu_path.format(self.__index + self.Base_bus_number) + self.psu_oper_status, 'r') as power_status:
                if int(power_status.read()) == 0 :
                    return False
                else:
                    with open(self.psu_path.format(self.__index + self.Base_bus_number) + self.psu_oper_status2, 'r') as power_status2:
                        if int(power_status2.read()) == 0 :
                            return False
                        else:
                            status = 1
        except IOError:
            return False
        return status == 1

##############################################
# PSU methods
##############################################

    def get_voltage(self):
        """
        Retrieves current PSU voltage output

        Returns:
            A float number, the output voltage in volts,
            e.g. 12.1
        """
        val = int(self._read_file(self.psu_path,self.psu_output_vol, self.__index))
        voltage =  val/1000
        return voltage

    def get_current(self):
        """
        Retrieves present electric current supplied by PSU

        Returns:
            A float number, the electric current in amperes, e.g 15.4
        """
        val = int(self._read_file(self.psu_path,self.psu_output_curr, self.__index))
        current = val/1000
        return current

    def get_power(self):
        """
        Retrieves current energy supplied by PSU

        Returns:
            A float number, the power in watts, e.g. 302.6
        """
        val = int( self._read_file(self.psu_path,self.psu_output_power, self.__index))
        power = val/1000000
        return power

    def get_powergood_status(self):
        """
        Retrieves the powergood status of PSU

        Returns:
            A boolean, True if PSU has stablized its output voltages and passed all
            its internal self-tests, False if not.
        """
        return self.get_status()

    def set_status_led(self, color):
        """
        Sets the state of the PSU status LED

        Args:
            color: A string representing the color with which to set the
                   PSU status LED

        Returns:
            bool: True if status LED state is set successfully, False if not
        """
        raise NotImplementedError

    def get_status_led(self):
        """
        Gets the state of the PSU status LED

        Returns:
            A string, one of the predefined STATUS_LED_COLOR_* strings above
        """
        if self.get_powergood_status():
            return self.STATUS_LED_COLOR_GREEN
        else:
            return self.STATUS_LED_COLOR_OFF
