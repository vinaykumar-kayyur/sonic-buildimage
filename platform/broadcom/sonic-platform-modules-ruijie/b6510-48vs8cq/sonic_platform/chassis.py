#!/usr/bin/env python
# -*- coding: utf-8 -*-

#############################################################################
# Ruijie B6510-48VS8CQ
#
# Module contains an implementation of SONiC Platform Base API and
# provides the platform information
#
#############################################################################

try:
    import time
    import commands
    from sonic_platform_base.chassis_base import ChassisBase
    from sonic_platform.sfp import Sfp
    from sonic_platform.psu import Psu
    from sonic_platform.fan import Fan
    from sonic_platform.thermal import Thermal
    from sonic_platform.component import Component
    from sonic_platform.eeprom import Eeprom
    from sonic_platform.logger import logger
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

PORT_START = 0
PORT_END = 55
PORTS_IN_BLOCK = 56


class Chassis(ChassisBase):
    """
    Ruijie B6510-48VS8CQ Platform-specific Chassis class
    """

    SFP_STATUS_INSERTED = "1"
    SFP_STATUS_REMOVED = "0"
    port_dict = {}

    def __init__(self):
        ChassisBase.__init__(self)
        self.enable_read= "i2cset -f -y 2 0x35 0x2a 0x01"
        self.disable_read = "i2cset -f -y 2 0x35 0x2a 0x00"
        self.enable_write = "i2cset -f -y 2 0x35 0x2b 0x00"
        self.disable_write = "i2cset -f -y 2 0x35 0x2b 0x01"
        self.enable_erase = "i2cset -f -y 2 0x35 0x2c 0x01"
        self.disable_erase = "i2cset -f -y 2 0x35 0x2c 0x00"
        self.read_value = "i2cget -f -y 2 0x35 0x25"
        self.write_value = "i2cset -f -y 2 0x35 0x21 0x0a"

        # Initialize SFP list

        # sfp.py will read eeprom contents and retrive the eeprom data.
        # It will also provide support sfp controls like reset and setting
        # low power mode.
        # We pass the eeprom path and sfp control path from chassis.py
        # So that sfp.py implementation can be generic to all platforms
        for index in range(PORT_START, PORTS_IN_BLOCK):
            sfp_node = Sfp(index)
            self._sfp_list.append(sfp_node)
            if sfp_node.get_presence():
                self.port_dict[index] = self.SFP_STATUS_INSERTED
            else:
                self.port_dict[index] = self.SFP_STATUS_REMOVED

        try:
            from sonic_platform.config import DEVICE_CONF

            # init config
            self._init_by_config(DEVICE_CONF)
            self._eeprom = Eeprom(config=DEVICE_CONF.get("eeprom"))
        except ImportError:
            raise ImportError (str(e) + "- required module not found")

    def _init_standard_config(self, conflist, class_name, objlist):
        for conf in conflist:
            obj = globals()[class_name](conf.get("name"), config=conf)
            objlist.append(obj)

    def _init_by_config(self, config):
        # init component list
        coms = config.get("components")
        if coms and isinstance(coms, list):
            self._init_standard_config(coms, Component.__name__, self._component_list)

        # init fan list
        fans = config.get("fans")
        if fans and isinstance(fans, list):
            self._init_standard_config(fans, Fan.__name__, self._fan_list)

        # init psu list
        psus = config.get("psus")
        if psus and isinstance(psus, list):
            self._init_standard_config(psus, Psu.__name__, self._psu_list)

        # int thermal list
        thermals = config.get("thermals")
        if thermals and isinstance(thermals, list):
            self._init_standard_config(thermals, Thermal.__name__, self._thermal_list)

    def _init_by_hal(self, hal_interface):
        self.hal_interface = hal_interface
        self.hal_interface.get_fans()

    def get_name(self):
        """
        Retrieves the name of the chassis
        Returns:
            string: The name of the chassis
        """
        return self._eeprom.modelstr()

    def get_presence(self):
        """
        Retrieves the presence of the chassis
        Returns:
            bool: True if chassis is present, False if not
        """
        return True

    def get_model(self):
        """
        Retrieves the model number (or part number) of the chassis
        Returns:
            string: Model/part number of chassis
        """
        return self._eeprom.part_number_str()

    def get_serial(self):
        """
        Retrieves the serial number of the chassis (Service tag)
        Returns:
            string: Serial number of chassis
        """
        return self._eeprom.serial_str()

    def get_status(self):
        """
        Retrieves the operational status of the chassis
        Returns:
            bool: A boolean value, True if chassis is operating properly
            False if not
        """
        return True

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
            A string containing the hardware serial number for this
            chassis.
        """
        return self._eeprom.serial_number_str()

    def get_system_eeprom_info(self):
        """
        Retrieves the full content of system EEPROM information for the chassis
        Returns:
            A dictionary where keys are the type code defined in
            OCP ONIE TlvInfo EEPROM format and values are their corresponding
            values.
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
        try:
            is_power_loss = False
            # enable read
            commands.getstatusoutput(self.disable_write)
            commands.getstatusoutput(self.enable_read)
            ret , log = commands.getstatusoutput(self.read_value)
            if ret == 0 and "0x0a" in log:
                is_power_loss = True

            # erase i2c and e2
            commands.getstatusoutput(self.enable_erase)
            time.sleep(1)
            commands.getstatusoutput(self.disable_erase)
            # clear data
            commands.getstatusoutput(self.enable_write)
            commands.getstatusoutput(self.disable_read)
            commands.getstatusoutput(self.disable_write)
            commands.getstatusoutput(self.enable_read)
            # enable write and set data
            commands.getstatusoutput(self.enable_write)
            commands.getstatusoutput(self.disable_read)
            commands.getstatusoutput(self.write_value)
            if is_power_loss:
                return(self.REBOOT_CAUSE_POWER_LOSS, None)
        except Exception as e:
            logger.error(str(e))

        return (self.REBOOT_CAUSE_NON_HARDWARE, None)

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
                  Specifically for SFP event, besides SFP plug in and plug out,
                  there are some other error event could be raised from SFP, when
                  these error happened, SFP eeprom will not be avalaible, XCVRD shall
                  stop to read eeprom before SFP recovered from error status.
                      status='2' I2C bus stuck,
                      status='3' Bad eeprom,
                      status='4' Unsupported cable,
                      status='5' High Temperature,
                      status='6' Bad cable.
        """
        change_event_dict = {"fan": {}, "sfp": {}}
        sfp_status, sfp_change_dict = self.get_transceiver_change_event(timeout)
        change_event_dict["sfp"] = sfp_change_dict
        if sfp_status is True:
            return True, change_event_dict

        return False, {}

    def get_transceiver_change_event(self, timeout=0):

        start_time = time.time()
        currernt_port_dict = {}
        forever = False

        if timeout == 0:
            forever = True
        elif timeout > 0:
            timeout = timeout / float(1000)  # Convert to secs
        else:
            print("get_transceiver_change_event:Invalid timeout value", timeout)
            return False, {}

        end_time = start_time + timeout
        if start_time > end_time:
            print(
                "get_transceiver_change_event:" "time wrap / invalid timeout value",
                timeout,
            )
            return False, {}  # Time wrap or possibly incorrect timeout

        while timeout >= 0:
            # Check for OIR events and return updated port_dict
            for index in range(PORT_START, PORTS_IN_BLOCK):
                if self._sfp_list[index].get_presence():
                    currernt_port_dict[index] = self.SFP_STATUS_INSERTED
                else:
                    currernt_port_dict[index] = self.SFP_STATUS_REMOVED
            if currernt_port_dict == self.port_dict:
                if forever:
                    time.sleep(1)
                else:
                    timeout = end_time - time.time()
                    if timeout >= 1:
                        time.sleep(1)  # We poll at 1 second granularity
                    else:
                        if timeout > 0:
                            time.sleep(timeout)
                        return True, {}
            else:
                # Update reg value
                self.port_dict = currernt_port_dict
                print(self.port_dict)
                return True, self.port_dict
        print("get_transceiver_change_event: Should not reach here.")
        return False, {}
