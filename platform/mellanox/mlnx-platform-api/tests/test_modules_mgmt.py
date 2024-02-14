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

import os
import queue
import sys
import threading
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

from sonic_platform.device_data import DeviceDataManager
from sonic_py_common import device_info
from sonic_platform import modules_mgmt
from sonic_platform.modules_mgmt import ModulesMgmtTask
from sonic_platform_base.sonic_xcvr.api.public.cmis import CmisApi
from sonic_platform_base.sonic_xcvr.xcvr_eeprom import XcvrEeprom
from sonic_platform_base.sonic_xcvr.codes.public.cmis import CmisCodes
from sonic_platform_base.sonic_xcvr.mem_maps.public.cmis import CmisMemMap
from sonic_platform_base.sonic_xcvr.fields import consts


TESTED = False

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
        modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("0"): "1",
        modules_mgmt.SYSFS_INDEPENDENT_FD_FW_CONTROL.format("0"): "1",
        modules_mgmt.SYSFS_INDEPENDENT_FD_FW_CONTROL.format("1"): "1",
        modules_mgmt.SYSFS_INDEPENDENT_FD_FW_CONTROL.format("2"): "1",
        modules_mgmt.SYSFS_LEGACY_FD_PRESENCE: "1",
        modules_mgmt.PROC_CMDLINE: ""
    }


mock_file_content = _mock_sysfs_file_content()


class MockPoller:

    def __init__(self, modules_mgmt_task_stopping_event, modules_mgmt_thrd=None, num_of_ports=3, port_plug_out=False
                 , feature_enabled=True, warm_reboot=False, port_plug_in=False, check_ports=True):
        self.fds_dict = {}
        self.poller_count = 0
        self.modules_mgmt_task_stopping_event = modules_mgmt_task_stopping_event
        self.modules_mgmt_thrd = modules_mgmt_thrd
        self.num_of_ports = num_of_ports
        self.port_plug_out = port_plug_out
        self.port_plug_in = port_plug_in
        self.feature_enabled = feature_enabled
        self.warm_reboot = warm_reboot
        self.check_ports = check_ports

    def register(self, fd, attrs):
        self.fds_dict[fd.fileno()] = fd
        assert fd.fileno() in self.fds_dict

    def unregister(self, fd):
        if fd.fileno() in self.fds_dict.keys():
            del self.fds_dict[fd.fileno()]
        assert fd.fileno() not in self.fds_dict.keys()

    def poll(self, timeout=1000):
        global TESTED
        # when simulating port plug out or plug in need to change both presence and power_good sysfs
        self.poller_count += 1
        if self.check_ports:
            if 1 == self.poller_count:
                if self.port_plug_out:
                    # return first fd registered with some made up event number 870
                    fd_to_return = list(self.fds_dict.keys())[0]
                    fd = self.fds_dict[fd_to_return]
                    fd.set_file_int_content(0)
                    event_to_return = 870
                    return [(fd_to_return, event_to_return)]
            elif 2 == self.poller_count:
                if self.port_plug_in:
                    # return first fd registered with some made up event number 870
                    fd_to_return = list(self.fds_dict.keys())[0]
                    fd = self.fds_dict[fd_to_return]
                    fd.set_file_int_content(1)
                    event_to_return = 871
                    return [(fd_to_return, event_to_return)]
            elif 7 == self.poller_count:
                ports_to_test = self.num_of_ports if (not self.port_plug_out or not self.feature_enabled or self.warm_reboot)\
                    else self.num_of_ports * 2
                for i in range(ports_to_test):
                    # when feature is enabled, power_good sysfs is also registered for cmis non-flat memory cables
                    port_to_test = i if not self.feature_enabled else int(i / 2)
                    assert self.modules_mgmt_thrd.sfp_port_dict_initial[port_to_test].port_num == port_to_test
                    assert self.modules_mgmt_thrd.sfp_port_dict_initial[
                               port_to_test].initial_state == modules_mgmt.STATE_HW_NOT_PRESENT
                    if self.feature_enabled:
                        module_obj = self.modules_mgmt_thrd.fds_mapping_to_obj[list(self.fds_dict.keys())[i]][
                            'module_obj']
                        assert module_obj.port_num == port_to_test
                        if not self.warm_reboot:
                            if not self.port_plug_out:
                                assert module_obj.final_state == modules_mgmt.STATE_SW_CONTROL
                            else:
                                assert module_obj.final_state == modules_mgmt.STATE_HW_NOT_PRESENT
                        else:
                            if not self.port_plug_out:
                                assert module_obj.final_state == modules_mgmt.STATE_HW_PRESENT
                            elif self.port_plug_out and self.port_plug_in:
                                assert module_obj.final_state == modules_mgmt.STATE_FW_CONTROL
                            else:
                                assert module_obj.final_state == modules_mgmt.STATE_HW_NOT_PRESENT
                        TESTED = True
            if 10 == self.poller_count:
                assert len(self.modules_mgmt_thrd.sfp_port_dict_initial) == self.num_of_ports
                assert self.modules_mgmt_thrd.is_supported_indep_mods_system == self.feature_enabled
                self.modules_mgmt_task_stopping_event.set()
        return []


