#
# Copyright (c) 2021-2024 NVIDIA CORPORATION & AFFILIATES.
# Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import logging
import os
import queue
import sys
import syslog
import threading
import time
import types
import unittest

from mock import MagicMock, patch, mock_open, Mock
if sys.version_info.major == 3:
    from unittest import mock
else:
    import mock

test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
sys.path.insert(0, modules_path)

from sonic_platform import utils
import sonic_platform.chassis
from sonic_platform.chassis import Chassis
from sonic_platform.device_data import DeviceDataManager
from sonic_py_common import device_info
from sonic_platform import modules_mgmt
from sonic_platform.modules_mgmt import ModulesMgmtTask
from sonic_py_common.logger import Logger
from sonic_platform_base.sonic_xcvr.api.public.cmis import CmisApi
from sonic_platform_base.sonic_xcvr.api.public.c_cmis import CCmisApi
from sonic_platform_base.sonic_xcvr.xcvr_eeprom import XcvrEeprom
from sonic_platform_base.sonic_xcvr.codes.public.cmis import CmisCodes
from sonic_platform_base.sonic_xcvr.mem_maps.public.cmis import CmisMemMap
from sonic_platform_base.sonic_xcvr.fields import consts

sonic_platform.chassis.extract_RJ45_ports_index = mock.MagicMock(return_value=[])

logger = logging.getLogger()
logger.level = logging.DEBUG


class LoggerMock(object):
    """
    Logger class for SONiC Python applications
    """
    LOG_FACILITY_DAEMON = syslog.LOG_DAEMON
    LOG_FACILITY_USER = syslog.LOG_USER

    LOG_OPTION_NDELAY = syslog.LOG_NDELAY
    LOG_OPTION_PID = syslog.LOG_PID

    LOG_PRIORITY_ERROR = syslog.LOG_ERR
    LOG_PRIORITY_WARNING = syslog.LOG_WARNING
    LOG_PRIORITY_NOTICE = syslog.LOG_NOTICE
    LOG_PRIORITY_INFO = syslog.LOG_INFO
    LOG_PRIORITY_DEBUG = syslog.LOG_DEBUG

    DEFAULT_LOG_FACILITY = LOG_FACILITY_USER
    DEFAULT_LOG_OPTION = LOG_OPTION_NDELAY

    #syslog_to_logging_prio = { LOG_PRIORITY_INFO : logger.info}

    def __init__(self, log_identifier=None, log_facility=DEFAULT_LOG_FACILITY, log_option=DEFAULT_LOG_OPTION
                 , also_print_to_console=True):
        self._syslog = syslog

        if log_identifier is None:
            log_identifier = os.path.basename(sys.argv[0])

        # Initialize syslog
        self._syslog.openlog(ident=log_identifier, logoption=log_option, facility=log_facility)

        # Set the default minimum log priority to LOG_PRIORITY_NOTICE
        self.set_min_log_priority(self.LOG_PRIORITY_NOTICE)

        self.also_print_to_console = also_print_to_console


    def __del__(self):
        self._syslog.closelog()

    #
    # Methods for setting minimum log priority
    #

    def set_min_log_priority(self, priority):
        """
        Sets the minimum log priority level to <priority>. All log messages
        with a priority lower than <priority> will not be logged

        Args:
            priority: The minimum priority at which to log messages
        """
        self._min_log_priority = priority

    def set_min_log_priority_error(self):
        """
        Convenience function to set minimum log priority to LOG_PRIORITY_ERROR
        """
        self.set_min_log_priority(self.LOG_PRIORITY_ERROR)

    def set_min_log_priority_warning(self):
        """
        Convenience function to set minimum log priority to LOG_PRIORITY_WARNING
        """
        self.set_min_log_priority(self.LOG_PRIORITY_WARNING)

    def set_min_log_priority_notice(self):
        """
        Convenience function to set minimum log priority to LOG_PRIORITY_NOTICE
        """
        self.set_min_log_priority(self.LOG_PRIORITY_NOTICE)

    def set_min_log_priority_info(self):
        """
        Convenience function to set minimum log priority to LOG_PRIORITY_INFO
        """
        self.set_min_log_priority(self.LOG_PRIORITY_INFO)

    def set_min_log_priority_debug(self):
        """
        Convenience function to set minimum log priority to LOG_PRIORITY_DEBUG
        """
        self.set_min_log_priority(self.LOG_PRIORITY_DEBUG)

    #
    # Methods for logging messages
    #

    def log(self, priority, msg, also_print_to_console=True):
        if self._min_log_priority >= priority:
            # Send message to syslog
            self._syslog.syslog(priority, msg)

            # Send message to console
            if also_print_to_console:
                logger.info(msg)
                print(msg)

    def log_error(self, msg, also_print_to_console=False):
        self.log(self.LOG_PRIORITY_ERROR, msg, also_print_to_console)

    def log_warning(self, msg, also_print_to_console=False):
        self.log(self.LOG_PRIORITY_WARNING, msg, also_print_to_console)

    def log_notice(self, msg, also_print_to_console=False):
        self.log(self.LOG_PRIORITY_NOTICE, msg, also_print_to_console)

    def log_info(self, msg, also_print_to_console=True):
        self.log(self.LOG_PRIORITY_INFO, msg, also_print_to_console)
        print(msg)

    def log_debug(self, msg, also_print_to_console=False):
        self.log(self.LOG_PRIORITY_DEBUG, msg, also_print_to_console)


