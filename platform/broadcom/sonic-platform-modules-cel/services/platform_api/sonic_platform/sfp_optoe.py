#!/usr/bin/env python

#############################################################################
# Celestica
#
# Module contains an implementation of SONiC Platform Base API and
# provides the sfp status which are available in the platform
#
#############################################################################

import os
import syslog
import time

try:
    from sonic_platform_base.sonic_xcvr.sfp_optoe_base import SfpOptoeBase
    #from sonic_platform_base.sfp_base import SfpBase
    from sonic_platform_base.sonic_sfp.sfputilhelper import SfpUtilHelper
    from sonic_platform.common import Common
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

QSFP_INFO_OFFSET = 128


class SfpOptoe(SfpOptoeBase):
    """Platform-specific SfpOptoe class"""

    def __init__(self, sfp_index=0, conf=None):
        SfpOptoeBase.__init__(self)

        self._sfp_index = sfp_index
        self._config = conf
        self._sfp_type = None
        self._api_common = Common(self._config)
        self._read_porttab_mappings()

    @property
    def sfp_type(self):
        if self._sfp_type is None:
            self._sfp_type = self._detect_sfp_type()
        return self._sfp_type

    def _detect_sfp_type(self):
        sfp_type = 'N/A'
        info = self.get_transceiver_info()
        if info:
            sfp_type = info.get("type_abbrv_name")
        # XXX: Need this hack until xcvrd is refactored
        if sfp_type in ["OSFP-8X", "QSFP-DD"]:
            sfp_type = "QSFP_DD"
        return sfp_type

    def _read_porttab_mappings(self):
        self._sfputil_helper = SfpUtilHelper()
        self._sfputil_helper.read_porttab_mappings(
            self._get_path_to_port_config_file())

    def _get_path_to_port_config_file(self):
        host_platform_root_path = '/usr/share/sonic/device'
        docker_hwsku_path = '/usr/share/sonic/hwsku'

        host_platform_path = "/".join([host_platform_root_path,
                                       self._api_common.platform])
        hwsku_path = "/".join([host_platform_path, self._api_common.hwsku]
                              ) if self._api_common.is_host() else docker_hwsku_path

        return "/".join([hwsku_path, "port_config.ini"])

    def get_eeprom_path(self):
        eeprom_path = self._config['eeprom_path']
        port_to_i2c_mapping = self._config['port_i2c_mapping']
        port_eeprom_path = eeprom_path.format(
            port_to_i2c_mapping[self._sfp_index])

        return port_eeprom_path

    def get_name(self):
        """
        Retrieves the human-readable name of a sfp by 1-based index

        Returns:
        :param index: An integer, 1-based index of the sfp of which to query status
        :return: String,
            A string representing the name of the sfp.
        """
        return self._sfputil_helper.physical_to_logical[self._sfp_index + 1] or "Unknown"

    def get_presence(self):
        """
        Retrieves the presence of the device
        Returns:
            bool: True if device is present, False if not
        """
        return self._api_common.get_output(self._sfp_index, self._config['get_presence'], False)

    def get_position_in_parent(self):
        return self._sfp_index

    def is_replaceable(self):
        return True

    def get_status(self):
        """
        Retrieves the operational status of the device

        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        if not self.get_presence():
            return False
        reset = self.get_reset_status()
        if reset:
            status = False
        else:
            status = True
        return status

    def get_reset_status(self):
        """
        Retrieves the reset status of SFP
        Returns:
            A Boolean, True if reset enabled, False if disabled
        """
        return self._api_common.get_output(self._sfp_index, self._config['get_reset_status'], False)

    def get_lpmode(self):
        """
        Retrieves the lpmode (low power mode) status of this SFP
        Returns:
            A Boolean, True if lpmode is enabled, False if disabled
        """
        return self._api_common.get_output(self._sfp_index, self._config['get_lpmode'], False)

    def reset(self):
        """
        Reset SFP and return all user module settings to their default srate.

        Returns:
            A boolean, True if successful, False if not
        """
        config = self._config['reset']
        # Convert our register value back to a hex string and write back
        output1 = self._api_common.set_output(self._sfp_index, "0x0", config)

        # Sleep 1 second to allow it to settle
        time.sleep(1)
        # Flip the bit back high and write back to the register to take port out of reset
        output2 = self._api_common.set_output(self._sfp_index, "0x1", config)

        return True if (output1 and output2) else False

    def set_lpmode(self, lpmode):
        """
        Sets the lpmode (low power mode) of SFP

        Args:
            lpmode: A Boolean, True to enable lpmode, False to disable it
            Note  : lpmode can be overridden by set_power_override

        Returns:
            A boolean, True if lpmode is set successfully, False if not
        """
        return self._api_common.set_output(self._sfp_index, str(lpmode), self._config['set_lpmode'])

    def get_error_description(self):
        """
        Retrives the error descriptions of the SFP module

        Returns:
            String that represents the current error descriptions of vendor specific errors
            In case there are multiple errors, they should be joined by '|',
            like: "Bad EEPROM|Unsupported cable"
        """
        if not self.get_presence():
            return self.SFP_STATUS_UNPLUGGED
        return self.SFP_STATUS_OK
