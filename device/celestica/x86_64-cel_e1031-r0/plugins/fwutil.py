#!/usr/bin/env python

import sys
import os.path
import subprocess
import click
import os


class FwUtil():
    """Platform-specific FwUtil class"""

    def __init__(self):
        self.bios_version_path = "/sys/class/dmi/id/bios_version"
        self.smc_cpld_e1031_path = "/sys/devices/platform/e1031.smc/version"
        self.mmc_cpld_e1031_path = "/sys/devices/platform/e1031.smc/getreg"

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

    # Read register and resurn value
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
            with open(self.bios_version_path, 'r') as fd:
                bios_version = fd.read()
                return bios_version.strip()
        except Exception, e:
            return None

    # Get CPLD firmware version
    def get_cpld_version(self):
        try:
            with open(self.smc_cpld_e1031_path, 'r') as fd:
                smc_cpld_version = fd.read()

            smc_cpld_version = "{}.{}".format(int(smc_cpld_version[2], 16), int(
                smc_cpld_version[3], 16)) if smc_cpld_version is not None else smc_cpld_version

            mmc_cpld_version = self.__get_register_value(
                self.mmc_cpld_e1031_path, '0x100')
            mmc_cpld_version = "{}.{}".format(int(mmc_cpld_version[2], 16), int(
                mmc_cpld_version[3], 16)) if mmc_cpld_version is not None else mmc_cpld_version

            cpld_version = dict()
            cpld_version["SMC"] = str(smc_cpld_version)
            cpld_version["MMC"] = str(mmc_cpld_version)

            return cpld_version
        except Exception, e:
            return None

    def get_module_list(self):
        """
        Retrieves the list of module that available on the device

        :return: A list of module
        """
        return ["BIOS", "CPLD"]

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