class MockOpenNew:

    def __init__(self, name='', file_no=190, indep_mode=True):
        self.name = name
        self.file_no = file_no
        self.indep_mode = indep_mode
        self.retint = None
        self.seek_cursor = False
        self.curr = 0

    def read(self):
        if self.fileno() in [99]:
            return "S"
        else:
            if self.retint is not None:
                return str(self.retint)
            else:
                return mock_file_content[self.name]

    def readline(self):
        if self.fileno() in [99]:
            if self.indep_mode:
                return "SAI_INDEPENDENT_MODULE_MODE=1"
            else:
                return ""
        else:
            return _mock_sysfs_file_content()[self.name]

    def fileno(self):
        return self.file_no

    def seek(self, seek_val):
        self.curr = seek_val

    def close(self):
        pass

    def write(self, write_val):
        self.set_file_int_content(write_val)

    def set_file_int_content(self, retint):
        self.retint = str(retint)
        mock_file_content[self.name] = str(retint)

    def __enter__(self):
        return self

    def __exit__(self, filename, *args, **kwargs):
        pass


class MockPollerStopEvent:

    def __init__(self, modules_mgmt_task_stopping_event, modules_mgmt_thrd=None, num_of_ports=3, feature_enabled=True
                 , check_ports=True, ports_connected=True, ports_error=False, fw_controlled_ports=False):
        self.fds_dict = {}
        self.modules_mgmt_task_stopping_event = modules_mgmt_task_stopping_event
        self.modules_mgmt_thrd = modules_mgmt_thrd
        self.num_of_ports = num_of_ports
        self.feature_enabled = feature_enabled
        self.check_ports = check_ports
        self.ports_connected = ports_connected
        self.ports_error = ports_error
        self.fw_controlled_ports = fw_controlled_ports
        self.tested = False

    def register(self, fd, attrs):
        self.fds_dict[fd.fileno()] = 1 & attrs
        assert fd.fileno() in self.fds_dict

    def poll(self, timeout=1000):
        assert len(self.modules_mgmt_thrd.sfp_port_dict_initial) == self.num_of_ports
        assert self.modules_mgmt_thrd.is_supported_indep_mods_system == self.feature_enabled
        if self.check_ports:
            ports_to_test = self.num_of_ports if (not self.feature_enabled or not self.ports_connected or self.ports_error
                                                  or self.fw_controlled_ports) else self.num_of_ports * 2
            for i in range(ports_to_test):
                # when feature is enabled, power_good sysfs is also registered for cmis non-flat memory cables
                port_to_test = i if (not self.feature_enabled or not self.ports_connected or self.ports_error
                                     or self.fw_controlled_ports) else int(i / 2)
                assert self.modules_mgmt_thrd.sfp_port_dict_initial[port_to_test].port_num == port_to_test
                assert self.modules_mgmt_thrd.sfp_port_dict_initial[port_to_test].initial_state == modules_mgmt.STATE_HW_NOT_PRESENT
                module_obj = self.modules_mgmt_thrd.fds_mapping_to_obj[list(self.fds_dict.keys())[i]]['module_obj']
                assert module_obj.port_num == port_to_test
                if self.ports_error:
                    assert module_obj.final_state == modules_mgmt.STATE_ERROR_HANDLER
                else:
                    if self.ports_connected:
                        if self.feature_enabled:
                            if self.fw_controlled_ports:
                                assert module_obj.final_state == modules_mgmt.STATE_FW_CONTROL
                            else:
                                assert module_obj.final_state == modules_mgmt.STATE_SW_CONTROL
                        else:
                            assert module_obj.final_state == modules_mgmt.STATE_HW_PRESENT
                    else:
                        assert module_obj.final_state == modules_mgmt.STATE_HW_NOT_PRESENT
        self.modules_mgmt_task_stopping_event.set()
        global TESTED
        TESTED = True
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
        '//usr/share/sonic/platform/ACS-MSN4700/sai.profile' : True
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
        modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("0"): True,
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


def mock_read_int_from_file(filename, *args):
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
        if consts.FLAT_MEM_FIELD == field:
            return 0 if self.is_flat_memory else 1
        else:
            return 0


class MockXcvrapi:
    def __init__(self, is_cmis_api=True, is_flat_memory_bool=False):
        self.is_cmis_api = is_cmis_api
        self.is_flat_memory_bool = is_flat_memory_bool
        self.xcvr_eeprom = MagicMock(autospec=XcvrEeprom, return_value=MockXcvrEeprom(is_flat_memory_bool, CmisMemMap(CmisCodes)))

    def is_flat_memory(self):
        return self.is_flat_memory_bool

    def xcvr_eeprom(self):
        return self.xcvr_eeprom


class MockSFPxcvrapi:
    def __init__(self, xcvr_api_is_cmis_api=True, xcvr_eeprom_is_flat_memory=False):
        self.xcvr_api = Mock(spec=CmisApi(MockXcvrEeprom(False, CmisMemMap(CmisCodes))), return_value=MockXcvrapi(xcvr_api_is_cmis_api, xcvr_eeprom_is_flat_memory))
        self.xcvr_api_is_cmis_api = xcvr_api_is_cmis_api
        self.xcvr_eeprom_is_flat_memory = xcvr_eeprom_is_flat_memory
        self.xcvr_api.is_flat_memory = types.MethodType(self.is_flat_memory, self)

    def get_xcvr_api(self):
        return self.xcvr_api

    def is_flat_memory(self, ref):
        return self.xcvr_eeprom_is_flat_memory


