#!/usr/bin/env python
 
#############################################################################
# Inventec d7264
#
# Module contains an implementation of SONiC Platform Base API and
# provides the Chassis information
#
# version: 1.0
#############################################################################

try:
    from sonic_platform_base.chassis_base import ChassisBase
    from sonic_platform.component import Component
    from sonic_platform.eeprom import Eeprom
    from sonic_platform.watchdog import Watchdog
    from sonic_platform.psu import Psu
    from sonic_platform.fan import Fan
    from sonic_platform.sfp import Sfp
    from sonic_platform.qsfp import QSfp
    from sonic_platform.thermal import Thermal
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


###############
# Global
###############
NUM_PSU         = 2
NUM_FAN_TRAY    = 4
NUM_PORTS       = 64
QSFP_START      = 0
NUM_THERMAL     = 6
NUM_COMPONENT   = 2

class Chassis(ChassisBase):
    """Platform-specific Chassis class"""

    def __init__(self):
        # Initialize EEPROM and watchdog
        self._eeprom = Eeprom()
        self._watchdog = Watchdog()

        #Initialize FAN object
        for index in range(0, NUM_FAN_TRAY):
            fan = Fan(index)
            self._fan_list.append(fan)

        # Initialize PSU and PSU_fan object
        for index in range(0, NUM_PSU):
            psu = Psu(index)
            self._psu_list.append(psu)
            fan = Fan(index, True)
            self._fan_list.append(fan)

        # Initialize SFP/QSFP object
        for index in range(0, NUM_PORTS):
            if index < QSFP_START:
                sfp = Sfp(index)
            else:
                sfp = QSfp(index)
            self._sfp_list.append(sfp)

        # Initialize Thermal object
        for index in range(0, NUM_THERMAL):
            thermal = Thermal(index)
            self._thermal_list.append(thermal)

        # Initialize Component object
        for index in range(0, NUM_COMPONENT):
            component = Component(index)
            self._component_list.append(component)

    ####################
    # Device base 
    ####################

    def get_name(self):
        """
        Retrieves the name of the device

        Returns:
            string: The name of the device
        """
        return self._eeprom.modelstr()

    def get_presence(self):
        """
        Retrieves the presence of the device

        Returns:
            bool: True if device is present, False if not
        """
        return True

    def get_model(self):
        """
        Retrieves the model number (or part number) of the device

        Returns:
            string: Model/part number of device
        """
        return self._eeprom.part_number_str()

    def get_serial(self):
        """
        Retrieves the serial number of the device

        Returns:
            string: Serial number of device
        """
        return self._eeprom.serial_number_str()

    def get_status(self):
        """
        Retrieves the operational status of the device

        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        return True


    ####################
    # chassis base
    ####################

    def get_base_mac(self):
        """
        Retrieves the base MAC address for the chassis

        Returns:
            A string containing the MAC address in the format
            'XX:XX:XX:XX:XX:XX'
        """
        return self._eeprom.base_mac_addr()

    def get_serial_number(self):
        """
        Retrieves the hardware serial number for the chassis

        Returns:
            A string containing the hardware serial number for this chassis.
        """
        return self._eeprom.serial_number_str()

    def get_system_eeprom_info(self):
        """
        Retrieves the full content of system EEPROM information for the chassis

        Returns:
            A dictionary where keys are the type code defined in
            OCP ONIE TlvInfo EEPROM format and values are their corresponding
            values.
            Ex. { '0x21':'AG9064', '0x22':'V1.0', '0x23':'AG9064-0109867821',
                  '0x24':'001c0f000fcd0a', '0x25':'02/03/2018 16:22:00',
                  '0x26':'01', '0x27':'REV01', '0x28':'AG9064-C2358-16G'}
        """
        return self._eeprom.system_eeprom_info()

    def get_reboot_cause(self):
        """
        Retrieves the cause of the previous reboot

        Returns:
            A tuple (string, string) where the first element is a string
            containing the cause of the previous reboot. This string must be
            one of the predefined strings in this class. If the first string
            is "REBOOT_CAUSE_HARDWARE_OTHER", the second string can be used
            to pass a description of the reboot cause.
        """
        raise NotImplementedError


    ##############################################
    # Other methods
    ##############################################

    def get_change_event(self, timeout=0):
        """
        Returns a nested dictionary containing all devices which have
        experienced a change at chassis level

        Args:
            timeout: Timeout in milliseconds (optional). If timeout == 0,
                this method will block until a change is detected.

        Returns:
            (bool, dict):
                - True if call successful, False if not;
                - A nested dictionary where key is a device type,
                  value is a dictionary with key:value pairs in the format of
                  {'device_id':'device_event'},
                  where device_id is the device ID for this device and
                        device_event,
                             status='1' represents device inserted,
                             status='0' represents device removed.
                  Ex. {'fan':{'0':'0', '2':'1'}, 'sfp':{'11':'0'}}
                      indicates that fan 0 has been removed, fan 2
                      has been inserted and sfp 11 has been removed.
        """
        raise NotImplementedError
