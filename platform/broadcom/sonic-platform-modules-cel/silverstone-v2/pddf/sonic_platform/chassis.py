#!/usr/bin/env python
# @Company ：Celestica
# @Time    : 2023/5/26 15:37
# @Mail    : yajiang@celestica.com
# @Author  : jiang tao

try:
    import sys
    import time
    import syslog
    import subprocess
    from . import helper
    from . import component
    from .watchdog import Watchdog
    from sonic_platform_pddf_base.pddf_chassis import PddfChassis
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

HOST_REBOOT_CAUSE_PATH = "/host/reboot-cause/"
REBOOT_CAUSE_FILE = "reboot-cause.txt"
WATCHDOG_TIMELEFT_PATH = "/sys/class/watchdog/watchdog0/timeleft"
GET_REBOOT_CAUSE = "i2cget -y -f 100 0x0d 0x06 | tr a-z A-Z | cut -d 'X' -f 2"
SET_SYS_STATUS_LED = "i2cget -y -f 100 0x0d 0x62 | tr a-z A-Z | cut -d 'X' -f 2"
SET_LED_MODE_Manual = "i2cget -y -f 100 0x0d 0x06 | tr a-z A-Z | cut -d 'X' -f 2"

class Chassis(PddfChassis):
    """
    PDDF Platform-specific Chassis class
    """
    sfp_status_dict = {}

    def __init__(self, pddf_data=None, pddf_plugin_data=None):
        self.helper = helper.APIHelper()
        PddfChassis.__init__(self, pddf_data, pddf_plugin_data)

        for port_idx in range(1, self.platform_inventory['num_ports'] + 1):
            present = self.get_sfp(port_idx).get_presence()
            self.sfp_status_dict[port_idx] = '1' if present else '0'

        for index in range(self.platform_inventory['num_component']):
            component_obj = component.Component(index)
            self._component_list.append(component_obj)

    @staticmethod
    def _getstatusoutput(cmd):
        try:
            data = subprocess.check_output(cmd, shell=True,
                                           universal_newlines=True, stderr=subprocess.STDOUT)
            status = 0
        except subprocess.CalledProcessError as ex:
            data = ex.output
            status = ex.returncode
        if data[-1:] == '\n':
            data = data[:-1]
        return status, data

    @staticmethod
    def initizalize_system_led():
        return True

    def get_status_led(self):
        return self.get_system_led("SYS_LED")

    def set_status_led(self, color):
        # ALARM_LED
        print("rancho test {}".format(color))
        if color == self.get_status_led():
            return False
        result, output = self.set_system_led("SYS_LED", color)
        print("result=%s  output=%s" % (result, output))
        # status, res = self.helper.ipmi_raw(SET_LED_MODE_Manual)
        # if status != 0:
        #     return False
        #
        # color_val = "0x1"
        # if color == "green":
        #     color_val = "0x1"
        # elif color == "amber":
        #     color_val = "0x2"
        # status, res = self.helper.ipmi_raw(SET_SYS_STATUS_LED.format(color_val))
        #
        # return True if status else False

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
        status, hw_reboot_cause = self.helper.run_command(GET_REBOOT_CAUSE)
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
        sfp_dict = {}

        sfp_removed = '0'
        sfp_inserted = '1'

        sfp_present = True
        sfp_absent = False

        start_time = time.time()
        time_period = timeout / float(1000)  # Convert msecs to secss

        while time.time() < (start_time + time_period) or timeout == 0:
            for port_idx in range(1, self.platform_inventory['num_ports'] + 1):
                if self.sfp_status_dict[port_idx] == sfp_removed and \
                        self.get_sfp(port_idx).get_presence() == sfp_present:
                    sfp_dict[port_idx] = sfp_inserted
                    self.sfp_status_dict[port_idx] = sfp_inserted
                elif self.sfp_status_dict[port_idx] == sfp_inserted and \
                        self.get_sfp(port_idx).get_presence() == sfp_absent:
                    sfp_dict[port_idx] = sfp_removed
                    self.sfp_status_dict[port_idx] = sfp_removed

            if sfp_dict:
                return True, {'sfp': sfp_dict}

            time.sleep(0.5)

        return True, {'sfp': {}}  # Timeout