def _mock_sysfs_file_content():
    return {
        modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format("0"): "1",
        modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format("1"): "1",
        modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format("2"): "1",
        modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format("0"): "1",
        modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format("1"): "1",
        modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format("2"): "1",
        modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format("0"): "1",
        modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format("1"): "1",
        modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format("2"): "1",
        modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_LIMIT.format("0"): "48",
        modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_LIMIT.format("1"): "48",
        modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_LIMIT.format("2"): "48",
        modules_mgmt.SYSFS_INDEPENDENT_FD_FREQ_SUPPORT.format("0"): "0",
        modules_mgmt.SYSFS_INDEPENDENT_FD_FREQ_SUPPORT.format("1"): "0",
        modules_mgmt.SYSFS_INDEPENDENT_FD_FREQ_SUPPORT.format("2"): "0",
        modules_mgmt.SYSFS_INDEPENDENT_FD_HW_RESET: "",
        modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_LIMIT: "48",
        modules_mgmt.SYSFS_INDEPENDENT_FD_FW_CONTROL: "",
        modules_mgmt.SYSFS_LEGACY_FD_PRESENCE: "1",
        modules_mgmt.PROC_CMDLINE: ""
    }


mock_file_content = _mock_sysfs_file_content()


def mock_read_str_from_file(file_path, **kwargs):
    return mock_file_content[file_path]


def mock_write_file(file_path, content, **kwargs):
    mock_file_content[file_path] = content

class MockPoller:

    def __init__(self, modules_mgmt_task_stopping_event):
        self.fds_dict = {}
        self.poller_count = 0
        self.modules_mgmt_task_stopping_event = modules_mgmt_task_stopping_event

    def register(self, fd, attrs):
        self.fds_dict[fd.fileno()] = fd
        assert fd.fileno() in self.fds_dict
        print(f'test registered port fd {fd}')

    def poll(self, timeout=1000):
        # when simulating port plug out or plug in need to change both presence and power_good sysfs
        self.poller_count += 1
        print(f'test polling iteration {self.poller_count}')
        if 9 == self.poller_count:
            # return first fd registered with some made up event number 870
            fd_to_return = list(self.fds_dict.keys())[0]
            fd = self.fds_dict[fd_to_return]
            print(f'test MockPoller poll calling {fd}.set_file_int_content with value 0')
            print(f'fd {fd} fd.name {fd.name} fd.fileno() {fd.fileno()} dir {fd.__dir__}')
            fd.set_file_int_content(0)
            fd.set_bla(0)
            event_to_return = 870
            print(f'test polling returning fd and event {fd_to_return}, {event_to_return} on iteration {self.poller_count}')
            return [(fd_to_return,event_to_return)]
        else:
            # sleep_time = timeout/1000
            # print(f'test polling sleeping {sleep_time} seconds ...')
            # time.sleep(sleep_time)
            if 10 == self.poller_count:
                self.modules_mgmt_task_stopping_event.set()
            return []


