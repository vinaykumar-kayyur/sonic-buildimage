#!/usr/bin/env python

#############################################################################
# Mellanox
#
# implementation of new platform api
#############################################################################
from __future__ import print_function
try:
    from sonic_platform_base.component_base import ComponentBase
    from glob import glob
    import subprocess
    import io
    import re
    import sys
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

#components definitions
COMPONENT_BIOS = "BIOS"
COMPONENT_CPLD = "CPLD"

BIOS_QUERY_VERSION_COMMAND = 'dmidecode -t 11'
CPLD_VERSION_FILE_PATTERN = '/var/run/hw-management/system/cpld[0-9]_version'
CPLD_VERSION_MAX_LENGTH = 4

CPLD_UPDATE_COMMAND = "cpldupdate --dev {} {}"
CPLD_INSTALL_SUCCESS_FLAG = "PASS!"

MST_DEVICE_PATTERN = "/dev/mst/mt[0-9]*_pciconf0"
MACHINE_CONF_FILE = "/host/machine.conf"
MACHINE_CONF_MAX_SIZE = 2048

BIOS_VERSION_PARSE_PATTERN = 'OEM[\s]*Strings\n[\s]*String[\s]*1:[\s]*([0-9a-zA-Z_\.]*)'
ONIE_VERSION_PARSE_PATTERN = 'onie_version=[0-9]{4}\.[0-9]{2}-([0-9]+)\.([0-9]+)\.([0-9]+)'
ONIE_VERSION_MAJOR_OFFSET = 1
ONIE_VERSION_MINOR_OFFSET = 2
ONIE_VERSION_RELEASE_OFFSET = 3
# To update BIOS requires the ONIE with version 5.2.0016 or upper
ONIE_REQUIRED_MAJOR = "5"
ONIE_REQUIRED_MINOR = "2"
ONIE_REQUIRED_RELEASE = "0016"

ONIE_FW_UPDATE_CMD_ADD = "/usr/bin/onie-fw-update add {}"
ONIE_FW_UPDATE_CMD_UPDATE = "/usr/bin/onie-fw-update update"

class Component(ComponentBase):
    def get_name(self):
        """
        Retrieves the name of the component

        Returns:
            A string containing the name of the component
        """
        return self.name


    def _read_generic_file(self, filename, len):
        """
        Read a generic file, returns the contents of the file
        """
        result = ''
        try:
            with io.open(filename, 'r') as fileobj:
                result = fileobj.read(len)
            return result
        except IOError as e:
            raise RuntimeError("Failed to read file {} due to {}".format(filename, repr(e)))


    def _get_command_result(self, cmdline):
        try:
            proc = subprocess.Popen(cmdline, stdout=subprocess.PIPE, shell=True, stderr=subprocess.STDOUT)
            stdout = proc.communicate()[0]
            proc.wait()
            result = stdout.rstrip('\n')

        except OSError as e:
            raise RuntimeError("Failed to execute command {} due to {}".format(cmdline, repr(e)))

        return result


    def _does_file_exist(self, image_path):
        image = glob(image_path)
        if not image:
            return False, "Failed to get the image file via {} or multiple files matched".format(image_path)
        if len(image) != 1:
            return False, "Multiple files {} matched {}".format(image, image_path)
        return True, ""


class ComponentBIOS(Component):
    def __init__(self):
        self.name = COMPONENT_BIOS


    def get_description(self):
        """
        Retrieves the description of the component

        Returns:
            A string containing the description of the component
        """
        return "BIOS - Basic Input/Output System"


    def get_firmware_version(self):
        """
        Retrieves the firmware version of the component

        Returns:
            A string containing the firmware version of the component

        BIOS version is retrieved via command 'dmidecode -t 11'
        which should return result in the following convention
            # dmidecode 3.0
            Getting SMBIOS data from sysfs.
            SMBIOS 2.7 present.

            Handle 0x0022, DMI type 11, 5 bytes
            OEM Strings
                    String 1:*0ABZS017_02.02.002*
                    String 2: To Be Filled By O.E.M.

        By using regular expression 'OEM[\s]*Strings\n[\s]*String[\s]*1:[\s]*([0-9a-zA-Z_\.]*)'
        we can extrace the version string which is marked with * in the above context
        """
        bios_ver_str = self._get_command_result(BIOS_QUERY_VERSION_COMMAND)
        try:
            m = re.search(BIOS_VERSION_PARSE_PATTERN, bios_ver_str)
            result = m.group(1)
        except AttributeError as e:
            raise RuntimeError("Failed to parse BIOS version by {} from {} due to {}".format(
                               BIOS_VERSION_PARSE_PATTERN, bios_ver_str, repr(e)))

        return result


    def install_firmware(self, image_path):
        """
        Installs firmware to the component

        Args:
            image_path: A string, path to firmware image

        Returns:
            A boolean, True if install was successful, False if not
        """
        # check ONIE version. To update ONIE requires version 5.2.0016 or later.
        machine_conf = self._read_generic_file(MACHINE_CONF_FILE, MACHINE_CONF_MAX_SIZE)
        try:
            m = re.search(ONIE_VERSION_PARSE_PATTERN, machine_conf)
            onie_major = m.group(ONIE_VERSION_MAJOR_OFFSET)
            onie_minor = m.group(ONIE_VERSION_MINOR_OFFSET)
            onie_release = m.group(ONIE_VERSION_RELEASE_OFFSET)
        except AttributeError as e:
            print("Failed to parse ONIE version by {} from {} due to {}".format(
                                BIOS_VERSION_PARSE_PATTERN, machine_conf, repr(e)))
            return False
        if onie_major < ONIE_REQUIRED_MAJOR or onie_minor < ONIE_REQUIRED_MINOR or onie_release < ONIE_REQUIRED_RELEASE:
            print("ONIE {}.{}.{} or later is required".format(ONIE_REQUIRED_MAJOR, ONIE_REQUIRED_MINOR, ONIE_REQUIRED_RELEASE))
            return False

        # check whether the file exists
        image_exists, message = self._does_file_exist(image_path)
        if not image_exists:
            print(message)
            return False

        # do the real work.
        try:
            result = subprocess.call(ONIE_FW_UPDATE_CMD_ADD.format(image_path).split())
            if result:
                return False
            result = subprocess.call(ONIE_FW_UPDATE_CMD_UPDATE.split())
            if result:
                return False
        except Exception as e:
            print("Installing BIOS failed due to {}".format(repr(e)))
            return False

        print("Reboot via \"/sbin/reboot\" is required to finish BIOS installation.")
        print("Please don't try installing a new sonic image before BIOS installation finishing")
        return True


