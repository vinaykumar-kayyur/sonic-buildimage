#!/usr/bin/env python

#############################################################################
#
# Module contains an implementation of SONiC Platform Base API and
# provides the component information (such as CPLD, FPGA, BIOS etc) which are available in the platform
#
#############################################################################

try:
    from sonic_platform_base.component_base import ComponentBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

COMPONENT_NAME_LIST = ["CPLD1", "CPLD2", "CPLD3"]
COMPONENT_DES_LIST = ["Main board cpld 1 (0x60)", "Main board cpld 2 (0x62)", "Main board cpld 3 (0x64)"]

class Alpha_Component(ComponentBase):
    """Platform-specific Component class"""


    def __init__(self, component_index):
        self.index = component_index+1
        self.name = self.get_name()
        self.cpld_path = "/sys/bus/i2c/devices/"
        self.cpld_version = "/version"
        self.cpld_mapping = {
                1: "18-0060",
                2: "12-0062",
                3: "19-0064",
            }


    def get_name(self):
        """
        Retrieves the name of the component
         Returns:
            A string containing the name of the component
        """
        return COMPONENT_NAME_LIST[self.index-1]

    def get_description(self):
        """
        Retrieves the description of the component
            Returns:
            A string containing the description of the component
        """
        return COMPONENT_DES_LIST[self.index-1]

    def get_firmware_version(self):
        """
        Retrieves the firmware version of module
        Returns:
            string: The firmware versions of the module
        """
        cpld_version = None

        if "CPLD" in self.name:
            node = self.cpld_path + self.cpld_mapping[self.index] + self.cpld_version
            try:
                with open(node, 'r') as version:
                    cpld_version = version.read()
            except IOError:
                return None


            cpld_version = cpld_version.rstrip()

        return cpld_version

    def install_firmware(self, image_path):
        """
        Install firmware to module
        Args:
            image_path: A string, path to firmware image
        Returns:
            A boolean, True if install successfully, False if not
        """
        raise NotImplementedError
