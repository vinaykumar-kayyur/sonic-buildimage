#!/usr/bin/env python
# @Company ：Celestica
# @Time    : 2023/3/2 10:19
# @Mail    : yajiang@celestica.com
# @Author  : jiang tao

try:
    import os
    import sys
    import time
    import syslog
    from . import helper
    from . import component
    from .watchdog import Watchdog
    import subprocess
    from .event import XcvrEvent
    from sonic_py_common import logger
    from sonic_platform_pddf_base.pddf_chassis import PddfChassis
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

HOST_REBOOT_CAUSE_PATH = "/host/reboot-cause/"
REBOOT_CAUSE_FILE = "reboot-cause.txt"
WATCHDOG_TIMELEFT_PATH = "/sys/class/watchdog/watchdog0/timeleft"
GET_REBOOT_CAUSE = "0x3a 0x64 0x00 0x01 0x06"


class Chassis(PddfChassis):
    """
    PDDF Platform-specific Chassis class
    """

    def __init__(self, pddf_data=None, pddf_plugin_data=None):
        self.helper = helper.APIHelper()
        PddfChassis.__init__(self, pddf_data, pddf_plugin_data)

        for index in range(self.platform_inventory['num_component']):
            component_obj = component.Component(index)
            self._component_list.append(component_obj)

    def get_sfp(self, index):
        """
        Retrieves sfp represented by (1-based) index <index>
        For Quanta the index in sfputil.py starts from 1, so override
        Args:
            index: An integer, the index (1-based) of the sfp to retrieve.
            The index should be the sequence of a physical port in a chassis,
            starting from 1.
        Returns:
            An object dervied from SfpBase representing the specified sfp
        """
        sfp = None

        try:
            if index == 0:
                raise IndexError
            sfp = self._sfp_list[index - 1]
        except IndexError:
            sys.stderr.write("override: SFP index {} out of range (1-{})\n".format(
                index, len(self._sfp_list)))

        return sfp

    def get_reboot_cause(self):
        """
        Retrieves the cause of the previous reboot
        Returns:
            A tuple (string, string) where the first element is a string
            containing the cause of the previous reboot. This string must be
            one of the predefined strings in this class. If the first string
            is "REBOOT_CAUSE_HARDWARE_OTHER", the second string can be used
            to pass a description of the reboot cause.
            REBOOT_CAUSE_POWER_LOSS = "Power Loss"
            REBOOT_CAUSE_THERMAL_OVERLOAD_CPU = "Thermal Overload: CPU"
            REBOOT_CAUSE_THERMAL_OVERLOAD_ASIC = "Thermal Overload: ASIC"
            REBOOT_CAUSE_THERMAL_OVERLOAD_OTHER = "Thermal Overload: Other"
            REBOOT_CAUSE_INSUFFICIENT_FAN_SPEED = "Insufficient Fan Speed"
            REBOOT_CAUSE_WATCHDOG = "Watchdog"
            REBOOT_CAUSE_HARDWARE_OTHER = "Hardware - Other"
            REBOOT_CAUSE_NON_HARDWARE = "Non-Hardware"
        """
        reboot_cause_path = (HOST_REBOOT_CAUSE_PATH + REBOOT_CAUSE_FILE)
        sw_reboot_cause = self.helper.read_txt_file(reboot_cause_path) or "Unknown"
        status_wat, val = self.helper.run_command("cat %s" % WATCHDOG_TIMELEFT_PATH)
        status, hw_reboot_cause = self.helper.ipmi_raw(GET_REBOOT_CAUSE)
        if float(val) <= 1 and float(hw_reboot_cause) == 44:
            hw_reboot_cause = "66"

        prev_reboot_cause = {
            '11': (self.REBOOT_CAUSE_POWER_LOSS, "The last reset is Power on reset"),
            '22': (self.REBOOT_CAUSE_HARDWARE_OTHER, "The last reset is soft-set CPU warm reset"),
            '33': (self.REBOOT_CAUSE_NON_HARDWARE, "The last reset is CPU cold reset"),
            '44': (self.REBOOT_CAUSE_NON_HARDWARE, "The last reset is CPU warm reset"),
            '66': (self.REBOOT_CAUSE_WATCHDOG, "The last reset is watchdog reset"),

        }.get(hw_reboot_cause, (self.REBOOT_CAUSE_HARDWARE_OTHER, 'Unknown reason'))

        if sw_reboot_cause != 'Unknown':
            prev_reboot_cause = (self.REBOOT_CAUSE_NON_HARDWARE, sw_reboot_cause)

        return prev_reboot_cause

    def get_watchdog(self):
        """
        Retreives hardware watchdog device on this chassis

        Returns:
            An object derived from WatchdogBase representing the hardware
            watchdog device
        """

        try:

            if self._watchdog is None:
                # Create the watchdog Instance
                self._watchdog = Watchdog()
        except Exception as E:
            syslog.syslog(syslog.LOG_ERR, "Fail to load watchdog due to {}".format(E))
        return self._watchdog

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
        # SFP event
        if self.get_num_sfps() == 0:
            for index in range(self.platform_inventory['num_ports']):
                sfp = Sfp(index, self.pddf_obj, self.plugin_data)
                self._sfp_list.append(sfp)

        succeed, sfp_event = XcvrEvent(self._sfp_list).get_xcvr_event(timeout)
        if succeed:
            return True, {'sfp': sfp_event}
        return False, {'sfp': {}}
