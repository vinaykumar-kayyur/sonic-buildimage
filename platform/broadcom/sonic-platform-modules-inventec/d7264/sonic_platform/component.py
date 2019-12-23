#!/usr/bin/env python

#############################################################################
# Inventec d7264
#
# Module contains an implementation of SONiC Platform Base API and
# provides the Component information
#
# version: 1.0
#############################################################################

try:
    import os
    import re
    from sonic_platform_base.component_base import ComponentBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


###############
# Global
###############
HWMON_CPLD1_PATH    = "/sys/class/hwmon/hwmon3/device/"
DMI_PATH            = "/sys/class/dmi/id/"

COMPONENT_NAME_LIST = [
    "CPLD_1",
    "BIOS"
]

COMPONENT_DESC_LIST = [
    "platform management and control LED",
    "platform interrupt event handle",
    "Basic Input/Output System"
]



class Component(ComponentBase):
    """Platform-specific Component class"""

    DEVICE_TYPE = "component"

    def __init__(self, component_index):
        self.index = component_index


    #######################
    # private function
    #######################

    def __get_attr_value(self, attr_path):

        retval = 'ERR'
        if (not os.path.isfile(attr_path)):
            return retval

        try:
            with open(attr_path, 'r') as fd:
                retval = fd.read()
        except Exception as error:
            logging.error("Unable to open ", attr_path, " file !")

        retval = retval.rstrip(' \t\n\r')
        return retval

    def __get_cpld_version(self):
        cpld_version = None
        attr_cpld_version = "info"

        if COMPONENT_NAME_LIST[self.index] == "CPLD_1":
            attr_path = HWMON_CPLD1_PATH + attr_cpld_version

        attr_rv = self.__get_attr_value(attr_path)
        if (attr_rv != 'ERR'):
            for line in attr_rv.split("\n"):
                re_rv = re.search(r"The CPLD version is (?P<version>.+)", line)
                if re_rv is not None:
                    cpld_version = re_rv.group("version")

        return cpld_version

    ####################
    # Device base
    ####################

    def get_name(self):
        """
        Retrieves the name of the component

        Returns:
            A string containing the name of the component
        """
        return COMPONENT_NAME_LIST[self.index]

    def get_description(self):
        """
        Retrieves the description of the component

        Returns:
            A string containing the description of the component
        """
        return COMPONENT_DESC_LIST[self.index]

    def get_firmware_version(self):
        """
        Retrieves the firmware version of the component

        Returns:
            A string containing the firmware version of the component
        """
        version = None
        attr_bios_version = "bios_date"

        if "CPLD" in COMPONENT_NAME_LIST[self.index]:
            version = self.__get_cpld_version()
        elif COMPONENT_NAME_LIST[self.index] == "BIOS":
            attr_path = DMI_PATH + attr_bios_version
            attr_rv = self.__get_attr_value(attr_path)
            if (attr_rv != 'ERR'):
                version = attr_rv

        return version

    def install_firmware(self, image_path):
        """
        Installs firmware to the component

        Args:
            image_path: A string, path to firmware image

        Returns:
            A boolean, True if install was successful, False if not
        """
        raise NotImplementedError