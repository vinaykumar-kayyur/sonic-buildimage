#!/usr/bin/env python
 
#############################################################################
# Inventec d7264
#
# Module contains an implementation of SONiC Platform Base API and
# provides the PSU information
#
# version: 1.0
#############################################################################

try:
    import os
    from sonic_platform_base.psu_base import PsuBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


###############
# Global
###############
HWMON_PATH = "/sys/class/hwmon/hwmon2/"

class Psu(PsuBase):
    """Inventec Platform-specific PSU class"""

    def __init__(self, psu_index):
        self.index                  = psu_index + 1
        self.psu_presence_attr      = "psu{}".format(self.index - 1)
        self.psu_power_in_attr      = "psoc_psu{}_pin".format(self.index)
        self.psu_power_out_attr     = "psoc_psu{}_pout".format(self.index)
        self.psu_voltage_in_attr    = "psoc_psu{}_vin".format(self.index)
        self.psu_voltage_out_attr   = "psoc_psu{}_vout".format(self.index)
        self.psu_current_in_attr    = "psoc_psu{}_iin".format(self.index)        
        self.psu_current_out_attr   = "psoc_psu{}_iout".format(self.index)
        self.psu_serial_attr        = "psoc_psu{}_serial".format(self.index)
        self.psu_model_attr         = "psoc_psu{}_version".format(self.index)


    #######################
    # private function
    #######################

    def __get_attr_value(self, attr_path):

        retval = 'ERR'
        if (not os.path.isfile(attr_path)):
            return retval

        try:
            with open(attr_path, 'r') as fd:
                retval = fd.read()
        except Exception as error:
            logging.error("Unable to open ", attr_path, " file !")

        retval = retval.rstrip(' \t\n\r')
        return retval


    ####################
    # Device base
    ####################

    def get_name(self):
        """
        Retrieves the name of the device

        Returns:
            string: The name of the device
        """
        return "PSU-{}".format(self.index)

    def get_presence(self):
        """
        Retrieves the presence of the device

        Returns:
            bool: True if device is present, False if not

        Note:
            CPLD report the PSU{} status in psoc driver
            000 = PSU normal operation  string = "0 : normal"
            100 = PSU fault             string = "4 : fault"
            010 = PSU unpowered         string = "2 : unpowered"
            111 = PSU not installed     string = "7 : not installed"
        """
        presence = False
        attr_not_installed = "0 : not installed"
        attr_path = HWMON_PATH + self.psu_presence_attr

        attr_rv = self.__get_attr_value(attr_path)
        if (attr_rv != 'ERR'):
            if (attr_rv != attr_not_installed):
                presence = True

        return presence

    def get_model(self):
        """
        Retrieves the model number (or part number) of the device

        Returns:
            string: Model/part number of device
        """
        model_str = ""
        attr_path = HWMON_PATH + self.psu_model_attr

        attr_rv = self.__get_attr_value(attr_path)
        if (attr_rv != 'ERR'):
            model_str = attr_rv

        return model_str

    def get_serial(self):
        """
        Retrieves the serial number of the device

        Returns:
            string: Serial number of device
        """
        serial_no = ""
        attr_path = HWMON_PATH + self.psu_serial_attr

        attr_rv = self.__get_attr_value(attr_path)
        if (attr_rv != 'ERR'):
            serial_no = attr_rv

        return serial_no

    def get_status(self):
        """
        Retrieves the operational status of the device

        Returns:
            A boolean value, True if device is operating properly, False if not
        Note:
            CPLD report the PSU{} status in psoc driver
            000 = PSU normal operation  string = "0 : normal"
            100 = PSU fault             string = "4 : fault"
            010 = PSU unpowered         string = "2 : unpowered"
            111 = PSU not installed     string = "7 : not installed"
        """
        status = False
        attr_not_installed = "0 : normal"
        attr_path = HWMON_PATH + self.psu_presence_attr

        attr_rv = self.__get_attr_value(attr_path)
        if (attr_rv != 'ERR'):
            if (attr_rv == attr_not_installed):
                status = True

        return status


    #################
    # psu base
    #################

    def get_voltage(self):
        """
        Retrieves current PSU voltage output

        Returns:
            A float number, the output voltage in volts,
            e.g. 12.1
        """
        voltage_out = 0.0
        attr_path = HWMON_PATH + self.psu_voltage_out_attr

        attr_rv = self.__get_attr_value(attr_path)
        if (attr_rv != 'ERR'):
            voltage_out = float(attr_rv) / 1000

        return voltage_out

    def get_current(self):
        """
        Retrieves present electric current supplied by PSU

        Returns:
            A float number, the electric current in amperes, e.g 15.4
        """
        current_in = 0.0
        attr_path = HWMON_PATH + self.psu_current_out_attr

        attr_rv = self.__get_attr_value(attr_path)
        if (attr_rv != 'ERR'):
            current_in = float(attr_rv) / 1000

        return current_in

    def get_power(self):
        """
        Retrieves current energy supplied by PSU

        Returns:
            A float number, the power in watts, e.g. 302.6
        """
        power_out = 0.0
        attr_path = HWMON_PATH + self.psu_power_out_attr

        attr_rv = self.__get_attr_value(attr_path)
        if (attr_rv != 'ERR'):
            power_out = float(attr_rv) / 1000

        return power_out

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
        raise NotImplementedError