class MockOpenNew:

    def __init__(self, name='', file_no=190, indep_mode=True):
        self.name = name
        self.file_no = file_no
        self.indep_mode = indep_mode
        self.retint = None

    def read(self):
        if self.fileno() in [99]:
            return "S"
        else:
            print(f'test mock_open_new reading file content')
            if self.retint:
                print(f'test mock_open_new returning file content {retint}')
                return self.retint
            else:
                print(f'test mock_open_new returning {_mock_sysfs_file_content()[self.name]}')
                return _mock_sysfs_file_content()[self.name]

    def readline(self):
        print(f'reading line fd file_no {self.fileno} fileno() {self.fileno()} self.indep_mode {self.indep_mode}')
        if self.fileno() in [99]:
            if self.indep_mode:
                return "SAI_INDEPENDENT_MODULE_MODE=1"
            else:
                return ""
        else:
            return _mock_sysfs_file_content()[self.name]

    def fileno(self):
        return self.file_no

    def set_file_int_content(self, retint):
        print(f'test mock_open_new setting file content {retint}')
        self.retint = retint

    # def __enter__(self):
    #     print(f"enter MockOpenNew name {self.name} file_no {self.file_no}")
    #
    # def __exit__(self):
    #     print(f"exit MockOpenNew name {self.name} file_no {self.file_no}")


class MockPollerStopEvent:

    def __init__(self, modules_mgmt_task_stopping_event, modules_mgmt_thrd=None, feature_enabled=True):
        self.fds_dict = {}
        self.modules_mgmt_thrd = modules_mgmt_thrd
        self.modules_mgmt_task_stopping_event = modules_mgmt_task_stopping_event
        self.feature_enabled = feature_enabled

    def register(self, fd, attrs):
        self.fds_dict[fd.fileno()] = 1 & attrs
        #assert fd.fileno() in [0, 1, 2]
        assert fd.fileno() in self.fds_dict
        print(f'test registered port fd {fd}')

    def poll(self, timeout=1000):
        print(f'test starting poll tests')
        assert len(self.modules_mgmt_thrd.sfp_port_dict_initial) == 3
        assert self.modules_mgmt_thrd.is_supported_indep_mods_system == self.feature_enabled
        #try:
        if True:
            print(f'test starting ports tests')
            for i in range(3 if not self.feature_enabled else 6):
                print(f'test port {i} starting tests')
                # when feature is enabled, power_good sysfs is also registered for cmis non-flat memory cables
                port_to_test = i if not self.feature_enabled else int(i / 2)
                assert self.modules_mgmt_thrd.sfp_port_dict_initial[port_to_test].port_num == port_to_test
                assert self.modules_mgmt_thrd.sfp_port_dict_initial[port_to_test].initial_state == modules_mgmt.STATE_HW_NOT_PRESENT
                if True:#not self.feature_enabled:
                    print(f'test getting module_obj for port {i}')
                    module_obj = self.modules_mgmt_thrd.fds_mapping_to_obj[list(self.fds_dict.keys())[i]]['module_obj']
                    assert module_obj.port_num == port_to_test
                    #assert module_obj.current_state == modules_mgmt.STATE_FW_CONTROL
                    #assert module_obj.final_state == modules_mgmt.STATE_FW_CONTROL
                    print(f'test port {i} final_state {module_obj.final_state}')
                    if self.feature_enabled:
                        assert module_obj.final_state == modules_mgmt.STATE_SW_CONTROL
                    else:
                        assert module_obj.final_state == modules_mgmt.STATE_HW_PRESENT
                #module_fd = self.fds_mapping_to_obj[fd]['fd']
                #fd_name = self.fds_mapping_to_obj[fd]['fd_name']
        # except IndexError as e:
        #     print(f'exception in test {e} on i {i}')
        self.modules_mgmt_task_stopping_event.set()
        return []


def _mock_is_file_indep_mode_disabled_content():
    return {
        modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE: True,
        modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD: True,
        modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON: True,
        modules_mgmt.SYSFS_INDEPENDENT_FD_HW_RESET: True,
        modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_LIMIT: True,
        modules_mgmt.SYSFS_INDEPENDENT_FD_FW_CONTROL: True,
        modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("0"): True,
        modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("1"): True,
        modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("2"): True,
        '//usr/share/sonic/platform/ACS-MSN4700/sai.profile'    :   True
    }


mock_is_file_indep_mode_disabled_content = _mock_is_file_indep_mode_disabled_content()


