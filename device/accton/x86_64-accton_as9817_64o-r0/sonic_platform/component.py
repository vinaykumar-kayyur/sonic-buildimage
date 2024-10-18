#############################################################################
# Edgecore
#
# Component contains an implementation of SONiC Platform Base API and
# provides the components firmware management function
#
#############################################################################

try:
    import os
    import json
    from sonic_platform_base.component_base import ComponentBase
    from .helper import APIHelper
    from sonic_py_common.general import getstatusoutput_noshell
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

PLATFORM_SYSFS_PATH = "/sys/devices/platform"
CPLD_SYSFS_MAPPING = {
    "CPLD1": "as9817_64_fpga/cpld1_version",
    "CPLD2": "as9817_64_fpga/cpld2_version",
    "CPLD3": "as9817_64_fan/hwmon/hwmon*/version",
    "FPGA": "as9817_64_sys/fpga_version",
}
BIOS_VERSION_PATH = "/sys/class/dmi/id/bios_version"

COMPONENT_LIST= [
   ("CPLD1", "CPLD 1"),
   ("CPLD2", "CPLD 2"),
   ("CPLD3", "FAN CPLD"),
   ("FPGA", "FPGA"),
   ("BIOS", "Basic Input/Output System")
]

class Component(ComponentBase):
    """Platform-specific Component class"""

    DEVICE_TYPE = "component"

    def __init__(self, component_index=0):
        ComponentBase.__init__(self)
        self._api_helper = APIHelper()
        self.index = component_index
        self.name = self.get_name()

    def __get_bios_version(self):
        # Retrieves the BIOS firmware version
        try:
            with open(BIOS_VERSION_PATH, 'r') as fd:
                bios_version = fd.read()
                return bios_version.strip()
        except Exception as e:
            return None

    def __get_cpld_version(self, cpld_name):
        # Retrieves the CPLD firmware version
        cpld_version = 'None'
        try:
            cpld_path = CPLD_SYSFS_MAPPING[cpld_name]
            version_path = "{}/{}".format(PLATFORM_SYSFS_PATH, cpld_path)
            cpld_version_raw = self._api_helper.glob_read_txt_file(version_path)
            if cpld_version_raw is not None:
                cpld_version = "{}".format(float(cpld_version_raw))
        except Exception as e:
            pass

        return cpld_version

    def get_name(self):
        """
        Retrieves the name of the component
         Returns:
            A string containing the name of the component
        """
        return COMPONENT_LIST[self.index][0]

    def get_description(self):
        """
        Retrieves the description of the component
            Returns:
            A string containing the description of the component
        """
        return COMPONENT_LIST[self.index][1]

    def get_firmware_version(self):
        """
        Retrieves the firmware version of module
        Returns:
            string: The firmware versions of the module
        """
        fw_version = None

        if self.name == "BIOS":
            fw_version = self.__get_bios_version()
        elif "CPLD" in self.name or "FPGA" in self.name:
            cpld_version = self.__get_cpld_version(self.name)
            fw_version = cpld_version
        return fw_version

    def install_firmware(self, image_path):
        """
        Install firmware to module
        Args:
            image_path: A string, path to firmware image
        Returns:
            A boolean, True if install successfully, False if not
        """
        return False

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
        return 'N/A'

    def get_serial(self):
        """
        Retrieves the serial number of the device
        Returns:
            string: Serial number of device
        """
        return 'N/A'

    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        return True

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
        return -1

    def is_replaceable(self):
        """
        Indicate whether this device is replaceable.
        Returns:
            bool: True if it is replaceable.
        """
        return False

