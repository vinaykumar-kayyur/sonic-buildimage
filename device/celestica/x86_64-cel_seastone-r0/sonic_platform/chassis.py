#!/usr/bin/env python

#############################################################################
# Celestica
#
# Module contains an implementation of SONiC Platform Base API and
# provides the Chassis information which are available in the platform
#
#############################################################################

try:
    import subprocess
    from sonic_platform_base.chassis_base import ChassisBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

RESET_REGISTER = "0x103"
GETREG_PATH = "/sys/devices/platform/dx010_cpld/getreg"
HOST_REBOOT_CAUSE_PATH = "/host/reboot-cause/"
REBOOT_CAUSE_FILE = "reboot-cause.txt"
PREV_REBOOT_CAUSE_FILE = "previous-reboot-cause.txt"


class Chassis(ChassisBase):
    """Platform-specific Chassis class"""

    def __init__(self):
        ChassisBase.__init__(self)

    def __get_register_value(self, register):
        # Retrieves the cpld register value
        cmd = "echo {1} > {0}; cat {0}".format(GETREG_PATH, register)
        p = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        raw_data, err = p.communicate()
        if err is not '':
            return None
        return raw_data.strip()

    def __read_txt_file(self, file_path):
        try:
            with open(file_path, 'r') as fd:
                data = fd.read()
                return data.strip()
        except IOError:
            pass
        return None

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
        description = 'Unknown reason'

        reboot_cause_path = (HOST_REBOOT_CAUSE_PATH + REBOOT_CAUSE_FILE)
        prev_reboot_cause_path = (HOST_REBOOT_CAUSE_PATH + PREV_REBOOT_CAUSE_FILE)

        hw_reboot_cause = self.__get_register_value(RESET_REGISTER)

        sw_reboot_cause = self.__read_txt_file(
            reboot_cause_path) or "Unknown"
        prev_sw_reboot_cause = self.__read_txt_file(
            prev_reboot_cause_path) or "Unknown"

        if sw_reboot_cause == "Unknown" and (prev_sw_reboot_cause == "Unknown" or prev_sw_reboot_cause == self.REBOOT_CAUSE_POWER_LOSS) and hw_reboot_cause == "0x11":
            reboot_cause = self.REBOOT_CAUSE_POWER_LOSS
        elif sw_reboot_cause != "Unknown" and hw_reboot_cause == "0x11":
            reboot_cause = self.REBOOT_CAUSE_NON_HARDWARE
            description = sw_reboot_cause
        elif prev_reboot_cause_path != "Unknown" and hw_reboot_cause == "0x11":
            reboot_cause = self.REBOOT_CAUSE_NON_HARDWARE
            description = prev_sw_reboot_cause
        elif hw_reboot_cause == "0x22":
            reboot_cause = self.REBOOT_CAUSE_WATCHDOG,
        else:
            reboot_cause = self.REBOOT_CAUSE_HARDWARE_OTHER
            description = 'Unknown reason'

        return (reboot_cause, description)