def mock_is_file_indep_mode_disabled(file_path, **kwargs):
    return mock_is_file_indep_mode_disabled_content[file_path]


def _mock_is_file_indep_mode_enabled_content():
    return {
        modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE: True,
        modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD: True,
        modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON: True,
        modules_mgmt.SYSFS_INDEPENDENT_FD_HW_RESET: True,
        modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_LIMIT: True,
        modules_mgmt.SYSFS_INDEPENDENT_FD_FW_CONTROL: True,
        modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format("0"): True,
        modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format("1"): True,
        modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format("2"): True,
        modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format("0"): True,
        modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format("1"): True,
        modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format("2"): True,
        modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format("0"): True,
        modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format("1"): True,
        modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format("2"): True,
        '//usr/share/sonic/platform/ACS-MSN4700/sai.profile'    :   True
    }


mock_is_file_indep_mode_enabled_content = _mock_is_file_indep_mode_enabled_content()


def mock_is_file_indep_mode_enabled(file_path, **kwargs):
    return mock_is_file_indep_mode_enabled_content[file_path]


def mock_read_int_from_file_new_no_self(filename, *args):
    return_dict = {
        modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("0") : 1,
        modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("1") : 1,
        modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("2") : 1
    }

    return return_dict[filename]


class MockXcvrEeprom():

    def __init__(self, is_flat_memory, mem_map):
        self.is_flat_memory = is_flat_memory
        self.mem_map = mem_map

    def is_cmis_api(self):
        return self.is_cmis_api

    def is_flat_memory(self):
        return self.is_flat_memory

    def read(self, field):
        print(f'test MockXcvrEeprom read field {field}')
        if consts.FLAT_MEM_FIELD == field:
            return 0 if self.is_flat_memory else 1
        else:
            return 0


class MockXcvrapi():
    # def __new__(cls, *args, **kwargs):
    #     return mock.Mock(autospec=cls)

    def __init__(self, is_cmis_api=True, is_flat_memory_bool=False):
        print(f'test MockXcvrapi init is_cmis_api {is_cmis_api} is_flat_memory_bool {is_flat_memory_bool}')
        self.is_cmis_api = is_cmis_api
        self.is_flat_memory_bool = is_flat_memory_bool
        self.xcvr_eeprom = MagicMock(autospec=XcvrEeprom, return_value=MockXcvrEeprom(False, CmisMemMap(CmisCodes)))

    def is_flat_memory(self):
        print(f'test returning for is_flat_memory {self.is_flat_memory_bool}')
        return self.is_flat_memory_bool

    def xcvr_eeprom(self):
        print(f'test returning xcvr_eeprom {self.xcvr_eeprom}')
        return self.xcvr_eeprom


class MockSFPxcvrapi:

    def __init__(self, xcvr_api_is_cmis_api=True, xcvr_eeprom_is_flat_memory=False):
        print(f'test MockSFPxcvrapi init xcvr_api_is_cmis_api {xcvr_api_is_cmis_api} xcvr_eeprom_is_flat_memory {xcvr_eeprom_is_flat_memory}')
        self.xcvr_api = Mock(spec=CmisApi(MockXcvrEeprom(False, CmisMemMap(CmisCodes))), return_value=MockXcvrapi(xcvr_api_is_cmis_api, xcvr_eeprom_is_flat_memory))
        self.xcvr_api_is_cmis_api = xcvr_api_is_cmis_api
        self.xcvr_eeprom_is_flat_memory = xcvr_eeprom_is_flat_memory
        self.xcvr_api.is_flat_memory = types.MethodType(self.is_flat_memory, self)
        #__enter__.return_value
        #self.xcvr_api.is_flat_memory = self.is_flat_memory()

    def get_xcvr_api(self):
        return self.xcvr_api

    def is_flat_memory(self, ref):
        print(f'test MockSFPxcvrapi returning is_flat_memory {self.xcvr_eeprom_is_flat_memory}')
        return self.xcvr_eeprom_is_flat_memory


mock_sfp_all_ports_cmis_api = {
    0: MockSFPxcvrapi(),
    1: MockSFPxcvrapi(),
    2: MockSFPxcvrapi()
}


def mock_sfp(port, *args, **kwargs):
    print(f'returning mock sfp for port {port}')
    return mock_sfp_all_ports_cmis_api[port]


def check_power_cap(port, module_sm_obj):
    pass

