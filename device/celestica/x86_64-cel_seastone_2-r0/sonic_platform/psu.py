#!/usr/bin/env python

#############################################################################
# Celestica
#
# Module contains an implementation of SONiC Platform Base API and
# provides the psu status which are available in the platform
#
#############################################################################

import re
import json
import math
import os.path
import inspect

try:
    from sonic_platform_base.psu_base import PsuBase
    from common import Common
    from sonic_platform.fan import Fan
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class Psu(PsuBase):
    """Platform-specific Fan class"""

    PSU_CONFIG = 'psu.json'

    def __init__(self, index, conf=None):
        PsuBase.__init__(self)

        self.psu_index = index

        self._config = conf
        self._api_common = Common()
        self._initialize_fan()

        self._name = self.get_name()

    def _initialize_fan(self):
        from sonic_platform.fan import Fan

        fan_config_path = self._api_common.get_config_path(Fan.FAN_CONFIG)
        fan_config = self._api_common.load_json_file(fan_config_path)

        num_fan = fan_config['psu_fan'][self.psu_index]["num_of_fan"]
        for fan_index in range(0, num_fan):
            fan = Fan(fan_index, is_psu_fan=True, psu_index=self.psu_index, conf=fan_config)
            self._fan_list.append(fan)

    def get_voltage(self):
        """
        Retrieves current PSU voltage output

        Returns:
            A float number, the output voltage in volts, 
            e.g. 12.1 
        """
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)
        default = 0
        
        return self._api_common.get_output(self.psu_index, config, default) if self.get_presence() else default

    def get_current(self):
        """
        Retrieves present electric current supplied by PSU

        Returns:
            A float number, the electric current in amperes, e.g 15.4
        """
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)
        default = 0

        return self._api_common.get_output(self.psu_index, config, default) if self.get_presence() else default

    def get_power(self):
        """
        Retrieves current energy supplied by PSU

        Returns:
            A float number, the power in watts, e.g. 302.6
        """

        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)
        default = 0

        return self._api_common.get_output(self.psu_index, config, default) if self.get_presence() else default

    def get_powergood_status(self):
        """
        Retrieves the powergood status of PSU

        Returns:
            A boolean, True if PSU has stablized its output voltages and passed all
            its internal self-tests, False if not.
        """
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)
        default = False

        return self._api_common.get_output(self.psu_index, config, default) if self.get_presence() else default

    def set_status_led(self, color):
        """
        Sets the state of the PSU status LED
        Note:
            Seastone2 CPLD able to set only AMBER color.
            This function should be disable auto mode before execute 
            command: ipmitool raw 0x3a 0x0f 0x02 0x00
        Args:
            color: A string representing the color with which to set the
                   PSU status LED

        Returns:
            bool: True if status LED state is set successfully, False if not
        """
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)
        default = False

        return self._api_common.set_output(self.psu_index, color, config) if self.get_presence() else default

    def get_status_led(self):
        """
        Gets the state of the PSU status LED
        Note:
            Seastone2 PSU LED got only 2 mode, AMBER and Hardware control mode.
        Returns:
            A string, one of the predefined STATUS_LED_COLOR_* strings above
        """
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)
        default = "N/A"

        return self._api_common.get_output(self.psu_index, config, default) if self.get_presence() else default

    def get_temperature(self):
        """
        Retrieves current temperature reading from PSU

        Returns:
            A float number of current temperature in Celsius up to nearest thousandth
            of one degree Celsius, e.g. 30.125 
        """
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)
        default = 0
        output = self._api_common.get_output(
            self.psu_index, config, default) if self.get_presence() else default

        return float(output)

    def get_temperature_high_threshold(self):
        """
        Retrieves the high threshold temperature of PSU

        Example output
        PSUL_Temp2  | 35.000 | degrees C|ok| na | na | na | na | na | na
        The thresholds listed are, in order: lnr, lcr, lnc, unc, ucr, unr

        These are acronyms for:
        Lower Non-Recoverable
        Lower Critical
        Lower Non-Critical
        Upper Non-Critical
        Upper Critical
        Upper Non-Recoverable

        Returns:
            ucr as float number and return 0 if the BMC output is na.
            The high threshold temperature of PSU in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)
        default = 0
        output = self._api_common.get_output(
            self.psu_index, config, default) if self.get_presence() else default

        return float(output)

    def get_voltage_high_threshold(self):
        """
        Retrieves the high threshold PSU voltage output

        Returns:
            ucr as float number and return 0 if the BMC output is na.
            A float number, the high threshold output voltage in volts, 
            e.g. 12.1 
        """
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)
        default = 0
        output = self._api_common.get_output(
            self.psu_index, config, default) if self.get_presence() else default

        return float(output)

    def get_voltage_low_threshold(self):
        """
        Retrieves the low threshold PSU voltage output

        Returns:
            lcr as float number and return 0 if the BMC output is na.
            A float number, the low threshold output voltage in volts, 
            e.g. 12.1 
        """
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)
        default = 0
        output = self._api_common.get_output(
            self.psu_index, config, default) if self.get_presence() else default

        return float(output)

    def get_name(self):
        """
        Retrieves the name of the device
            Returns:
            string: The name of the device
        """
        default = Common.NULL_VAL
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)

        return self._api_common.get_output(self.psu_index, config, default)

    def get_presence(self):
        """
        Retrieves the presence of the PSU
        Returns:
            bool: True if PSU is present, False if not
        """
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)
        default = False

        return self._api_common.get_output(self.psu_index, config, default)

    def get_model(self):
        """
        Retrieves the model number (or part number) of the device
        Returns:
            string: Model/part number of device
        """
        default = Common.NULL_VAL
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)

        return self._api_common.get_output(self.psu_index, config, default) if self.get_presence() else default

    def get_serial(self):
        """
        Retrieves the serial number of the device
        Returns:
            string: Serial number of device
        """
        default = Common.NULL_VAL
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)

        return self._api_common.get_output(self.psu_index, config, default) if self.get_presence() else default

    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        return self.get_powergood_status()