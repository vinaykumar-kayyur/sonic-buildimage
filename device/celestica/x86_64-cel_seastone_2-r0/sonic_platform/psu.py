#!/usr/bin/env python

#############################################################################
# Celestica
#
# Module contains an implementation of SONiC Platform Base API and
# provides the fan status which are available in the platform
#
#############################################################################

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

    def __init__(self, index, psu_index=0, conf=None):
        PsuBase.__init__(self)

        self.psu_index = index

        self._config = conf
        self._api_common = Common()
        self._name = self.get_name()
        self._fan_list = self.get_all_fans()

    def get_num_fans(self):
        """
        Retrieves the number of fan modules available on this PSU

        Returns:
            An integer, the number of fan modules available on this PSU
        """
        default = Common.NULL_VAL
        config = self._config.get("get_name")

        psu_attr = self._api_common.get_val(self.psu_index, config, default)
        
        __fan_list = psu_attr['fan_name']

        return len(__fan_list) if self.get_presence() else default

    def get_all_fans(self):
        """
        Retrieves all fan modules available on this PSU

        Returns:
            A list of objects derived from FanBase representing all fan
            modules available on this PSU
        """
        default = Common.NULL_VAL
        config = self._config.get("get_name")

        psu_attr = self._api_common.get_val(self.psu_index, config, default)
        
        __fan_list = psu_attr['fan_name']

        return __fan_list if self.get_presence() else default

    def get_fan(self, index):
        """
        Retrieves fan module represented by (0-based) index <index>

        Args:
            index: An integer, the index (0-based) of the fan module to
            retrieve

        Returns:
            An object dervied from FanBase representing the specified fan
            module
        """
        fan = None

        try:
            fan = self._fan_list[index]
        except IndexError:
            sys.stderr.write("Fan index {} out of range (0-{})\n".format(
                             index, len(self._fan_list)-1))

        return fan

    def get_voltage(self):
        """
        Retrieves current PSU voltage output

        Returns:
            A float number, the output voltage in volts, 
            e.g. 12.1 
        """
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)
        ret_val = 0

        if self.get_presence() and config.get('oper_type') == Common.OPER_IMPI:
            status, result = self._api_common.ipmi_get(self.psu_index, config)
            raw_val = result if status else ret_val

        return float(raw_val)

    def get_current(self):
        """
        Retrieves present electric current supplied by PSU

        Returns:
            A float number, the electric current in amperes, e.g 15.4
        """
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)
        ret_val = 0

        if self.get_presence() and config.get('oper_type') == Common.OPER_IMPI:
            status, result = self._api_common.ipmi_get(self.psu_index, config)
            raw_val = result if status else ret_val

        return float(raw_val)

    def get_power(self):
        """
        Retrieves current energy supplied by PSU

        Returns:
            A float number, the power in watts, e.g. 302.6
        """
        
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)
        ret_val = 0

        if self.get_presence() and config.get('oper_type') == Common.OPER_IMPI:
            status, result = self._api_common.ipmi_get(self.psu_index, config)
            raw_val = result if status else ret_val

        return float(raw_val)

    def get_powergood_status(self):
        """
        Retrieves the powergood status of PSU

        Returns:
            A boolean, True if PSU has stablized its output voltages and passed all
            its internal self-tests, False if not.
        """
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)
        ret_val = False

        if config.get('oper_type') == Common.OPER_IMPI:
            status, result = self._api_common.ipmi_get(self.psu_index, config)
            ret_val = result if status else ret_val

        return ret_val 

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
        avaliable_input = config.get('avaliable_input')
        if avaliable_input and color not in avaliable_input:
            return False

        return self._api_common.set_val(self.psu_index, color, config) if self.get_presence() else default

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
        ret_val = "off" 

        if self.get_presence() and config.get('oper_type') == Common.OPER_IMPI:
            status, led_color = self._api_common.ipmi_get(self.psu_index, config)

        return led_color if status else ret_val

    def get_temperature(self):
        """
        Retrieves current temperature reading from PSU

        Returns:
            A float number of current temperature in Celsius up to nearest thousandth
            of one degree Celsius, e.g. 30.125 
        """
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)
        ret_val = 0

        if self.get_presence() and config.get('oper_type') == Common.OPER_IMPI:
            status, result = self._api_common.ipmi_get(self.psu_index, config)
            raw_val = result if status else ret_val

        return float(raw_val)

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
        ret_val = 0

        if self.get_presence() and config.get('oper_type') == Common.OPER_IMPI:
            status, result = self._api_common.ipmi_get(self.psu_index, config)
            raw_val = result if status else ret_val

        return float(raw_val)

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
        ret_val = 0

        if self.get_presence() and config.get('oper_type') == Common.OPER_IMPI:
            status, result = self._api_common.ipmi_get(self.psu_index, config)
            raw_val = result if status else ret_val

        return float(raw_val)

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
        ret_val = 0

        if self.get_presence() and config.get('oper_type') == Common.OPER_IMPI:
            status, result = self._api_common.ipmi_get(self.psu_index, config)
            raw_val = result if status else ret_val

        return float(raw_val)

    def get_name(self):
        """
        Retrieves the name of the device
            Returns:
            string: The name of the device
        """
        default = Common.NULL_VAL
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)

        psu_attr = self._api_common.get_val(self.psu_index, config, default)
        
        psu_name = psu_attr['psu_name']

        return psu_name if self.get_presence() else default

    def get_presence(self):
        """
        Retrieves the presence of the PSU
        Returns:
            bool: True if PSU is present, False if not
        """
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)
        ret_val = False

        if config.get('oper_type') == Common.OPER_IMPI:
            status, result = self._api_common.ipmi_get(self.psu_index, config)
            ret_val = result if status else ret_val

        return ret_val