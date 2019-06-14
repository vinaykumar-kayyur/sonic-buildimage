#!/usr/bin/env python

#############################################################################
# Celestica
#
# Module contains an implementation of SONiC Platform Base API and
# provides the components firmware management fucntion
#
#############################################################################

try:
    from sonic_platform_base.device_base import DeviceBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class Device(DeviceBase):
    """Platform-specific Device class"""

    MODULES_NAME = ["CPLD1", "CPLD2", "CPLD3", "CPLD4", "BIOS"]

    def __init__(self, index, device_type):
        self.device_type = device_type
        self.index = index
        DeviceBase.__init__(self)

    def get_name(self):
        """
        Retrieves the name of the device

        Returns:
            string: The name of the device
        """
        device_name = {
            "module": self.MODULES_NAME[self.index]
        }.get(self.device_type, None)
        return device_name
