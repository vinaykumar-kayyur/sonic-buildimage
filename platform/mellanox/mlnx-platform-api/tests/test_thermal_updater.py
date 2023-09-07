#
# Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES.
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

import time
from unittest import mock

from sonic_platform import utils
from sonic_platform.thermal_updater import Timer, ThermalUpdater
from sonic_platform.thermal_updater import ASIC_DEFAULT_TEMP_WARNNING_THRESHOLD, \
                                           ASIC_DEFAULT_TEMP_CRITICAL_THRESHOLD


mock_tc_config = """
{
    "dev_parameters": {
        "asic": {
            "pwm_min": 20,
            "pwm_max": 100,
            "val_min": "!70000",
            "val_max": "!105000",
            "poll_time": 3
        },
        "module\\\\d+": {
            "pwm_min": 20,
            "pwm_max": 100,
            "val_min": 60000,
            "val_max": 80000,
            "poll_time": 20
        }
    }
}
"""


class TestThermalUpdater:
    def test_timer(self):
        timer = Timer()
        timer.start()
        mock_cb_1000_run_now = mock.MagicMock()
        mock_cb_1000_run_future = mock.MagicMock()
        mock_cb_1_run_future_once = mock.MagicMock()
        mock_cb_1_run_future_repeat = mock.MagicMock()
        timer.schedule(1000, cb=mock_cb_1000_run_now, repeat=False, run_now=True)
        timer.schedule(1000, cb=mock_cb_1000_run_future, repeat=False, run_now=False)
        timer.schedule(1, cb=mock_cb_1_run_future_once, repeat=False, run_now=False)
        timer.schedule(1, cb=mock_cb_1_run_future_repeat, repeat=True, run_now=False)
        time.sleep(3)
        timer.stop()

        mock_cb_1000_run_now.assert_called_once()
        mock_cb_1000_run_future.assert_not_called()
        mock_cb_1_run_future_once.assert_called_once()
        assert mock_cb_1_run_future_repeat.call_count > 1

    def test_load_tc_config_non_exists(self):
        updater = ThermalUpdater(None)
        updater.load_tc_config()
        assert updater._timer._timestamp_queue.qsize() == 2

    def test_load_tc_config_mocked(self):
        updater = ThermalUpdater(None)
        mock_os_open = mock.mock_open(read_data=mock_tc_config)
        with mock.patch('sonic_platform.utils.open', mock_os_open):
            updater.load_tc_config()
        assert updater._timer._timestamp_queue.qsize() == 2

    @mock.patch('sonic_platform.thermal_updater.ThermalUpdater.update_asic', mock.MagicMock())
    @mock.patch('sonic_platform.thermal_updater.ThermalUpdater.update_module', mock.MagicMock())
    @mock.patch('sonic_platform.thermal_updater.ThermalUpdater.wait_all_sfp_ready')
    @mock.patch('sonic_platform.utils.write_file')
    def test_start_stop(self, mock_write, mock_wait):
        mock_wait.return_value = True
        updater = ThermalUpdater(None)
        updater.start()
        mock_write.assert_called_once_with('/run/hw-management/config/suspend', 0)
        utils.wait_until(updater._timer.is_alive, timeout=5)

        mock_write.reset_mock()
        updater.stop()
        assert not updater._timer.is_alive()
        mock_write.assert_called_once_with('/run/hw-management/config/suspend', 1)

        mock_wait.return_value = False
        mock_write.reset_mock()
        updater.start()
        mock_write.assert_called_once_with('/run/hw-management/config/suspend', 1)
        updater.stop()

    @mock.patch('sonic_platform.thermal_updater.time.sleep', mock.MagicMock())
    def test_wait_all_sfp_ready(self):
        mock_sfp = mock.MagicMock()
        mock_sfp.is_sw_control = mock.MagicMock(return_value=True)
        updater = ThermalUpdater([mock_sfp])
        assert updater.wait_all_sfp_ready()
        mock_sfp.is_sw_control.side_effect = Exception('')
        assert not updater.wait_all_sfp_ready()

    @mock.patch('sonic_platform.utils.read_int_from_file')
    def test_update_asic(self, mock_read):
        mock_read.return_value = 8
        updater = ThermalUpdater(None)
        updater.set_thermal_data = mock.MagicMock()
        assert updater.get_asic_temp() == 1000
        assert updater.get_asic_temp_waning_threashold() == 1000
        assert updater.get_asic_temp_critical_threashold() == 1000
        updater.update_asic()
        assert updater.set_thermal_data.call_count == 3

        mock_read.return_value = None
        assert updater.get_asic_temp() == ASIC_DEFAULT_TEMP_WARNNING_THRESHOLD
        assert updater.get_asic_temp_waning_threashold() == ASIC_DEFAULT_TEMP_WARNNING_THRESHOLD
        assert updater.get_asic_temp_critical_threashold() == ASIC_DEFAULT_TEMP_CRITICAL_THRESHOLD

    def test_update_module(self):
        mock_sfp = mock.MagicMock()
        mock_sfp.sdk_index = 10
        mock_sfp.get_presence = mock.MagicMock(return_value=True)
        mock_sfp.get_temperature = mock.MagicMock(return_value=55.0)
        mock_sfp.get_temperature_warning_threashold = mock.MagicMock(return_value=70.0)
        mock_sfp.get_temperature_critical_threashold = mock.MagicMock(return_value=80.0)
        updater = ThermalUpdater([mock_sfp])
        updater.set_thermal_data = mock.MagicMock()
        updater.update_module()
        updater.set_thermal_data.assert_has_calls([
            mock.call(11, 'input', 55000),
            mock.call(11, 'emergency', 70000),
            mock.call(11, 'crit', 80000),
        ])

        mock_sfp.get_temperature = mock.MagicMock(return_value=0.0)
        updater.update_module()
        updater.set_thermal_data.assert_has_calls([
            mock.call(11, 'input', 0),
            mock.call(11, 'emergency', 0),
            mock.call(11, 'crit', 0),
        ])

        mock_sfp.get_presence = mock.MagicMock(return_value=False)
        updater.remove_thermal_data = mock.MagicMock()
        updater.update_module()
        updater.remove_thermal_data.assert_has_calls([
            mock.call(11, 'input'),
            mock.call(11, 'emergency'),
            mock.call(11, 'crit'),
        ])
