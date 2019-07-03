#!/usr/bin/env python

#############################################################################
# DELLEMC
#
# Module contains an implementation of SONiC Platform Base API and
# provides the platform information
#
#############################################################################

try:
    import os
    import sys
    import click
    import subprocess
    import glob
    import sonic_device_util
    from commands import getstatusoutput
    from sonic_platform_base.platform_base import PlatformBase
    from sonic_platform_base.chassis_base import ChassisBase
    from sonic_platform_base.fan_base import FanBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class Chassis(ChassisBase):
    """
    DELLEMC Platform-specific Chassis class
    """

    HWMON_DIR = "/sys/devices/platform/SMF.512/hwmon/"
    HWMON_NODE = os.listdir(HWMON_DIR)[0]
    MAILBOX_DIR = HWMON_DIR + HWMON_NODE

    reset_reason_dict = {}
    reset_reason_dict[11] = ChassisBase.REBOOT_CAUSE_POWER_LOSS
    reset_reason_dict[33] = ChassisBase.REBOOT_CAUSE_WATCHDOG
    reset_reason_dict[44] = ChassisBase.REBOOT_CAUSE_NON_HARDWARE
    reset_reason_dict[55] = ChassisBase.REBOOT_CAUSE_NON_HARDWARE

    power_reason_dict = {}
    power_reason_dict[11] = ChassisBase.REBOOT_CAUSE_POWER_LOSS
    power_reason_dict[22] = ChassisBase.REBOOT_CAUSE_THERMAL_OVERLOAD_CPU
    power_reason_dict[33] = ChassisBase.REBOOT_CAUSE_THERMAL_OVERLOAD_ASIC
    power_reason_dict[44] = ChassisBase.REBOOT_CAUSE_INSUFFICIENT_FAN_SPEED

    _component_name_list = ["BIOS", "CPLD1", "CPLD2", "FPGA"]

    def __init__(self):
        ChassisBase.__init__(self)

    def get_pmc_register(self, reg_name):
        rv = 'ERR'
        mb_reg_file = self.MAILBOX_DIR+'/'+reg_name

        if (not os.path.isfile(mb_reg_file)):
            print mb_reg_file,  'not found !'
            return rv

        try:
            with open(mb_reg_file, 'r') as fd:
                rv = fd.read()
        except Exception as error:
            logging.error("Unable to open ", mb_reg_file, "file !")

        rv = rv.rstrip('\r\n')
        rv = rv.lstrip(" ")
        return rv

    # Run bash command and print output to stdout
    def run_command(self, command):
        click.echo(click.style("Command: ", fg='cyan') +
                   click.style(command, fg='green'))

        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        (out, err) = proc.communicate()

        click.echo(out)

        if proc.returncode != 0:
            sys.exit(proc.returncode)

    def get_reboot_cause(self):
        """
        Retrieves the cause of the previous reboot
        """
        reset_reason = int(self.get_pmc_register('smf_reset_reason'))
        power_reason = int(self.get_pmc_register('smf_poweron_reason'))

        # Reset_Reason = 11 ==> PowerLoss
        # So return the reboot reason from Last Power_Reason Dictionary
        # If Reset_Reason is not 11 return from Reset_Reason dictionary
        # Also check if power_reason, reset_reason are valid values by
        # checking key presence in dictionary else return
        # REBOOT_CAUSE_HARDWARE_OTHER as the Power_Reason and Reset_Reason
        # registers returned invalid data
        if (reset_reason == 11):
            if (power_reason in self.power_reason_dict):
                return (self.power_reason_dict[power_reason], None)
        else:
            if (reset_reason in self.reset_reason_dict):
                return (self.reset_reason_dict[reset_reason], None)

        return (ChassisBase.REBOOT_CAUSE_HARDWARE_OTHER, "Invalid Reason")

    def get_component_name_list(self):
        """
        Retrieves chassis components list such as BIOS, CPLD, FPGA, etc.

        Returns:
            A list containing component name.
        """
        return self._component_name_list

    def get_firmware_version(self, component_name):

        version = None

        if component_name in self._component_name_list:

            if component_name == self._component_name_list[0]:  # BIOS
                status, version = getstatusoutput(
                                        "dmidecode -s system-version")

            elif component_name == self._component_name_list[1]:  # CPLD1
                version = None

            elif component_name == self._component_name_list[2]:  # CPLD2
                version = None

            elif component_name == self._component_name_list[3]:  # SMF
                version = None

        return version

    def install_component_firmware(self, component_name, image_path):

        bios_image = None
        bios_version = "3.25.0."
        bios_file_name = "S6100*BIOS*"
        flashrom = "/usr/local/bin/flashrom"
        PLATFORM_ROOT_PATH = '/usr/share/sonic/device'
        machine_info = sonic_device_util.get_machine_info()
        platform = sonic_device_util.get_platform_info(machine_info)
        platform_path = "/".join([PLATFORM_ROOT_PATH, platform, "bin"])

        warning = """
        ********************************************************************
        * Warning - Upgrading BIOS is inherently risky and should only be  *
        * attempted when necessary.  A failure at this upgrade may cause   *
        * a board RMA.  Proceed with caution !                             *
        ********************************************************************
        """

        if component_name in self._component_name_list:
            if component_name == self._component_name_list[0]:  # BIOS

                # current BIOS version
                current_bios_version = self.get_firmware_version("BIOS")

                # Construct BIOS image path
                if image_path is not None:
                    image_path = image_path + platform_path
                    for name in glob.glob(
                                    os.path.join(image_path, bios_file_name)):
                        bios_image = image_path = name

                if not bios_image:
                    print "BIOS image file not found:", image_path
                    return False

                # Extract BIOS image version
                bios_image = os.path.basename(bios_image)
                bios_image = bios_image.strip('S6100-BIOS-')
                bios_image_version = bios_image.strip('.bin')

                if bios_image_version.startswith(bios_version):
                    bios_image_minor = bios_image_version.replace(
                                                bios_image_version[:7], '')
                    if bios_image_minor.startswith("2"):
                        bios_image_minor = bios_image_minor.split("-")[1]

                if current_bios_version.startswith(bios_version):
                    current_bios_minor = current_bios_version.replace(
                                                current_bios_version[:7], '')
                    if current_bios_minor.startswith("2"):
                        current_bios_minor = current_bios_minor.split("-")[1]

                # BIOS version check
                if bios_image_minor > current_bios_minor:

                    print warning
                    prompt_text = "New BIOS image " + bios_image_version + \
                        " available to install, continue?"
                    yes = click.confirm(prompt_text)

                elif current_bios_minor > bios_image_minor:

                    print warning
                    prompt_text = "Do you want to downgrade BIOS image from " \
                        + current_bios_version + " to " + \
                        bios_image_version + " continue?"

                    yes = click.confirm(prompt_text)

                else:
                    print("BIOS is already with {} latest version".format(
                        current_bios_version))
                    return True

                if yes:
                    command = flashrom + " -p" + " internal" + " -w " + \
                                         image_path
                    self.run_command(command)

            elif component_name == self._component_name_list[1]:  # CPLD1
                return False

            elif component_name == self._component_name_list[2]:  # CPLD2
                return False

            elif component_name == self._component_name_list[3]:  # SMF
                return False
        else:
            print "Invalid component Name:", component_name

        return True

