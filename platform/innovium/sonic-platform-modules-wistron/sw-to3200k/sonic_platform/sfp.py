#!/usr/bin/env python

#############################################################################
# Sfp contains an implementation of SONiC Platform Base API and
# provides the sfp device status which are available in the platform
#############################################################################
try:
    from sonic_platform_base.sonic_xcvr.sfp_optoe_base import SfpOptoeBase
    from sonic_py_common.logger import Logger
    import sys
    import time
except ImportError as err:
    raise ImportError(str(err) + "- required module not found")


QSFP_TYPE_CODE_LIST = [
    '0x0d', # QSFP+ or later
    '0x11'  # QSFP28 or later
]

QSFP_DD_TYPE_CODE_LIST = [
    '0x18' # QSFP-DD Double Density 8X Pluggable Transceiver
]


QSFP_TYPE = "QSFP"
QSFP_DD_TYPE = "QSFP_DD"

# Global logger class instance
logger = Logger()


class Sfp(SfpOptoeBase):
    """Platform-specific Sfp class"""

    # Port number
    PORT_START = 0
    PORT_END = 31

    port_to_i2c_mapping = {
        0: 10,
        1: 11,
        2: 12,
        3: 13,
        4: 14,
        5: 15,
        6: 16,
        7: 17,
        8: 18,
        9: 19,
        10: 20,
        11: 21,
        12: 22,
        13: 23,
        14: 24,
        15: 25,
        16: 26,
        17: 27,
        18: 28,
        19: 29,
        20: 30,
        21: 31,
        22: 32,
        23: 33,
        24: 34,
        25: 35,
        26: 36,
        27: 37,
        28: 38,
        29: 39,
        30: 40,
        31: 41,
    }

    _sfp_port = range(32, PORT_END + 1)
    RESET_1_16_PATH = "/sys/bus/i2c/devices/0-0061/module_reset_{}"
    RESET_17_32_PATH = "/sys/bus/i2c/devices/0-0062/module_reset_{}"
    PRS_1_16_PATH = "/sys/bus/i2c/devices/0-0061/module_present_{}"
    PRS_17_32_PATH = "/sys/bus/i2c/devices/0-0062/module_present_{}"

    def __init__(self, sfp_index, sfp_type):
        # Init index
        SfpOptoeBase.__init__(self)
        self.index = sfp_index
        self.sfp_type = sfp_type
        self.port_num = self.index + 1

        # Init eeprom path
        eeprom_low_path = '/sys/bus/i2c/devices/0-00{}/eeprom_low'
        eeprom_0_path = '/sys/bus/i2c/devices/0-00{}/eeprom_pg0'
        eeprom_1_path = '/sys/bus/i2c/devices/0-00{}/eeprom_pg1'
        eeprom_2_path = '/sys/bus/i2c/devices/0-00{}/eeprom_pg2'
        eeprom_3_path = '/sys/bus/i2c/devices/0-00{}/eeprom_pg3'
        eeprom_4_path = '/sys/bus/i2c/devices/0-00{}/eeprom_pg4'
        eeprom_11_path = '/sys/bus/i2c/devices/0-00{}/eeprom_pg11'
        name_path = '/sys/bus/i2c/devices/0-00{}/port_name'
        power_mode_path = '/sys/bus/i2c/devices/0-00{}/power_mode'
        grid_path = '/sys/bus/i2c/devices/0-00{}/grid'
        freq_path = '/sys/bus/i2c/devices/0-00{}/freq'
        outp_path = '/sys/bus/i2c/devices/0-00{}/output_power'
        self.port_to_eeprom_low_mapping = {}
        self.port_to_eeprom_0_mapping = {}
        self.port_to_eeprom_1_mapping = {}
        self.port_to_eeprom_2_mapping = {}
        self.port_to_eeprom_3_mapping = {}
        self.port_to_eeprom_4_mapping = {}
        self.port_to_eeprom_11_mapping = {}
        self.port_to_name_mapping = {}
        self.port_to_power_mode_mapping = {}
        self.port_to_grid_mapping = {}
        self.port_to_freq_mapping = {}
        self.port_to_outp_mapping = {}
        for x in range(self.PORT_START, self.PORT_END + 1):
            p_num = x - 1 if self.PORT_START == 1 else x
            self.port_to_eeprom_low_mapping[p_num] = eeprom_low_path.format(self.port_to_i2c_mapping[p_num])
            self.port_to_eeprom_0_mapping[p_num] = eeprom_0_path.format(self.port_to_i2c_mapping[p_num])
            self.port_to_eeprom_1_mapping[p_num] = eeprom_1_path.format(self.port_to_i2c_mapping[p_num])
            self.port_to_eeprom_2_mapping[p_num] = eeprom_2_path.format(self.port_to_i2c_mapping[p_num])
            self.port_to_eeprom_3_mapping[p_num] = eeprom_3_path.format(self.port_to_i2c_mapping[p_num])
            self.port_to_eeprom_4_mapping[p_num] = eeprom_4_path.format(self.port_to_i2c_mapping[p_num])
            self.port_to_eeprom_11_mapping[p_num] = eeprom_11_path.format(self.port_to_i2c_mapping[p_num])
            self.port_to_name_mapping[p_num] = name_path.format(self.port_to_i2c_mapping[p_num])
            self.port_to_power_mode_mapping[p_num] = power_mode_path.format(self.port_to_i2c_mapping[p_num])
            self.port_to_grid_mapping[p_num] = grid_path.format(self.port_to_i2c_mapping[p_num])
            self.port_to_freq_mapping[p_num] = freq_path.format(self.port_to_i2c_mapping[p_num])
            self.port_to_outp_mapping[p_num] = outp_path.format(self.port_to_i2c_mapping[p_num])

        self.reinit()

    def reinit(self):
        self._detect_sfp_type(self.sfp_type)

    def _detect_sfp_type(self, sfp_type):
        eeprom_raw = []
        eeprom_raw = self._xcvr_api_factory._get_id()
        if eeprom_raw is not None:
            eeprom_raw = hex(eeprom_raw)
            if eeprom_raw in QSFP_TYPE_CODE_LIST:
                self.sfp_type = QSFP_TYPE
            elif eeprom_raw in QSFP_DD_TYPE_CODE_LIST:
                self.sfp_type = QSFP_DD_TYPE
            else:
                # we don't regonize this identifier value, treat the xSFP module as the default type
                self.sfp_type = sfp_type
        else:
            # eeprom_raw being None indicates the module is not present.
            # in this case we treat it as the default type according to the SKU
            self.sfp_type = sfp_type

    def get_presence(self):
        """
        Retrieves the presence of the SFP
        Returns:
            bool: True if SFP is present, False if not
        """
        presence = False
        try:
            if self.index < 16:
                pres_path = self.PRS_1_16_PATH.format(self.port_num)
            else:
                pres_path = self.PRS_17_32_PATH.format(self.port_num)
            with open(pres_path, 'r') as sfp_presence:
                presence = int(sfp_presence.read(), 16)
        except IOError:
            return False
        logger.log_info("debug:port_ %s sfp presence is %s" % (str(self.index), str(presence)))
        return presence == True

    def get_reset_status(self):
        """
        Retrieves the reset status of SFP
        Returns:
            A Boolean, True if reset enabled, False if disabled
        """
        # SFP doesn't support this feature
        return False

    def reset(self):
        """
        Reset SFP and return all user module settings to their default srate.
        Returns:
            A boolean, True if successful, False if not
        """
        # SFP doesn't support this feature
        return False

    def get_lpmode(self):
        """
        Retrieves the lpmode (low power mode) status of this SFP
        Returns:
            A Boolean, True if lpmode is enabled, False if disabled
        """
        # SFP doesn't support this feature
        return False

    def set_lpmode(self, lpmode):
        """
        Sets the lpmode (low power mode) of SFP
        Args:
            lpmode: A Boolean, True to enable lpmode, False to disable it
            Note  : lpmode can be overridden by set_power_override
        Returns:
            A boolean, True if lpmode is set successfully, False if not
        """
        if not self.get_presence():
            return False
        self.set_power_override(True, True if lpmode is True else False)
        return True

    def get_power_override(self):
        """
        Retrieves the power-override status of this SFP
        Returns:
            A Boolean, True if power-override is enabled, False if disabled
        """
        # SFP doesn't support this feature
        return False

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
        if not self.get_presence():
            return False
        if self.sfp_type == QSFP_TYPE:
            try:
                power_override_bit = (1 << 0) if power_override else 0
                power_set_bit = (1 << 1) if power_set else (1 << 3)

                # Write to eeprom
                with open(self.port_to_power_mode_mapping[self.index], "w") as fd:
                    fd.write(str((power_override_bit | power_set_bit)))
                    time.sleep(0.01)
                    fd.close()
            except Exception as e:
                print('Error: unable to open file: ', str(e))
                fd.close()
                return False
            return True
        elif self.sfp_type == QSFP_DD_TYPE:
            try:
                power_override_bit = (1 << 6)
                power_set_bit = (1 << 4) if power_set else (0 << 4)

                # Write to eeprom
                with open(self.port_to_power_mode_mapping[self.index], "w") as fd:
                    fd.write(str((power_override_bit | power_set_bit)))
                    time.sleep(0.01)
                    fd.close()
            except Exception as e:
                print('Error: unable to open file: ', str(e))
                fd.close()
                return False
            return True

    def get_name(self):
        """
        Retrieves the name of the device
            Returns:
            string: The name of the device
        """
        try:
            with open(self.port_to_name_mapping[self.index], 'r') as sfp_name:
                name = sfp_name.read()
        except IOError:
            name = "Unknown"

        return name

    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        return self.get_presence() and not self.get_reset_status()

    def get_position_in_parent(self):
        """
        Returns:
            Temp return 0
        """
        return 0

    def is_replaceable(self):
        """
        Retrieves if replaceable
        Returns:
            A boolean value, True if replaceable
        """
        return True

    def get_error_description(self):
        """
        Get error description

        Args:
            error_code: The error code returned by _get_error_code

        Returns:
            The error description
        """
        if self.get_presence():
            return self.SFP_STATUS_OK
        else:
            return self.SFP_STATUS_UNPLUGGED

    def read_eeprom(self, offset, num_bytes):
        """
        read eeprom specfic bytes beginning from a random offset with size as num_bytes

        Args:
             offset :
                     Integer, the offset from which the read transaction will start
             num_bytes:
                     Integer, the number of bytes to be read

        Returns:
            bytearray, if raw sequence of bytes are read correctly from the offset of size num_bytes
            None, if the read_eeprom fails
        """
        if not self.get_presence():
            return None
        if self.sfp_type == None:
            return None

        return bytearray([int(x, 16) for x in self._read_eeprom_specific_bytes(offset, num_bytes)])

    def write_eeprom(self, offset, num_bytes, write_buffer):
        """
        write eeprom specfic bytes beginning from a random offset with size as num_bytes
        and write_buffer as the required bytes

        Args:
             offset :
                     Integer, the offset from which the read transaction will start
             num_bytes:
                     Integer, the number of bytes to be written
             write_buffer:
                     bytearray, raw bytes buffer which is to be written beginning at the offset

        Returns:
            a Boolean, true if the write succeeded and false if it did not succeed.
        """
        if not self.get_presence():
            return False
        if not (self.sfp_type == None):
            #offset check
            if offset == (0x12 * 128 + 128):
                # Write to eeprom
                with open(self.port_to_grid_mapping[self.index], "w") as fd:
                    fd.write(str((int(str(write_buffer.hex()), 16))))
                    time.sleep(0.01)
                    fd.close()
            elif offset == (0x12 * 128 + 136):
                # Write to eeprom
                with open(self.port_to_freq_mapping[self.index], "w") as fd:
                    fd.write(str((int(str(write_buffer.hex()), 16))))
                    time.sleep(0.01)
                    fd.close()
            elif offset == (0x12 * 128 + 200):
                # Write to eeprom
                with open(self.port_to_outp_mapping[self.index], "w") as fd:
                    fd.write(str((int(str(write_buffer.hex()), 16))))
                    time.sleep(0.01)
                    fd.close()
            else:
                return False
        else:
            return False

    def _read_eeprom_specific_bytes(self, offset, num_bytes, page = 0):
        sysfsfile_eeprom = None
        eeprom_raw = []
        for i in range(0, num_bytes):
            eeprom_raw.append("0x00")

        if offset < 256:
            pg = 0
        else:
            pg = (offset // 128) - 1
            offset = (offset % 128)

        if pg == 0x0:
            if offset < 128:
                sysfs_sfp_i2c_client_eeprom_path = self.port_to_eeprom_low_mapping[self.index]
            else:
                sysfs_sfp_i2c_client_eeprom_path = self.port_to_eeprom_0_mapping[self.index]
                offset = offset - 128
        elif pg == 0x1:
            sysfs_sfp_i2c_client_eeprom_path = self.port_to_eeprom_1_mapping[self.index]
        elif pg == 0x2:
            sysfs_sfp_i2c_client_eeprom_path = self.port_to_eeprom_2_mapping[self.index]
        elif pg == 0x3:
            sysfs_sfp_i2c_client_eeprom_path = self.port_to_eeprom_3_mapping[self.index]
        elif pg == 0x4:
            sysfs_sfp_i2c_client_eeprom_path = self.port_to_eeprom_4_mapping[self.index]
        elif pg == 0x10:
            sysfs_sfp_i2c_client_eeprom_path = self.port_to_eeprom3_mapping[self.index]
        elif pg == 0x11:
            sysfs_sfp_i2c_client_eeprom_path = self.port_to_eeprom_11_mapping[self.index]
        else:
            return eeprom_raw

        try:
            sysfsfile_eeprom = open(sysfs_sfp_i2c_client_eeprom_path, mode="rb", buffering=0)
            sysfsfile_eeprom.seek(offset)
            raw = sysfsfile_eeprom.read(num_bytes)
            if sys.version_info[0] >= 3:
                for n in range(0, num_bytes):
                    eeprom_raw[n] = hex(raw[n])[2:].zfill(2)
            else:
                for n in range(0, num_bytes):
                    eeprom_raw[n] = hex(ord(raw[n]))[2:].zfill(2)

        except BaseException:
            pass
        finally:
            if sysfsfile_eeprom:
                sysfsfile_eeprom.close()

        return eeprom_raw