class ComponentCPLD(Component):
    def __init__(self):
        self.name = COMPONENT_CPLD


    def get_description(self):
        """
        Retrieves the description of the component

        Returns:
            A string containing the description of the component
        """
        return "CPLD - includes all CPLDs in the switch"


    def get_firmware_version(self):
        """
        Retrieves the firmware version of the component

        Returns:
            A string containing the firmware version of the component
        """
        cpld_version_file_list = glob(CPLD_VERSION_FILE_PATTERN)
        cpld_version = ''
        if cpld_version_file_list is not None and cpld_version_file_list:
            cpld_version_file_list.sort()
            for version_file in cpld_version_file_list:
                version = self._read_generic_file(version_file, CPLD_VERSION_MAX_LENGTH)
                if not cpld_version == '':
                    cpld_version += '.'
                cpld_version += version.rstrip('\n')
        else:
            raise RuntimeError("Failed to get CPLD version files by matching {}".format(CPLD_VERSION_FILE_PATTERN))

        return cpld_version


    def install_firmware(self, image_path):
        """
        Installs firmware to the component

        Args:
            image_path: A string, path to firmware image

        Returns:
            A boolean, True if install was successful, False if not

        Details:
            The command "cpldupdate" is provided to install CPLD. There are two ways to do it:
                1. To burn CPLD via gpio, which is faster but only supported on new systems, like Anaconda, ...
                2. To install CPLD via firmware, which is slower but supported on older systems.
                   This also requires the mst device designated.
            "cpldupdate --dev <devname> <vme_file>" has the logic of testing whether to update via gpio is supported,
            and if so then go this way, otherwise tries updating software via fw. So we take advantage of it to update the CPLD. 
            By doing so we don't have to mind whether to update via gpio supported, which belongs to hardware details.

            So the procedure should be:
                1. Test whether the file exists
                2. Fetch the mst device name
                3. Update CPLD via executing "cpldupdate --dev <devname> <vme_file>"
                4. Check the result
        """
        # check whether the file exists
        image_exists, message = self._does_file_exist(image_path)
        if not image_exists:
            print(message)
            return False

        mst_dev_list = glob(MST_DEVICE_PATTERN)
        if not mst_dev_list or not len(mst_dev_list) == 1:
            print("Failed to get mst device which is required for CPLD updating or multiple device files matched")
            return False

        cmdline = CPLD_UPDATE_COMMAND.format(mst_dev_list[0], image_path)
        outputline = ""
        success_flag = False
        try:
            proc = subprocess.Popen(cmdline, stdout=subprocess.PIPE, shell=True, stderr=subprocess.STDOUT)
            while True:
                out = proc.stdout.read(1)
                if out == '' and proc.poll() != None:
                    break
                if out != '':
                    sys.stdout.write(out)
                    sys.stdout.flush()
                    outputline += out
                if (out == '\n' or out == '\r') and len(outputline):
                    m = re.search(CPLD_INSTALL_SUCCESS_FLAG, outputline)
                    if m and m.group(0) == CPLD_INSTALL_SUCCESS_FLAG:
                        success_flag = True

        except OSError as e:
            raise RuntimeError("Failed to execute command {} due to {}".format(cmdline, repr(e)))

        if success_flag:
            print("Success. Refresh or power cycle is required to finish CPLD installation.")
        else:
            print("Failed to install CPLD")

        return success_flag
