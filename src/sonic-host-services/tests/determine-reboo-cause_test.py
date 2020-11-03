import imp
import sys
import os
import pytest

import swsssdk

from unittest import mock

BUILTINS = "builtins"

from .mock_connector import MockConnector

swsssdk.SonicV2Connector = MockConnector

test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
scripts_path = os.path.join(modules_path, "scripts")
sys.path.insert(0, modules_path)

PROC_CMDLINE_CONTENTS = """\
BOOT_IMAGE=/image-20191130.52/boot/vmlinuz-4.9.0-11-2-amd64 root=/dev/sda4 rw console=tty0 console=ttyS1,9600n8 quiet net.ifnames=0 biosdevname=0 loop=image-20191130.52/fs.squashfs loopfstype=squashfs apparmor=1 security=apparmor varlog_size=4096 usbcore.autosuspend=-1 module_blacklist=gpio_ich SONIC_BOOT_TYPE=warm"""

EXPECTED_PARSE_WARMFAST_REBOOT_FROM_PROC_CMDLINE = "warm"

PROC_CMDLINE_CONTENTS = """\
BOOT_IMAGE=/image-20191130.52/boot/vmlinuz-4.9.0-11-2-amd64 root=/dev/sda4 rw console=tty0 console=ttyS1,9600n8 quiet net.ifnames=0 biosdevname=0 loop=image-20191130.52/fs.squashfs loopfstype=squashfs apparmor=1 security=apparmor varlog_size=4096 usbcore.autosuspend=-1 module_blacklist=gpio_ich SONIC_BOOT_TYPE=warm"""

REBOOT_CAUSE_CONTENTS = """\
User issued 'warm-reboot' command [User: admin, Time: Mon Nov  2 22:37:45 UTC 2020]""" 

GET_SONIC_VERSION_INFO = "SONiC.20191130.52"

EXPECTED_PARSE_WARMFAST_REBOOT_FROM_PROC_CMDLINE = "warm"
EXPECTED_FIND_SOFTWARE_REBOOT_CAUSE_USER = "User issued 'warm-reboot' command [User: admin, Time: Mon Nov  2 22:37:45 UTC 2020]"
EXPECTED_FIND_SOFTWARE_REBOOT_CAUSE_FIRSTBOOT = "Unknown (First boot of SONiC version {})".format(GET_SONIC_VERSION_INFO)

imp.load_source('determine-reboot-cause', scripts_path + '/determine-reboot-cause')
from determine-reboot-cause import *

class TestDetermineRebootCause(object):
    def test_parse_warmfast_reboot_from_proc_cmdline(self):
        with mock.patch("os.path.isfile") as mock_isfile: 
            mock_isfile.return_value = True 
            open_mocked = mock.mock_open(read_data=PROC_CMDLINE_CONTENTS) 
            with mock.patch("{}.open".format(BUILTINS), open_mocked): 
                result = determine-reboot-cause.parse_warmfast_reboot_from_proc_cmdline() 
                assert result == EXPECTED_PARSE_WARMFAST_REBOOT_FROM_PROC_CMDLINE
                open_mocked.assert_called_once_with("/proc/cmdline") 

    def test_find_software_reboot_cause_user(self):
        with mock.patch("os.path.isfile") as mock_isfile: 
            mock_isfile.return_value = True 
            open_mocked = mock.mock_open(read_data=REBOOT_CAUSE_CONTENTS) 
            with mock.patch("{}.open".format(BUILTINS), open_mocked): 
                result = determine-reboot-cause.find_software_reboot-cause() 
                assert result == EXPECTED_FIND_SOFTWARE_REBOOT_CAUSE_USER
                open_mocked.assert_called_once_with("/host/reboot-cause/reboot-cause.txt") 

    def test_find_software_reboot_cause_first_boot(self):
        with mock.patch("os.path.isfile") as mock_isfile: 
            mock_isfile.return_value = True 
            with mock.patch("sonic_py_common.device_info.get_sonic_version_info") as get_sonic_version_info_mocked:
                get_sonic_version_info_mocked.return_value = GET_SONIC_VERSION_INFO
                result = determine-reboot-cause.find_software_reboot_cause() 
                assert result == EXPECTED_FIND_SOFTWARE_REBOOT_CAUSE_FIRSTBOOT

    def test_find_proc_cmdline_reboot_cause(self):
        with mock.patch("determine-reboot-cause.parse_warmfast_reboot_from_proc_cmdline") as parse_reboot_from_cmdline_mocked:
            parse_reboot_from_cmdline_mocked.return_value = "fast"
            result = determine-reboot-cause.find_proc_cmdline_reboot_cause() 
            assert result == "fast"

    def test_find_hardware_reboot_cause(self):
        with mock.patch("sonic_platform.platform.Platform.get_chassis.get_reboot_cause") as get_hw_reboot_cause_mocked:
            get_hw_reboot_cause_mocked.return_value = {"Powerloss", ""}
            result = determine-reboot-cause.find_hardware_reboot_cause() 
            assert result == "Powerloss"

    def test_create_prev_cause_history_file_and_symlink(self):
        reboot_cause_dict = determine-reboot-cause.get_reboot_cause_dict("Unknown","") 
        determine-reboot-cause.create_prev_cause_history_file_and_symlink(reboot_cause_dict)
        assert os.path.isfile("/host/reboot-cause/previous-reboot-cause.json")
