#############################################################################
# FS
#
# Sfp contains an implementation of SONiC Platform Base API and
# provides the sfp device status which are available in the platform
#
#############################################################################

import os
import time
import sys

from ctypes import create_string_buffer

try:
    from sonic_py_common.logger import Logger
    from sonic_platform_base.sonic_xcvr.sfp_optoe_base import SfpOptoeBase
    from sonic_platform_base.sonic_sfp.sfputilhelper import SfpUtilHelper
    from .helper import APIHelper
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

CPLD_ADDR_MAPPING = {
    0: {
        "bus": 18,
        "addr": "60"
    },  # port 31-56
    1: {
        "bus": 12,
        "addr": "62"
    },  # port  1-30
}
CPLD_I2C_PATH = "/sys/bus/i2c/devices/{}-00{}/"

logger = Logger()
class Sfp(SfpOptoeBase):
    """Platform-specific Sfp class"""

    # Port number
    PORT_START = 1
    PORT_END = 58

    # Path to sysfs
    PLATFORM_ROOT_PATH = "/usr/share/sonic/device"
    PMON_HWSKU_PATH = "/usr/share/sonic/hwsku"
    HOST_CHK_CMD = "which systemctl > /dev/null 2>&1"

    PLATFORM = "x86-fs_n8550_48b8c"
    HWSKU = "fs_n8550_48b8c"

    _port_to_i2c_mapping = {
        1: [42],
        2: [41],
        3: [44],
        4: [43],
        5: [47],
        6: [45],
        7: [46],
        8: [50],
        9: [48],
        10: [49],
        11: [52],
        12: [51],
        13: [53],
        14: [56],
        15: [55],
        16: [54],
        17: [58],
        18: [57],
        19: [60],
        20: [59],
        21: [61],
        22: [63],
        23: [62],
        24: [64],
        25: [66],
        26: [68],
        27: [65],
        28: [67],
        29: [69],
        30: [71],
        31: [72],
        32: [70],
        33: [74],
        34: [73],
        35: [76],
        36: [75],
        37: [77],
        38: [79],
        39: [78],
        40: [80],
        41: [81],
        42: [82],
        43: [84],
        44: [85],
        45: [83],
        46: [87],
        47: [88],
        48: [86],
        49: [25],
        50: [26],
        51: [27],
        52: [28],
        53: [29],
        54: [30],
        55: [31],
        56: [32],
        57: [22],
        58: [23]
    }

    def __init__(self, sfp_index=0):
        SfpOptoeBase.__init__(self)
        self._api_helper = APIHelper()
        # Init index
        self.index = sfp_index
        self.port_num = self.index + 1

        cpld_idx = 0 if self.port_num > 30 else 1
        bus = CPLD_ADDR_MAPPING[cpld_idx]["bus"]
        addr = CPLD_ADDR_MAPPING[cpld_idx]["addr"]
        self.cpld_path = CPLD_I2C_PATH.format(bus, addr)

        # Init eeprom path
        eeprom_path = '/sys/bus/i2c/devices/{0}-0050/eeprom'
        self.port_to_eeprom_mapping = {}
        for x in range(self.PORT_START, self.PORT_END + 1):
            self.port_to_eeprom_mapping[x] = eeprom_path.format(
                self._port_to_i2c_mapping[x][0])

        if self.port_num <= 48  or self.port_num >=57:
            self.sfp_type = self.SFP_TYPE
        elif self.port_num <= 56:
            self.sfp_type = self.QSFP_TYPE

    def __is_host(self):
        return os.system(self.HOST_CHK_CMD) == 0

    def __get_path_to_port_config_file(self):
        platform_path = "/".join([self.PLATFORM_ROOT_PATH, self.PLATFORM])
        hwsku_path = "/".join(
            [platform_path,
             self.HWSKU]) if self.__is_host() else self.PMON_HWSKU_PATH
        return "/".join([hwsku_path, "port_config.ini"])

    def get_eeprom_path(self):
        port_eeprom_path = self.port_to_eeprom_mapping[self.port_num]
        return port_eeprom_path

    def get_reset_status(self):
        """
        Retrieves the reset status of SFP
        Returns:
            A Boolean, True if reset enabled, False if disabled
        """
        if self.sfp_type == self.SFP_TYPE:
            return False  # SPF port doesn't support this feature

        val = self._api_helper.read_txt_file(
            self.cpld_path + "module_reset_" + str(self.port_num))
        if val is not None:
            return int(val, 10) == 1
        else:
            return False

    def get_rx_los(self):
        """
        Retrieves the RX LOS (lost-of-signal) status of SFP
        Returns:
            A Boolean, True if SFP has RX LOS, False if not.
            Note : RX LOS status is latched until a call to get_rx_los or a reset.
        """
        if self.sfp_type == self.SFP_TYPE:
            cpld_val = self._api_helper.read_txt_file(
                self.cpld_path + "module_rx_los_" + str(self.port_num))
            if cpld_val is not None:
                rx_los = [(int(cpld_val, 10) == 1)]
            else:
                rx_los = [False]
            return rx_los
        else:
            api = self.get_xcvr_api()
            return api.get_rx_los() if api is not None else None

    def get_tx_fault(self):
        """
        Retrieves the TX fault status of SFP
        Returns:
            A Boolean, True if SFP has TX fault, False if not
            Note : TX fault status is lached until a call to get_tx_fault or a reset.
        """
        if self.sfp_type == self.SFP_TYPE:
            cpld_val = self._api_helper.read_txt_file(
                self.cpld_path + "module_tx_fault_" + str(self.port_num))
            if cpld_val is not None:
                tx_fault = [(int(cpld_val, 10) == 1)]
            else:
                tx_fault = [False]
            return tx_fault
        else:
            return SfpOptoeBase.get_tx_fault(self)

    def get_tx_disable(self):
        """
        Retrieves the tx_disable status of this SFP
        Returns:
            A Boolean, True if tx_disable is enabled, False if disabled
        """
        if self.sfp_type == self.SFP_TYPE:
            tx_disable = False

            cpld_val = self._api_helper.read_txt_file(
                    self.cpld_path + "module_tx_disable_" + str(self.port_num))
            if cpld_val is not None:
                tx_disable = (int(cpld_val, 10) == 1)

            return tx_disable
        else:
            api = self.get_xcvr_api()
            return api.get_tx_disable() if api is not None else None

    def get_tx_disable_channel(self):
        """
        Retrieves the TX disabled channels in this SFP
        Returns:
            A hex of 4 bits (bit 0 to bit 3 as channel 0 to channel 3) to represent
            TX channels which have been disabled in this SFP.
            As an example, a returned value of 0x5 indicates that channel 0
            and channel 2 have been disabled.
        """
        if self.sfp_type == self.SFP_TYPE:
            # SFP doesn't support this feature
            return False
        else:
            api = self.get_xcvr_api()
            return api.get_tx_disable_channel() if api is not None else None

    def get_lpmode(self):
        """
        Retrieves the lpmode (low power mode) status of this SFP
        Returns:
            A Boolean, True if lpmode is enabled, False if disabled
        """
        if self.sfp_type == self.SFP_TYPE:
            # SFP doesn't support this feature
            return False

        power_set = self.get_power_set()
        power_override = self.get_power_override()
        return power_set and power_override

    def get_power_set(self):

        if self.sfp_type == self.SFP_TYPE:
            # SFP doesn't support this feature
            return False
        else:
            api = self.get_xcvr_api()
            return api.get_power_set() if api is not None else None

    def get_power_override(self):
        """
        Retrieves the power-override status of this SFP
        Returns:
            A Boolean, True if power-override is enabled, False if disabled
        """
        if self.sfp_type == self.SFP_TYPE:
            return False  # SFP doesn't support this feature
        else:
            api = self.get_xcvr_api()
            return api.get_power_override() if api is not None else None

    def reset(self):
        """
        Reset SFP and return all user module settings to their default srate.
        Returns:
            A boolean, True if successful, False if not
        """
        # Check for invalid port_num
        if self.sfp_type == self.SFP_TYPE:
            return False  # SFP doesn't support this feature

        ret = self._api_helper.write_txt_file(
            self.cpld_path + "module_reset_" + str(self.port_num), 1)
        if ret is not True:
            return ret

        time.sleep(0.01)
        ret = self._api_helper.write_txt_file(
            self.cpld_path + "module_reset_" + str(self.port_num), 0)
        time.sleep(0.2)
        return ret

    def tx_disable(self, tx_disable):
        """
        Disable SFP TX for all channels
        Args:
            tx_disable : A Boolean, True to enable tx_disable mode, False to disable
                         tx_disable mode.
        Returns:
            A boolean, True if tx_disable is set successfully, False if not
        """
        if self.sfp_type == self.SFP_TYPE:
            ret = self._api_helper.write_txt_file(
                self.cpld_path + "module_tx_disable_" + str(self.port_num), 1
                if tx_disable else 0)
            time.sleep(0.01)
            return ret
        else:
            if not self.get_presence():
                return False
            api = self.get_xcvr_api()
            return api.tx_disable(tx_disable) if api is not None else None

    def tx_disable_channel(self, channel, disable):
        """
        Sets the tx_disable for specified SFP channels
        Args:
            channel : A hex of 4 bits (bit 0 to bit 3) which represent channel 0 to 3,
                      e.g. 0x5 for channel 0 and channel 2.
            disable : A boolean, True to disable TX channels specified in channel,
                      False to enable
        Returns:
            A boolean, True if successful, False if not
        """
        if self.sfp_type == self.SFP_TYPE:
            return False  # SFP doesn't support this feature
        else:
            if not self.get_presence():
                return False
            api = self.get_xcvr_api()
            return api.tx_disable_channel(channel, disable) if api is not None else None

    def set_lpmode(self, lpmode):
        """
        Sets the lpmode (low power mode) of SFP
        Args:
            lpmode: A Boolean, True to enable lpmode, False to disable it
            Note  : lpmode can be overridden by set_power_override
        Returns:
            A boolean, True if lpmode is set successfully, False if not
        """
        if self.sfp_type == self.SFP_TYPE:
            return False  # SFP doesn't support this feature

        if not self.get_presence():
            return False
        api = self.get_xcvr_api()
        if api is None:
            return False
        if api.get_lpmode_support() == False:
            logger.log_notice("The transceiver of port {} doesn't support to set low power mode.". format(self.port_num))
            return True
        if lpmode is True:
            '''
            use power override to control lpmode
            '''
            return api.set_power_override(True, True)
        else:
            return api.set_power_override(True, False)

    def set_power_override(self, power_override, power_set):
        """
        Sets SFP power level using power_override and power_set
        Args:
            power_override :
                    A Boolean, True to override set_lpmode and use power_set
                    to control SFP power, False to disable SFP power control
                    through power_override/power_set and use set_lpmode
                    to control SFP power.
            power_set :
                    Only valid when power_override is True.
                    A Boolean, True to set SFP to low power mode, False to set
                    SFP to high power mode.
        Returns:
            A boolean, True if power-override and power_set are set successfully,
            False if not
        """
        if self.sfp_type == self.SFP_TYPE:
            return False  # SFP doesn't support this feature
        else:
            if not self.get_presence():
                return False
            api = self.get_xcvr_api()
            return api.set_power_override(power_override, power_set) if api is not None else None

    def get_name(self):
        """
        Retrieves the name of the device
            Returns:
            string: The name of the device
        """
        sfputil_helper = SfpUtilHelper()
        sfputil_helper.read_porttab_mappings(
            self.__get_path_to_port_config_file())
        name = sfputil_helper.logical[self.index] or "Unknown"
        return name

    def get_presence(self):
        """
        Retrieves the presence of the device
        Returns:
            bool: True if device is present, False if not
        """
        val = self._api_helper.read_txt_file(
            self.cpld_path + "module_present_" + str(self.port_num))
        if val is not None:
            return val == '1'
        else:
            return False

    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        return self.get_presence() and not self.get_reset_status()

    def get_position_in_parent(self):
        """
        Retrieves 1-based relative physical position in parent device. If the agent cannot determine the parent-relative position
        for some reason, or if the associated value of entPhysicalContainedIn is '0', then the value '-1' is returned
        Returns:
            integer: The 1-based relative physical position in parent device or -1 if cannot determine the position
        """
        return self.port_num

    def is_replaceable(self):
        """
        Indicate whether this device is replaceable.
        Returns:
            bool: True if it is replaceable.
        """
        return True

