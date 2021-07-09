#!/usr/bin/env python

########################################################################
#
# Module contains an implementation of SONiC Platform Base API and
# provides the Fan-Drawers' information available in the platform.
#
########################################################################

try:
    from sonic_platform_base.fan_drawer_base import FanDrawerBase
    from .helper import APIHelper
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

FANS_PER_FANTRAY = 1
CPLD_I2C_PATH = "/sys/devices/platform/as7535_32xb_fan/fan"

class FanDrawer(FanDrawerBase):
    """Platform-specific Fan class"""

    def __init__(self, fantray_index):
        self._api_helper = APIHelper()
        FanDrawerBase.__init__(self)
        self.fantrayindex = fantray_index

        # FanTray is 0-based in platforms
        self.__initialize_fan()

    def __initialize_fan(self):
        from sonic_platform.fan import Fan

        for i in range(FANS_PER_FANTRAY):
            self._fan_list.append(Fan(self.fantrayindex, i))

    def get_name(self):
        """
        Retrieves the fan drawer name
        Returns:
            string: The name of the device
        """
        return "FanTray-{}".format(self.fantrayindex)

    def is_replaceable(self):
        """
        Indicate whether this device is replaceable.
        Returns:
            bool: True if it is replaceable.
        """
        return True

    def get_presence(self):
        """
        Retrieves the presence of the FAN
        Returns:
            bool: True if FAN is present, False if not
        """
        present_path = "{}{}{}".format(CPLD_I2C_PATH, self.fantrayindex+1, '_present')
        val=self._api_helper.read_txt_file(present_path)

        if val is not None:
            return int(val, 10)==1

        return False

    def get_position_in_parent(self):
        """
        Retrieves 1-based relative physical position in parent device.
        If the agent cannot determine the parent-relative position
        for some reason, or if the associated value of
        entPhysicalContainedIn is'0', then the value '-1' is returned
        Returns:
            integer: The 1-based relative physical position in parent device
            or -1 if cannot determine the position
        """
        return self.fantrayindex+1