def check_power_cap(port, module_sm_obj):
    pass


class TestModulesMgmt(unittest.TestCase):
    """Test class to test modules_mgmt.py. The test cases covers:
        1. cables detection for 1 to 3 32 ports - feature disabled / enabled / poller
        2. cable disconnection - plug out
        3. cable reconnection - plug in
        4. warm reboot normal flow with FW ports
        5. warm reboot flow with FW ports plugged out
        6. warm reboot flow with FW ports plugged out and then plugged in (stays FW controlled, no SFP mock change)
        7. test 32 FW controlled (non cmis flat mem) cables powered off
        8. test 32 SW controlled (cmis active non flat mem) cables powered off
    """

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

    def mock_open_builtin(self, file_name, feature_enabled=True):
        return_dict = {
            (modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("0"), 'r') : MockOpenNew(modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("0"), 100),
            (modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("1"), 'r') : MockOpenNew(modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("1"), 101),
            (modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("2"), 'r') : MockOpenNew(modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("2"), 102),
            '//usr/share/sonic/platform/ACS-MSN4700/sai.profile' : MockOpenNew('//usr/share/sonic/platform/ACS-MSN4700/sai.profile', 99, feature_enabled),
            modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("0") : MockOpenNew(name=modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("0"), file_no=100),
            modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("1") : MockOpenNew(modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("1"), 101),
            modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("2") : MockOpenNew(modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("2"), 102),
            modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format("0"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format("0"), 0),
            modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format("1"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format("1"), 1),
            modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format("2"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format("2"), 2),
            modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format("0"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format("0"), 200),
            modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format("1"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format("1"), 201),
            modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format("2"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format("2"), 202),
            modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format("0"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format("0"), 300),
            modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format("1"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format("1"), 301),
            modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format("2"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format("2"), 302),
            modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_LIMIT.format("0"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_LIMIT.format("0"), 500),
            modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_LIMIT.format("1"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_LIMIT.format("1"), 501),
            modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_LIMIT.format("2"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_LIMIT.format("2"), 502),
            modules_mgmt.SYSFS_INDEPENDENT_FD_FREQ_SUPPORT.format("0"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_FREQ_SUPPORT.format("0"), 602),
            modules_mgmt.SYSFS_INDEPENDENT_FD_FREQ_SUPPORT.format("1"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_FREQ_SUPPORT.format("1"), 602),
            modules_mgmt.SYSFS_INDEPENDENT_FD_FREQ_SUPPORT.format("2"): MockOpenNew(modules_mgmt.SYSFS_INDEPENDENT_FD_FREQ_SUPPORT.format("2"), 602),
            modules_mgmt.PROC_CMDLINE: MockOpenNew(modules_mgmt.PROC_CMDLINE, 200)
        }
        return return_dict[file_name]

    def mock_open_new_side_effect_feature_disabled(self, filename, *args, **kwargs):
        mock_context = MagicMock()
        mock_context.__enter__.return_value = self.mock_open_builtin(filename, False)
        mock_context.__exit__.return_value = False
        return mock_context

    def mock_open_new_side_effect_feature_enabled(self, filename, *args, **kwargs):
        mock_context = MagicMock()
        mock_context.__enter__.return_value = self.mock_open_builtin(filename)
        mock_context.__exit__.return_value = False
        return mock_context

    def mock_open_new_side_effect_poller_test(self, filename, *args, **kwargs):
        if filename in ['//usr/share/sonic/platform/ACS-MSN4700/sai.profile']:
            mock_context = MagicMock()
            mock_context.__enter__.return_value = MockOpenNew(filename, 99)
            mock_context.__exit__.return_value = False
            return mock_context
        else:
            mock_context = MagicMock()
            mock_open_new = MockOpenNew(filename, self.fd_number_by_fd_name_dict[filename])
            mock_context.return_value = mock_open_new
            mock_context.__enter__.return_value = mock_open_new
            mock_context.__exit__.return_value = False
            if 'hw_present' in filename or 'power_on' in filename or 'freq' in filename or 'control' in filename:
                return mock_context
            else:
                return mock_context.return_value

    def mock_open_new_side_effect_warm_reboot(self, filename, *args, **kwargs):
        if filename in ['//usr/share/sonic/platform/ACS-MSN4700/sai.profile']:
            mock_context = MagicMock()
            mock_context.__enter__.return_value = MockOpenNew(filename, 99)
            mock_context.__exit__.return_value = False
            return mock_context
        else:
            mock_open_new = MockOpenNew(filename, self.fd_number_by_fd_name_dict[filename])
            return mock_open_new


    #@classmethod
    def setup_class(cls):
        os.environ["MLNX_PLATFORM_API_UNIT_TESTING"] = "1"
        cls.fd_number_by_fd_name_dict = {
                modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("0") : 100,
                modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("1") : 101,
                modules_mgmt.SYSFS_LEGACY_FD_PRESENCE.format("2") : 102,
                '//usr/share/sonic/platform/ACS-MSN4700/sai.profile' : 99,
                modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format("0") : 0,
                modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format("1") : 1,
                modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format("2") : 2,
                modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format("0") : 200,
                modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format("1") : 201,
                modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format("2") : 202,
                modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format("0") : 300,
                modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format("1") : 301,
                modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format("2") : 302,
                modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_LIMIT.format("0") : 500,
                modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_LIMIT.format("1") : 501,
                modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_LIMIT.format("2") : 502,
                modules_mgmt.SYSFS_INDEPENDENT_FD_FREQ_SUPPORT.format("0") : 600,
                modules_mgmt.SYSFS_INDEPENDENT_FD_FREQ_SUPPORT.format("1") : 601,
                modules_mgmt.SYSFS_INDEPENDENT_FD_FREQ_SUPPORT.format("2") : 602,
                modules_mgmt.SYSFS_INDEPENDENT_FD_FW_CONTROL.format("0") : 700,
                modules_mgmt.SYSFS_INDEPENDENT_FD_FW_CONTROL.format("1") : 701,
                modules_mgmt.SYSFS_INDEPENDENT_FD_FW_CONTROL.format("2") : 702,
                modules_mgmt.PROC_CMDLINE : 200
        }
        # mock the directory holding relevant sai.profile
        device_info.get_paths_to_platform_and_hwsku_dirs = mock.MagicMock(return_value=('', '/usr/share/sonic/platform/ACS-MSN4700'))


    @patch('sonic_platform.device_data.DeviceDataManager.get_sfp_count', MagicMock(return_value=3))
    @patch('os.path.isfile', MagicMock(side_effect=mock_is_file_indep_mode_disabled))
    @patch('sonic_platform.utils.read_int_from_file', MagicMock(side_effect=mock_read_int_from_file))
    @patch('builtins.open', spec=open)
    def test_mdf_all_ports_feature_disabled(self, mock_open):
        mock_open.side_effect = self.mock_open_new_side_effect_feature_disabled
        global TESTED
        TESTED = False
        num_of_tested_ports = DeviceDataManager.get_sfp_count()
        assert num_of_tested_ports == 3

        # start modules_mgmt thread and the test in poller part
        modules_mgmt_task_stopping_event = threading.Event()
        modules_changes_queue = queue.Queue()
        modules_mgmt_thrd = ModulesMgmtTask(main_thread_stop_event=modules_mgmt_task_stopping_event,
                                            q=modules_changes_queue)
        with patch('select.poll', MagicMock(return_value=MockPollerStopEvent(modules_mgmt_task_stopping_event
                                                                    , modules_mgmt_thrd, feature_enabled=False))):
            assert modules_mgmt_thrd.sfp_port_dict_initial == {}
            assert modules_mgmt_thrd.is_supported_indep_mods_system == False
            modules_mgmt_thrd.run()
        # a check that modules mgmt thread ran and got into the poller part
        assert TESTED

    @patch('sonic_platform.device_data.DeviceDataManager.get_sfp_count', MagicMock(return_value=3))
    @patch('os.path.isfile', MagicMock(side_effect=mock_is_file_indep_mode_enabled))
    @patch('builtins.open', spec=open)
    def test_mdf_all_ports_feature_enabled(self, mock_open):
        mock_open.side_effect = self.mock_open_new_side_effect_feature_enabled
        global TESTED
        TESTED = False
        num_of_tested_ports = DeviceDataManager.get_sfp_count()
        assert num_of_tested_ports == 3

        # start modules_mgmt thread and the test in poller part
        modules_mgmt_task_stopping_event = threading.Event()
        modules_changes_queue = queue.Queue()
        modules_mgmt_thrd = ModulesMgmtTask(main_thread_stop_event=modules_mgmt_task_stopping_event,
                                            q=modules_changes_queue)
        assert modules_mgmt_thrd.sfp_port_dict_initial == {}
        with patch('select.poll', MagicMock(return_value=MockPollerStopEvent(modules_mgmt_task_stopping_event
                , modules_mgmt_thrd))):
            with patch('sonic_platform.sfp.SFP', MagicMock(return_value=MockSFPxcvrapi())):
                modules_mgmt_thrd.check_power_cap = check_power_cap
                modules_mgmt_thrd.run()
        # a check that modules mgmt thread ran and got into the poller part
        assert TESTED

    @patch('os.path.isfile', MagicMock(side_effect=mock_is_file_indep_mode_enabled))
    @patch('builtins.open', spec=open)
    @patch('sonic_platform.sfp.SFP', MagicMock(return_value=MockSFPxcvrapi()))
    def test_modules_mgmt_poller_events_3_ports(self, mock_open):
        mock_open.side_effect = self.mock_open_new_side_effect_poller_test
        mock_file_content[modules_mgmt.PROC_CMDLINE] = ''
        global TESTED
        TESTED = False
        DeviceDataManager.get_sfp_count = mock.MagicMock(return_value=3)
        num_of_tested_ports = DeviceDataManager.get_sfp_count()
        assert num_of_tested_ports == 3

        # start modules_mgmt thread and the test in poller part
        modules_mgmt_task_stopping_event = threading.Event()
        modules_changes_queue = queue.Queue()
        modules_mgmt_thrd = ModulesMgmtTask(main_thread_stop_event=modules_mgmt_task_stopping_event
                                            , q=modules_changes_queue)
        with patch('select.poll', MagicMock(return_value=MockPoller(modules_mgmt_task_stopping_event, modules_mgmt_thrd))):
            modules_mgmt_thrd.check_power_cap = check_power_cap
            modules_mgmt_thrd.run()
        # a check that modules mgmt thread ran and got into the poller part
        assert TESTED

    @patch('os.path.isfile', MagicMock(side_effect=mock_is_file_indep_mode_enabled))
    @patch('builtins.open', spec=open)
    @patch('sonic_platform.sfp.SFP', MagicMock(return_value=MockSFPxcvrapi()))
    def test_modules_mgmt_poller_events_single_port(self, mock_open):
        mock_open.side_effect = self.mock_open_new_side_effect_poller_test
        global TESTED
        TESTED = False
        DeviceDataManager.get_sfp_count = mock.MagicMock(return_value=1)
        num_of_tested_ports = DeviceDataManager.get_sfp_count()
        assert num_of_tested_ports == 1

        # start modules_mgmt thread and the test in poller part
        modules_mgmt_task_stopping_event = threading.Event()
        modules_changes_queue = queue.Queue()
        modules_mgmt_thrd = ModulesMgmtTask(main_thread_stop_event=modules_mgmt_task_stopping_event
                                            , q=modules_changes_queue)
        with patch('select.poll', MagicMock(return_value=MockPoller(modules_mgmt_task_stopping_event
                , modules_mgmt_thrd, num_of_tested_ports))):
            with patch('builtins.open', MagicMock(side_effect=self.mock_open_new_side_effect_poller_test)):
                modules_mgmt_thrd.check_power_cap = check_power_cap
                modules_mgmt_thrd.run()
        # a check that modules mgmt thread ran and got into the poller part
        assert TESTED

    @patch('os.path.isfile', MagicMock(side_effect=mock_is_file_indep_mode_enabled))
    @patch('builtins.open', spec=open)
    @patch('sonic_platform.sfp.SFP', MagicMock(return_value=MockSFPxcvrapi(False, True)))
    def test_modules_mgmt_normal_warm_reboot(self, mock_open):
        mock_open.side_effect = self.mock_open_new_side_effect_warm_reboot
        # mock /proc/cmdline with warm reboot boot type key value
        mock_file_content[modules_mgmt.PROC_CMDLINE] = f'{modules_mgmt.CMDLINE_STR_TO_LOOK_FOR}{modules_mgmt.CMDLINE_VAL_TO_LOOK_FOR}'
        global TESTED
        TESTED = False
        DeviceDataManager.get_sfp_count = mock.MagicMock(return_value=1)
        num_of_tested_ports = DeviceDataManager.get_sfp_count()
        assert num_of_tested_ports == 1
        # set the port to start with FW controlled before warm reboot takes place
        mock_file_content[modules_mgmt.SYSFS_INDEPENDENT_FD_FW_CONTROL.format("0")] = "0"

        # start modules_mgmt thread and the test in poller part
        modules_mgmt_task_stopping_event = threading.Event()
        modules_changes_queue = queue.Queue()
        modules_mgmt_thrd = ModulesMgmtTask(main_thread_stop_event=modules_mgmt_task_stopping_event, q=modules_changes_queue)
        with patch('select.poll', MagicMock(return_value=MockPoller(modules_mgmt_task_stopping_event, modules_mgmt_thrd
                , num_of_tested_ports, warm_reboot=True))):
            modules_mgmt_thrd.check_power_cap = check_power_cap
            modules_mgmt_thrd.run()
        # a check that modules mgmt thread ran and got into the poller part
        assert TESTED

    @patch('os.path.isfile', MagicMock(side_effect=mock_is_file_indep_mode_enabled))
    @patch('builtins.open', spec=open)
    @patch('sonic_platform.sfp.SFP', MagicMock(return_value=MockSFPxcvrapi(False, True)))
    def test_modules_mgmt_plug_out_fw_cable_after_warm_reboot(self, mock_open):
        mock_open.side_effect = self.mock_open_new_side_effect_warm_reboot
        # mock /proc/cmdline with warm reboot boot type key value
        mock_file_content[modules_mgmt.PROC_CMDLINE] = f'{modules_mgmt.CMDLINE_STR_TO_LOOK_FOR}{modules_mgmt.CMDLINE_VAL_TO_LOOK_FOR}'
        global TESTED
        TESTED = False
        DeviceDataManager.get_sfp_count = mock.MagicMock(return_value=1)
        num_of_tested_ports = DeviceDataManager.get_sfp_count()
        assert num_of_tested_ports == 1

        # set the port to start with FW controlled before warm reboot takes place
        mock_file_content[modules_mgmt.SYSFS_INDEPENDENT_FD_FW_CONTROL.format("0")] = "0"

        # start modules_mgmt thread and the test in poller part
        modules_mgmt_task_stopping_event = threading.Event()
        modules_changes_queue = queue.Queue()
        modules_mgmt_thrd = ModulesMgmtTask(main_thread_stop_event=modules_mgmt_task_stopping_event
                                            , q=modules_changes_queue)
        with patch('select.poll', MagicMock(return_value=MockPoller(modules_mgmt_task_stopping_event
                , modules_mgmt_thrd, num_of_tested_ports, port_plug_out=True, warm_reboot=True))):
            modules_mgmt_thrd.check_power_cap = check_power_cap
            modules_mgmt_thrd.run()
        # a check that modules mgmt thread ran and got into the poller part
        assert TESTED

    @patch('os.path.isfile', MagicMock(side_effect=mock_is_file_indep_mode_enabled))
    @patch('builtins.open', spec=open)
    @patch('sonic_platform.sfp.SFP', MagicMock(return_value=MockSFPxcvrapi(False, True)))
    def test_modules_mgmt_plug_out_plug_in_fw_cable_after_warm_reboot(self, mock_open):
        mock_open.side_effect = self.mock_open_new_side_effect_warm_reboot
        # mock /proc/cmdline with warm reboot boot type key value
        mock_file_content[modules_mgmt.PROC_CMDLINE] = f'{modules_mgmt.CMDLINE_STR_TO_LOOK_FOR}{modules_mgmt.CMDLINE_VAL_TO_LOOK_FOR}'
        global TESTED
        TESTED = False
        DeviceDataManager.get_sfp_count = mock.MagicMock(return_value=1)
        num_of_tested_ports = DeviceDataManager.get_sfp_count()
        assert num_of_tested_ports == 1

        mock_file_content[modules_mgmt.SYSFS_INDEPENDENT_FD_FW_CONTROL.format("0")] = "0"

        # start modules_mgmt thread and the test in poller part
        modules_mgmt_task_stopping_event = threading.Event()
        modules_changes_queue = queue.Queue()
        modules_mgmt_thrd = ModulesMgmtTask(main_thread_stop_event=modules_mgmt_task_stopping_event
                                            , q=modules_changes_queue)
        with patch('select.poll', MagicMock(return_value=MockPoller(modules_mgmt_task_stopping_event
                , modules_mgmt_thrd, num_of_tested_ports, port_plug_out=True, warm_reboot=True, port_plug_in=True))):
            modules_mgmt_thrd.check_power_cap = check_power_cap
            modules_mgmt_thrd.run()
        # a check that modules mgmt thread ran and got into the poller part
        assert TESTED

    @patch('os.path.isfile', MagicMock(side_effect=mock_is_file_indep_mode_enabled))
    @patch('builtins.open', spec=open)
    @patch('sonic_platform.sfp.SFP', MagicMock(return_value=MockSFPxcvrapi(False, True)))
    def test_modules_mgmt_no_ports(self, mock_open):
        mock_open.side_effect = self.mock_open_new_side_effect_poller_test
        global TESTED
        TESTED = False
        DeviceDataManager.get_sfp_count = mock.MagicMock(return_value=0)
        num_of_tested_ports = DeviceDataManager.get_sfp_count()
        assert num_of_tested_ports == 0

        # start modules_mgmt thread and the test in poller part
        modules_mgmt_task_stopping_event = threading.Event()
        modules_changes_queue = queue.Queue()
        modules_mgmt_thrd = ModulesMgmtTask(main_thread_stop_event=modules_mgmt_task_stopping_event
                                            , q=modules_changes_queue)
        with patch('select.poll', MagicMock(return_value=MockPollerStopEvent(modules_mgmt_task_stopping_event
                , modules_mgmt_thrd, num_of_tested_ports, check_ports=False))):
            modules_mgmt_thrd.check_power_cap = check_power_cap
            modules_mgmt_thrd.run()
        # a check that modules mgmt thread ran and got into the poller part
        assert TESTED

    @patch('os.path.isfile', MagicMock(side_effect=mock_is_file_indep_mode_enabled))
    @patch('builtins.open', spec=open)
    @patch('sonic_platform.sfp.SFP', MagicMock(return_value=MockSFPxcvrapi(False, True)))
    def test_modules_mgmt_ports_disconnected(self, mock_open):
        mock_open.side_effect = self.mock_open_new_side_effect_poller_test
        global TESTED
        TESTED = False
        num_of_ports = 3
        DeviceDataManager.get_sfp_count = mock.MagicMock(return_value=num_of_ports)
        num_of_tested_ports = DeviceDataManager.get_sfp_count()
        assert num_of_tested_ports == num_of_ports

        # update hw_present sysfs with value of 0 for each port
        for i in range(num_of_tested_ports):
            modules_sysfs = modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format(f"{i}")
            mock_file_content[modules_sysfs] = "0"

        # start modules_mgmt thread and the test in poller part
        modules_mgmt_task_stopping_event = threading.Event()
        modules_changes_queue = queue.Queue()
        modules_mgmt_thrd = ModulesMgmtTask(main_thread_stop_event=modules_mgmt_task_stopping_event
                                            , q=modules_changes_queue)
        with patch('select.poll', MagicMock(return_value=MockPollerStopEvent(modules_mgmt_task_stopping_event
                , modules_mgmt_thrd, num_of_tested_ports, ports_connected=False))):
            modules_mgmt_thrd.check_power_cap = check_power_cap
            modules_mgmt_thrd.run()
        # a check that modules mgmt thread ran and got into the poller part
        assert TESTED

    @patch('os.path.isfile', MagicMock(side_effect=mock_is_file_indep_mode_enabled))
    @patch('builtins.open', spec=open)
    @patch('sonic_platform.sfp.SFP', MagicMock(return_value=MockSFPxcvrapi(False, True)))
    def test_modules_mgmt_bad_flows_port_disconnected(self, mock_open):
        mock_open.side_effect = self.mock_open_new_side_effect_poller_test
        global TESTED
        TESTED = False
        num_of_ports = 1
        DeviceDataManager.get_sfp_count = mock.MagicMock(return_value=num_of_ports)
        num_of_tested_ports = DeviceDataManager.get_sfp_count()
        assert num_of_tested_ports == num_of_ports

        # update hw_present sysfs with value of 0 for each port
        for i in range(num_of_tested_ports):
            modules_sysfs = modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format(f"{i}")
            mock_file_content[modules_sysfs] = "0"

        # start modules_mgmt thread and the test in poller part
        modules_mgmt_task_stopping_event = threading.Event()
        modules_changes_queue = queue.Queue()
        modules_mgmt_thrd = ModulesMgmtTask(main_thread_stop_event=modules_mgmt_task_stopping_event
                                            , q=modules_changes_queue)
        with patch('select.poll', MagicMock(return_value=MockPollerStopEvent(modules_mgmt_task_stopping_event
                , modules_mgmt_thrd, num_of_tested_ports, ports_connected=False))):
            modules_mgmt_thrd.check_power_cap = check_power_cap
            modules_mgmt_thrd.run()
        # a check that modules mgmt thread ran and got into the poller part
        assert TESTED

    @patch('os.path.isfile', MagicMock(side_effect=mock_is_file_indep_mode_enabled))
    @patch('builtins.open', spec=open)
    @patch('sonic_platform.sfp.SFP', MagicMock(return_value=MockSFPxcvrapi(False, True)))
    def test_modules_mgmt_bad_flows_power_good(self, mock_open):
        mock_open.side_effect = self.mock_open_new_side_effect_poller_test
        global TESTED
        TESTED = False
        num_of_ports = 1
        DeviceDataManager.get_sfp_count = mock.MagicMock(return_value=num_of_ports)
        num_of_tested_ports = DeviceDataManager.get_sfp_count()
        assert num_of_tested_ports == num_of_ports

        # update power_good sysfs with value of 0 for each port
        for i in range(num_of_tested_ports):
            modules_sysfs = modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format(f"{i}")
            mock_file_content[modules_sysfs] = "0"

        # start modules_mgmt thread and the test in poller part
        modules_mgmt_task_stopping_event = threading.Event()
        modules_changes_queue = queue.Queue()
        modules_mgmt_thrd = ModulesMgmtTask(main_thread_stop_event=modules_mgmt_task_stopping_event
                                            , q=modules_changes_queue)
        with patch('select.poll', MagicMock(return_value=MockPollerStopEvent(modules_mgmt_task_stopping_event
                , modules_mgmt_thrd, num_of_tested_ports, ports_connected=False))):
            modules_mgmt_thrd.check_power_cap = check_power_cap
            modules_mgmt_thrd.run()
        for i in range(num_of_tested_ports):
            modules_sysfs = modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format(f"{i}")
            mock_file_content[modules_sysfs] = "1"
        # a check that modules mgmt thread ran and got into the poller part
        assert TESTED

    @patch('os.path.isfile', MagicMock(side_effect=mock_is_file_indep_mode_enabled))
    @patch('builtins.open', spec=open)
    @patch('sonic_platform.sfp.SFP', MagicMock(return_value=MockSFPxcvrapi(False, True)))
    def test_modules_mgmt_bad_flows_ports_powered_off_fw_controlled(self, mock_open):
        mock_open.side_effect = self.mock_open_new_side_effect_poller_test
        global TESTED
        TESTED = False
        num_of_ports = 32
        DeviceDataManager.get_sfp_count = mock.MagicMock(return_value=num_of_ports)
        num_of_tested_ports = DeviceDataManager.get_sfp_count()
        assert num_of_tested_ports == num_of_ports

        # create or update different sysfs and is_file mocking with relevant value for each port
        for i in range(num_of_tested_ports):
            # mock power_on sysfs for all ports
            modules_sysfs = modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format(f"{i}")
            mock_file_content[modules_sysfs] = "0"
            mock_is_file_indep_mode_enabled_content[modules_sysfs] = True
            self.fd_number_by_fd_name_dict[modules_sysfs] = 300 + i
            # mock hw_presence sysfs for all ports
            modules_sysfs = modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format(f'{i}')
            mock_file_content[modules_sysfs] = "1"
            mock_is_file_indep_mode_enabled_content[modules_sysfs] = True
            self.fd_number_by_fd_name_dict[modules_sysfs] = i
            # mock power_good sysfs for all ports
            modules_sysfs = modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format(f'{i}')
            mock_file_content[modules_sysfs] = "1"
            mock_is_file_indep_mode_enabled_content[modules_sysfs] = True
            self.fd_number_by_fd_name_dict[modules_sysfs] = 200 + i
            # mock hw_reset sysfs for all ports
            modules_sysfs = modules_mgmt.SYSFS_INDEPENDENT_FD_HW_RESET.format(f'{i}')
            mock_is_file_indep_mode_enabled_content[modules_sysfs] = True
            self.fd_number_by_fd_name_dict[modules_sysfs] = 400 + i

        # start modules_mgmt thread and the test in poller part
        modules_mgmt_task_stopping_event = threading.Event()
        modules_changes_queue = queue.Queue()
        modules_mgmt_thrd = ModulesMgmtTask(main_thread_stop_event=modules_mgmt_task_stopping_event
                                            , q=modules_changes_queue)
        with patch('select.poll', MagicMock(return_value=MockPollerStopEvent(modules_mgmt_task_stopping_event
                , modules_mgmt_thrd, num_of_tested_ports, fw_controlled_ports=True))):
            modules_mgmt_thrd.check_power_cap = check_power_cap
            modules_mgmt_thrd.run()

        # change power_on sysfs values back to the default ones
        for i in range(num_of_tested_ports):
            modules_sysfs = modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format(f"{i}")
            mock_file_content[modules_sysfs] = "1"
        # a check that modules mgmt thread ran and got into the poller part
        assert TESTED

    @patch('os.path.isfile', MagicMock(side_effect=mock_is_file_indep_mode_enabled))
    @patch('builtins.open', spec=open)
    @patch('sonic_platform.sfp.SFP', MagicMock(return_value=MockSFPxcvrapi()))
    def test_modules_mgmt_bad_flows_ports_powered_off_sw_controlled(self, mock_open):
        mock_open.side_effect = self.mock_open_new_side_effect_poller_test
        global TESTED
        TESTED = False
        num_of_ports = 32
        DeviceDataManager.get_sfp_count = mock.MagicMock(return_value=num_of_ports)
        num_of_tested_ports = DeviceDataManager.get_sfp_count()
        assert num_of_tested_ports == num_of_ports

        # create or update different sysfs and is_file mocking with relevant value for each port
        for i in range(num_of_tested_ports):
            # mock power_on sysfs for all ports
            modules_sysfs = modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format(f"{i}")
            mock_file_content[modules_sysfs] = "0"
            mock_is_file_indep_mode_enabled_content[modules_sysfs] = True
            self.fd_number_by_fd_name_dict[modules_sysfs] = 300 + i
            # mock hw_presence sysfs for all ports
            modules_sysfs = modules_mgmt.SYSFS_INDEPENDENT_FD_PRESENCE.format(f'{i}')
            mock_file_content[modules_sysfs] = "1"
            mock_is_file_indep_mode_enabled_content[modules_sysfs] = True
            self.fd_number_by_fd_name_dict[modules_sysfs] = i
            # mock power_good sysfs for all ports
            modules_sysfs = modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_GOOD.format(f'{i}')
            mock_file_content[modules_sysfs] = "1"
            mock_is_file_indep_mode_enabled_content[modules_sysfs] = True
            self.fd_number_by_fd_name_dict[modules_sysfs] = 200 + i
            # mock hw_reset sysfs for all ports
            modules_sysfs = modules_mgmt.SYSFS_INDEPENDENT_FD_HW_RESET.format(f'{i}')
            mock_is_file_indep_mode_enabled_content[modules_sysfs] = True
            self.fd_number_by_fd_name_dict[modules_sysfs] = 400 + i
            # mock frequency_support sysfs for all ports
            modules_sysfs = modules_mgmt.SYSFS_INDEPENDENT_FD_FREQ_SUPPORT.format(f'{i}')
            mock_file_content[modules_sysfs] = "0"
            mock_is_file_indep_mode_enabled_content[modules_sysfs] = True
            self.fd_number_by_fd_name_dict[modules_sysfs] = 600 + i

        # start modules_mgmt thread and the test in poller part
        modules_mgmt_task_stopping_event = threading.Event()
        modules_changes_queue = queue.Queue()
        modules_mgmt_thrd = ModulesMgmtTask(main_thread_stop_event=modules_mgmt_task_stopping_event
                                            , q=modules_changes_queue)
        with patch('select.poll', MagicMock(return_value=MockPollerStopEvent(modules_mgmt_task_stopping_event
                , modules_mgmt_thrd, num_of_tested_ports))):
            modules_mgmt_thrd.check_power_cap = check_power_cap
            modules_mgmt_thrd.run()

        # change power_on sysfs values back to the default ones
        for i in range(num_of_tested_ports):
            modules_sysfs = modules_mgmt.SYSFS_INDEPENDENT_FD_POWER_ON.format(f"{i}")
            mock_file_content[modules_sysfs] = "1"
        # a check that modules mgmt thread ran and got into the poller part
        assert TESTED

    def teardown_class(cls):
        mock_file_content[modules_mgmt.PROC_CMDLINE] = ''
