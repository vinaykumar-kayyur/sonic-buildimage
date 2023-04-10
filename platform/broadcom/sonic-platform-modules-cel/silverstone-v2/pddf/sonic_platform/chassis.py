#!/usr/bin/env python
# @Company ：Celestica
# @Time    : 2023/3/2 10:19
# @Mail    : J_Talong@163.com yajiang@celestica.com
# @Author  : jiang tao

try:
    import os
    import sys
    import time
    import syslog
    from . import helper
    from . import component
    from .watchdog import Watchdog
    from sonic_platform_pddf_base.pddf_chassis import PddfChassis
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

HOST_REBOOT_CAUSE_PATH = "/host/reboot-cause/"
REBOOT_CAUSE_FILE = "reboot-cause.txt"
WATCHDOG_TIMELEFT_PATH = "/sys/class/watchdog/watchdog0/timeleft"
GET_REBOOT_CAUSE = "0x3a 0x64 0x00 0x01 0x06"

Sensor_List_Info = "/tmp/sensor_info.log"
Sensor_Info_Update_Period_Secs = 60


class Chassis(PddfChassis):
    """
    PDDF Platform-specific Chassis class
    """

    def __init__(self, pddf_data=None, pddf_plugin_data=None):
        self.helper = helper.APIHelper()
        self.__refresh_sensor_list_info()
        PddfChassis.__init__(self, pddf_data, pddf_plugin_data)

        for index in range(self.platform_inventory['num_component']):
            component_obj = component.Component(index)
            self._component_list.append(component_obj)

    def __refresh_sensor_list_info(self):
        """
        refresh the sensor list informal in sensor_info.log.
        The refresh interval is 60 seconds
        """
        if not os.path.exists(Sensor_List_Info):
            self.__write_sensor_list_info()

        with open(Sensor_List_Info, "r") as f:
            log_time = f.readline()
        if time.time() - float(log_time.strip()) > Sensor_Info_Update_Period_Secs:
            self.__write_sensor_list_info()

    def __write_sensor_list_info(self):
        """
        Write the log of the command 'ipmitool sensor list' in sensor_info.log
        """
        status, info = self.helper.run_command("ipmitool sensor list")
        if not status:
            print("Fail! Can't get sensor list info by command: ipmitool sensor list")
            return False
        with open(Sensor_List_Info, "w") as f:
            f.write("%s\n%s" % (str(time.time()), info))
        return True

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