class TestModulesMgmt(unittest.TestCase):
    """Test class to test modules_mgmt.py. The test cases covers:
        1. cables detection for all 32 ports
        2. cable disconnection - plug out
        3. cable reconnection - plug in
    """

    fds_and_events = {'90': '1', '91': '2', '92': '3'}

    def _mock_sysfs_file_content(self):
        return {
            modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE : "1",
            modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD : "1",
            modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON : "0",
            modules_mgmt.SYSFS_INDEPENDENT_FD_HW_RESET : "",
            modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_LIMIT : "48",
            modules_mgmt.SYSFS_INDEPENDENT_FD_FW_CONTROL : "1",
            modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("0") : "1",
            modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("1") : "1",
            modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("2") : "1",
            modules_mgmt.SYSFS_INDEPENDENT_FD_FREQ_SUPPORT.format("0"): "0"
        }

    def mock_open_new(self, file_name, *args, **kwargs):
        return_dict = {
            (modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("0"), 'r') : MockOpenNew(modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("0"), 0),
            (modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("1"), 'r') : MockOpenNew(modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("1"), 1),
            (modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("2"), 'r') : MockOpenNew(modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("2"), 2),
            ('//usr/share/sonic/platform/ACS-MSN4700/sai.profile', 'r') : MockOpenNew('//usr/share/sonic/platform/ACS-MSN4700/sai.profile', 99)
        }
        return return_dict[file_name]

    def mock_open_builtin(self, file_name, feature_enabled=True):
        return_dict = {
            (modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("0"), 'r') : MockOpenNew(modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("0"), 0),
            (modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("1"), 'r') : MockOpenNew(modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("1"), 1),
            (modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("2"), 'r') : MockOpenNew(modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("2"), 2),
            '//usr/share/sonic/platform/ACS-MSN4700/sai.profile' : MockOpenNew('//usr/share/sonic/platform/ACS-MSN4700/sai.profile', 99, feature_enabled),
            modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("0") : MockOpenNew(name=modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("0"), file_no=0),
            modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("1") : MockOpenNew(modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("1"), 1),
            modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("2") : MockOpenNew(modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("2"), 2),
            #modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format("0"): MagicMock(return_value=MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format("0"), 0)),
            modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format("0"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format("0"), 0),
            modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format("1"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format("1"), 1),
            modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format("2"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format("2"), 2),
            modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format("0"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format("0"), 50),
            modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format("1"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format("1"), 51),
            modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format("2"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format("2"), 52),
            modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format("0"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format("0"), 90),
            modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format("1"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format("1"), 91),
            modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format("2"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format("2"), 92),
            modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_LIMIT.format("0"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_LIMIT.format("0"), 100),
            modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_LIMIT.format("1"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_LIMIT.format("1"), 101),
            modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_LIMIT.format("2"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_LIMIT.format("2"), 102),
            modules_mgmt.SYSFS_INDEPENDENT_FD_FREQ_SUPPORT.format("0"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_FREQ_SUPPORT.format("0"), 112),
            modules_mgmt.SYSFS_INDEPENDENT_FD_FREQ_SUPPORT.format("1"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_FREQ_SUPPORT.format("1"), 112),
            modules_mgmt.SYSFS_INDEPENDENT_FD_FREQ_SUPPORT.format("2"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_FREQ_SUPPORT.format("2"), 112),
            modules_mgmt.PROC_CMDLINE: MockOpenNew(modules_mgmt.PROC_CMDLINE, 200)
        }
        return return_dict[file_name]

    def mock_open_builtin_feature_enabled(self, file_name):
        return_dict = {
            (modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("0"), 'r') : MockOpenNew(modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("0"), 0),
            (modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("1"), 'r') : MockOpenNew(modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("1"), 1),
            (modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("2"), 'r') : MockOpenNew(modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("2"), 2),
            '//usr/share/sonic/platform/ACS-MSN4700/sai.profile' : MockOpenNew('//usr/share/sonic/platform/ACS-MSN4700/sai.profile', 99),
            modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("0") : MockOpenNew(name=modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("0"), file_no=0),
            modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("1") : MockOpenNew(modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("1"), 1),
            modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("2") : MockOpenNew(modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("2"), 2)
        }
        return return_dict[file_name]


    def mock_open_new_side_effect_feature_disabled(self, filename, *args, **kwargs):
        mock_context = MagicMock()
        #mock_context.__enter__.return_value = self.mock_open_builtin(filename, args, kwargs)
        mock_context.__enter__.return_value = self.mock_open_builtin(filename, False)
        mock_context.__exit__.return_value = False
        mock_context.return_value.__enter__.return_value.readline.return_value = "SAI_INDEPENDENT_MODULE_MODE=1"
        mock_context.return_value.readline.return_value = "SAI_INDEPENDENT_MODULE_MODE=1"
        return mock_context

    def mock_open_new_side_effect_feature_enabled(self, filename, *args, **kwargs):
        mock_context = MagicMock()
        #mock_context.__enter__.return_value = self.mock_open_builtin(filename, args, kwargs)
        mock_context.__enter__.return_value = self.mock_open_builtin(filename)
        #mock_context.__enter__.return_value = self.mock_open_builtin_feature_enabled(filename)
        mock_context.__exit__.return_value = False
        #mock_context.return_value.__enter__.return_value.readline.return_value = "SAI_INDEPENDENT_MODULE_MODE=1"
        #mock_context.return_value.readline.return_value = "SAI_INDEPENDENT_MODULE_MODE=1"
        return mock_context

    def mock_open_new_side_effect_poller_test(self, filename, *args, **kwargs):
        if filename in ['//usr/share/sonic/platform/ACS-MSN4700/sai.profile']:
            mock_context = MagicMock()
            mock_context.__enter__.return_value = MockOpenNew(filename, 99)
            mock_context.__exit__.return_value = False
            return mock_context
        else:
            #return MagicMock(return_value=MockOpenNew(filename, self.fd_number_by_fd_name_dict[filename]))
            mock_context = MagicMock()
            mock_open_new = MockOpenNew(filename, self.fd_number_by_fd_name_dict[filename])
            mock_context.return_value = mock_open_new
            #mock_open_new.return_value.read = mock_open_new.read
            #mock_context.return_value.__enter__ = MockOpenNew(filename, self.fd_number_by_fd_name_dict[filename])
            mock_context.__enter__.return_value = mock_open_new
            mock_context.__exit__.return_value = False
            if 'present' in filename or 'power' in filename or 'freq':
                return mock_context
            else:
                return mock_context.return_value


    @classmethod
    def setup_class(cls):
        os.environ["MLNX_PLATFORM_API_UNIT_TESTING"] = "1"
        #cls.mock_file_content = cls._mock_sysfs_file_content()
        cls.fd_number_by_fd_name_dict = {
                modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("0") : 0,
                modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("1") : 1,
                modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("2") : 2,
                '//usr/share/sonic/platform/ACS-MSN4700/sai.profile' : 99,
                modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format("0") : 0,
                modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format("1") : 1,
                modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format("2") : 2,
                modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format("0") : 50,
                modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format("1") : 51,
                modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format("2") : 52,
                modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format("0") : 90,
                modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format("1") : 91,
                modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format("2") : 92,
                modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_LIMIT.format("0") : 100,
                modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_LIMIT.format("1") : 101,
                modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_LIMIT.format("2") : 102,
                modules_mgmt.SYSFS_INDEPENDENT_FD_FREQ_SUPPORT.format("0") : 110,
                modules_mgmt.SYSFS_INDEPENDENT_FD_FREQ_SUPPORT.format("1") : 111,
                modules_mgmt.SYSFS_INDEPENDENT_FD_FREQ_SUPPORT.format("2") : 112,
                modules_mgmt.PROC_CMDLINE : 200
        }


    def mock_read_int_from_file(self, file_path, *args):
        return self._mock_sysfs_file_content[file_path]
        #return self._mock_sysfs_file_content[args]

    def mock_write_file(self, file_path, content, **kwargs):
        self._mock_sysfs_file_content[file_path] = content

    def mock_read_int_from_file_new(self, filename, *args):
        return_dict = {
            modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("0") : 1,
            modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("1") : 1,
            modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("2") : 1
        }

        return return_dict[filename]


    # builtin_open = open # save the unpatched version
    #
    # def mock_open(*args, **kwargs):
    #     if 'present' in args[0]:
    #         # mocked open for path "foo"
    #         return mock.mock_open(read_data="bar")(*args, **kwargs)
    #     # unpatched version for every other path
    #     return builtin_open(*args, **kwargs)

    @mock.patch('sonic_platform.device_data.DeviceDataManager.get_sfp_count', MagicMock(return_value=3))
    @patch('sonic_py_common.logger.Logger', Mock(return_value=LoggerMock))
    @patch('os.path.isfile', MagicMock(side_effect=mock_is_file_indep_mode_disabled))
    @patch('sonic_platform.utils.read_int_from_file', MagicMock(side_effect=mock_read_int_from_file_new_no_self))
    @patch('builtins.open', spec=open)
    def test_mdf_all_ports_feature_disabled(self, mock_open):

        #stream_handler = logging.StreamHandler(sys.stdout)
        #logger.addHandler(stream_handler)
        try:
            chassis = Chassis()
            chassis.modules_mgmt_thread.is_alive = MagicMock(return_value=True)
            mock_file_content = self._mock_sysfs_file_content()

            num_of_tested_ports = DeviceDataManager.get_sfp_count()
            assert num_of_tested_ports == 3

            device_info.get_paths_to_platform_and_hwsku_dirs = mock.MagicMock(return_value=('', '/usr/share/sonic/platform/ACS-MSN4700'))
            modules_mgmt_task_stopping_event = threading.Event()
            modules_changes_queue = queue.Queue()
            modules_mgmt_thrd = ModulesMgmtTask(main_thread_stop_event=modules_mgmt_task_stopping_event,
                                                q=modules_changes_queue)
            modules_mgmt_thrd.logger = logger
            thrd_stream_handler = logging.StreamHandler(sys.stdout)
            modules_mgmt_thrd.logger.addHandler(thrd_stream_handler)
            Logger.level = logging.DEBUG
            #logger_logger = Logger()
            #logger_logger.addHandler(thrd_stream_handler)
            #thrd_logger = ModulesMgmtTask.logger.getLogger()
            #thrd_stream_handler = logging.StreamHandler(sys.stdout)
            #thrd_logger.addHandler(thrd_stream_handler)
            with patch('select.poll', MagicMock(return_value=MockPollerStopEvent(modules_mgmt_task_stopping_event
                                                                                 , modules_mgmt_thrd, False))):
                #with caplog.at_level(logging.DEBUG):
                #with pytest.raises(AttributeError):
                # mdf_logger = logging.getLogger('sonic_platform.modules_mgmt')
                # with mock.patch.object(mdf_logger, 'debug') as mock_debug:
                assert modules_mgmt_thrd.sfp_port_dict_initial == {}
                assert modules_mgmt_thrd.is_supported_indep_mods_system == False
                print('starting')
                mock_open.side_effect = self.mock_open_new_side_effect_feature_disabled
                #modules_mgmt_thrd.start()
                modules_mgmt_thrd.run()
                print('finishing')
                #modules_mgmt_thrd.join()
                sys.stdout.flush()
        finally:
            pass


    @mock.patch('sonic_platform.device_data.DeviceDataManager.get_sfp_count', MagicMock(return_value=3))
    @patch('os.path.isfile', MagicMock(side_effect=mock_is_file_indep_mode_enabled))
    @patch('builtins.open', spec=open)
    def test_mdf_all_ports_feature_enabled(self, mock_open):
        chassis = Chassis()
        chassis.modules_mgmt_thread.is_alive = MagicMock(return_value=True)
        mock_file_content = self._mock_sysfs_file_content()

        def mock_read_int_from_file(file_path, **kwargs):
            return mock_file_content[file_path]

        def mock_write_file(file_path, content, **kwargs):
            mock_file_content[file_path] = content

        utils.read_str_from_file = mock_read_str_from_file
        utils.write_file = mock_write_file

        num_of_tested_ports = DeviceDataManager.get_sfp_count()
        assert num_of_tested_ports == 3

        device_info.get_paths_to_platform_and_hwsku_dirs = mock.MagicMock(return_value=('', '/usr/share/sonic/platform/ACS-MSN4700'))
        modules_mgmt_task_stopping_event = threading.Event()
        modules_changes_queue = queue.Queue()
        modules_mgmt_thrd = ModulesMgmtTask(main_thread_stop_event=modules_mgmt_task_stopping_event,
                                            q=modules_changes_queue)
        assert modules_mgmt_thrd.sfp_port_dict_initial == {}
        mock_open.side_effect = self.mock_open_new_side_effect_feature_enabled

        with patch('select.poll', MagicMock(return_value=MockPollerStopEvent(modules_mgmt_task_stopping_event
                , modules_mgmt_thrd))):
            with patch('sonic_platform.sfp.SFP', MagicMock(return_value=MockSFPxcvrapi())):
                modules_mgmt_thrd.check_power_cap = check_power_cap
                modules_mgmt_thrd.run()
                #modules_mgmt_thrd.start()
                #modules_mgmt_thrd.join()

    @patch('os.path.isfile', MagicMock(side_effect=mock_is_file_indep_mode_enabled))
    @patch('builtins.open', spec=open)
    #@patch('builtins.open', new=mock_open)
    @patch('sonic_platform.sfp.SFP', MagicMock(return_value=MockSFPxcvrapi()))
    def test_modules_mgmt_poller_events_3_ports(self, mock_open):
        mock_file_content = self._mock_sysfs_file_content()

        def mock_read_int_from_file(file_path, **kwargs):
            return mock_file_content[file_path]

        def mock_write_file(file_path, content, **kwargs):
            mock_file_content[file_path] = content

        utils.read_str_from_file = mock_read_str_from_file
        utils.write_file = mock_write_file
        mock_open.side_effect = self.mock_open_new_side_effect_feature_enabled


        # utils.read_int_from_file = self.mock_read_int_from_file
        # utils.write_file = self.mock_write_file

        device_info.get_paths_to_platform_and_hwsku_dirs = mock.MagicMock(return_value=('', '/usr/share/sonic/platform/ACS-MSN4700'))
        #with patch("builtins.open", MagicMock(return_value=self.mock_open_new)) as mock_file:
        DeviceDataManager.get_sfp_count = mock.MagicMock(return_value=3)
        num_of_tested_ports = DeviceDataManager.get_sfp_count()
        assert num_of_tested_ports == 3


        modules_mgmt_task_stopping_event = threading.Event()
        modules_changes_queue = queue.Queue()
        modules_mgmt_thrd = ModulesMgmtTask(main_thread_stop_event=modules_mgmt_task_stopping_event, q=modules_changes_queue)
        with patch('select.poll', MagicMock(return_value=MockPoller(modules_mgmt_task_stopping_event))):
            modules_mgmt_thrd.check_power_cap = check_power_cap
            modules_mgmt_thrd.run()

    @patch('os.path.isfile', MagicMock(side_effect=mock_is_file_indep_mode_enabled))
    @patch('builtins.open', spec=open)
    @patch('sonic_platform.sfp.SFP', MagicMock(return_value=MockSFPxcvrapi()))
    def test_modules_mgmt_poller_events_single_port(self, mock_open):
        mock_file_content = self._mock_sysfs_file_content()

        def mock_read_int_from_file(file_path, **kwargs):
            return mock_file_content[file_path]

        def mock_write_file(file_path, content, **kwargs):
            mock_file_content[file_path] = content

        utils.read_str_from_file = mock_read_str_from_file
        utils.write_file = mock_write_file
        mock_open.side_effect = self.mock_open_new_side_effect_poller_test
        #mock_open.return_value = MagicMock(return_value=MockOpenNew(filename, 0))



        device_info.get_paths_to_platform_and_hwsku_dirs = mock.MagicMock(return_value=('', '/usr/share/sonic/platform/ACS-MSN4700'))
        DeviceDataManager.get_sfp_count = mock.MagicMock(return_value=1)
        num_of_tested_ports = DeviceDataManager.get_sfp_count()
        assert num_of_tested_ports == 1

        modules_mgmt_task_stopping_event = threading.Event()
        modules_changes_queue = queue.Queue()
        modules_mgmt_thrd = ModulesMgmtTask(main_thread_stop_event=modules_mgmt_task_stopping_event, q=modules_changes_queue)
        with patch('select.poll', MagicMock(return_value=MockPoller(modules_mgmt_task_stopping_event))):
            with patch('builtins.open', MagicMock(side_effect=self.mock_open_new_side_effect_poller_test)):
                modules_mgmt_thrd.check_power_cap = check_power_cap
                modules_mgmt_thrd.run()
