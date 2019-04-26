#!/usr/bin/env python

import os.path
import subprocess
import click
import os

try:
    from sonic_fw.fw_manage_base import FwBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class FwUtil(FwBase):
    """Platform-specific FwUtil class"""

    CPLD_ADDR_MAPPING = {
        "CPLD1": "0x100",
        "CPLD2": "0x200",
        "CPLD3": "0x280",
        "CPLD4": "0x300",
        "CPLD5": "0x380"
    }
    SUPPORTED_MODULES = ["BIOS", "CPLD"]
    GETREG_PATH = "/sys/devices/platform/dx010_cpld/getreg"
    BIOS_VERSION_PATH = "/sys/class/dmi/id/bios_version"

    # Run bash command and print output to stdout
    def run_command(self, command):
        click.echo(click.style("Command: ", fg='cyan') +
                   click.style(command, fg='green'))

        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        (out, err) = proc.communicate()
        click.echo("")
        click.echo(out)

        if proc.returncode != 0:
            return False
        return True

    # Read register and return value
    def __get_register_value(self, path, register):
        cmd = "echo {1} > {0}; cat {0}".format(path, register)
        p = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        raw_data, err = p.communicate()
        if err is not '':
            return None
        return raw_data.strip()

    # Get BIOS firmware version
    def get_bios_version(self):
        try:
            with open(self.BIOS_VERSION_PATH, 'r') as fd:
                bios_version = fd.read()
                return bios_version.strip()
        except Exception, e:
            return None

    # Get CPLD firmware version
    def get_cpld_version(self):
        cpld_version = dict()
        for cpld_name in self.CPLD_ADDR_MAPPING:
            try:
                cpld_addr = self.CPLD_ADDR_MAPPING[cpld_name]
                cpld_version_raw = self.__get_register_value(
                    self.GETREG_PATH, cpld_addr)
                cpld_version_str = "{}.{}".format(int(cpld_version_raw[2], 16), int(
                    cpld_version_raw[3], 16)) if cpld_version_raw is not None else 'None'
                cpld_version[cpld_name] = cpld_version_str
            except Exception, e:
                cpld_version[cpld_name] = 'None'
        return cpld_version

    def get_module_list(self):
        """
        Retrieves the list of module that available on the device

        :return: A list of modules
        """
        return self.SUPPORTED_MODULES

    def get_fw_version(self, module_name):
        """
        Retrieves the firmware version of module

        :param module_name: A string, module name
        :return: Dict, firmware version object
        """

        fw_version = {
            "BIOS": self.get_bios_version(),
            "CPLD": self.get_cpld_version()
        }.get(module_name.upper(), None)

        fw_dict = dict()
        fw_dict["module_name"] = module_name
        fw_dict["fw_version"] = fw_version
        fw_dict["has_submodule"] = True if type(fw_version) is dict else False

        return fw_dict

    def install(self, module_name, image_path):
        """
        Install firmware to module

        :param module_name: A string, name of module that need to install new firmware
        :param image_path: A string, path to firmware image 
        :return: Boolean
        """
        module_name = module_name.upper()

        if module_name == "CPLD":
            img_dir = os.path.dirname(image_path)
            img_name = os.path.basename(image_path)
            root, ext = os.path.splitext(img_name)
            ext = ".vme" if ext == "" else ext
            new_image_path = os.path.join(img_dir, (root.lower() + ext))
            os.rename(image_path, new_image_path)
            install_command = "ls"
            install_command = "ispvm %s" % new_image_path
        elif module_name == "BIOS":
            click.echo("Not supported")
            return False

        return self.run_command(install_command)
