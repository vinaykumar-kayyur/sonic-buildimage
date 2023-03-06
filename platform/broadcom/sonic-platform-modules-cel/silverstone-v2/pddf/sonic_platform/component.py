#!/usr/bin/env python
# -*- coding: utf-8 -*-#

# @Time   : 2023/3/3 17:09
# @Mail   : J_Talong@163.com yajiang@celestica.com
# @Author : jiang tao
#############################################################################
# Celestica
#
# Component contains an implementation of SONiC Platform Base API and
# provides the components firmware management function
#
#############################################################################
try:
    from sonic_platform_base.component_base import ComponentBase
    from . import helper
    import re
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

FPGA_VERSION_PATH = "/sys/devices/platform/fpga-sys/version"
SWCPLD1_VERSION_PATH = "/sys/bus/i2c/devices/i2c-10/10-0030/version"
SWCPLD2_VERSION_PATH = "/sys/bus/i2c/devices/i2c-10/10-0031/version"
BCPLD_VERSION_PATH = "/sys/devices/platform/sys_cpld/version"
BIOS_VERSION_PATH = "/sys/class/dmi/id/bios_version"


###################
Check_Bios_Boot = "0x3a 0x25 0x02"
Fan_CPLD_Cmd = "0x3a 0x64 02 01 00"
COME_CPLD_Cmd = "0x3a 0x3e 1 0x1a 1 0xe0"
Main_BMC_Cmd = "0x32 0x8f 0x08 0x01"
Backup_BMC_Cmd = "0x32 0x8f 0x08 0x01"
#########
COMPONENT_NAME_LIST = ["FPGA", "COME_CPLD", "SWCPLD1", "SWCPLD2", "FANCPLD", "SYSCPLD",
                       "Main_BMC", "Backup_BMC", "Main_BIOS", "Backup_BIOS"]
COMPONENT_DES_LIST = ["Used for managering the CPU and expanding I2C channels",
                      "Used for managing the CPU",
                      "Used for managing QSFP+ ports (1-16)",
                      "Used for managing QSFP+ ports (17-32)",
                      "Used for managing fans",
                      "Used for managing control the system power & reset",
                      "Main Baseboard Management Controller",
                      "Backup Baseboard Management Controller",
                      "Main basic Input/Output System",
                      "Backup basic Input/Output System"]


class Component(ComponentBase):
    """Platform-specific Component class"""

    DEVICE_TYPE = "component"

    def __init__(self, component_index):
        ComponentBase.__init__(self)
        self.index = component_index
        self.helper = helper.APIHelper()
        self.name = self.get_name()

    def __get_bios_version(self):
        """
        Get Bios version by command 'dmidecode -t bios | grep Version'
        return: Bios Version
        """
        bios_version_cmd = "dmidecode -t bios | grep Version"
        status, result = self.helper.ipmi_raw(Check_Bios_Boot)
        bios_version = "N/A"
        if not status:
            print("Fail! Unable to get the current Main bios or backup bios!")
            return bios_version
        status_ver, version_str = self.helper.run_command(bios_version_cmd)
        if not status:
            print("Fail! Unable to get the bios version!")
            return bios_version

        if result.strip() == "01":
            if self.name == "Main_BIOS":
                bios_version = re.findall(r"Version:(.*)", version_str)[0]
                return bios_version.strip()
            elif self.name == "Backup_BIOS":
                return bios_version

        elif result.strip() == "03":
            if self.name == "Backup_BIOS":
                bios_version = re.findall(r"Version:(.*)", version_str)[0]
                return bios_version.strip()
            elif self.name == "Main_BIOS":
                return bios_version

    def __get_cpld_version(self):
        # TODO need to overwrite -- Yagami
        version = "N/A"
        if self.name in ["COME_CPLD", "FANCPLD"]:
            version_cmd = COME_CPLD_Cmd if self.name == "COME_CPLD" else Fan_CPLD_Cmd
            status, ver = self.helper.ipmi_raw(version_cmd)
            if not status:
                print("Fail! Can't get %s version by command:%s" % (self.name, version_cmd))
                return version
            version1 = int(ver.strip()) / 10
            version2 = int(ver.strip()) % 10
            version = "%d.%d" % (version1, version2)
            return version
        else:
            if self.name == "SWCPLD1":
                return version
            elif self.name == "SYSCPLD":
                return version
            elif self.name == "SWCPLD2":
                return version

    def __get_fpga_version(self):
        # TODO need to overwrite -- Yagami
        return "N/A"

    def __get_bmc_version(self):
        """
        Get main/backup bmc version
        """
        version = "N/A"
        cmd = Main_BMC_Cmd if self.name == "Main_BMC" else Backup_BMC_Cmd
        status, result = self.helper.ipmi_raw(cmd)
        if not status:
            print("Fail! Can't get the %s version by command:%s" % (self.name, cmd))
            return version
        str_1 = str(int(result.strip().split(" ")[0]))
        str_2 = str(int(result.strip().split(" ")[1], 16))
        version = "%s.%s" % (str_1, str_2)
        return version

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
        return COMPONENT_DES_LIST[self.index]

    def get_firmware_version(self):
        """
        Retrieves the firmware version of module
        Returns:
            string: The firmware versions of the module
        """
        fw_version = None

        if "BIOS" in self.name:
            fw_version = self.__get_bios_version()
        elif "CPLD" in self.name:
            fw_version = self.__get_cpld_version()
        elif self.name == "FPGA":
            fw_version = self.__get_fpga_version()
        elif "BMC" in self.name:
            fw_version = self.__get_bmc_version()
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

    def update_firmware(self, image_path):
        # Not support
        return False
