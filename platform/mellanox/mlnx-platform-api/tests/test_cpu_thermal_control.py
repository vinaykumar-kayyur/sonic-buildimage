import glob
import os
import pytest
import sys
if sys.version_info.major == 3:
    from unittest import mock
else:
    import mock

test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
sys.path.insert(0, modules_path)

from sonic_platform.cpu_thermal_control import CPUThermalControl


class TestCPUThermalControl:
    @mock.patch('sonic_platform.device_data.DeviceDataManager.get_cpu_thermal_threshold', mock.MagicMock(return_value=(85, 95)))
    @mock.patch('sonic_platform.utils.read_int_from_file')
    @mock.patch('sonic_platform.utils.write_file')
    def test_run(self, mock_write_file, mock_read_file):
        instance = CPUThermalControl()
        file_content = {
            CPUThermalControl.CPU_COOLING_STATE: 5,
            CPUThermalControl.CPU_TEMP_FILE: instance.temp_high + 1
        }

        def read_file(file_path, **kwargs):
            return file_content[file_path]

        mock_read_file.side_effect = read_file
        # Test current temp is higher than high threshold
        instance.run(0)
        mock_write_file.assert_called_with(CPUThermalControl.CPU_COOLING_STATE, CPUThermalControl.MAX_COOLING_STATE, log_func=None)

        # Test current temp is lower than low threshold
        file_content[CPUThermalControl.CPU_TEMP_FILE] = instance.temp_low - 1
        instance.run(0)
        mock_write_file.assert_called_with(CPUThermalControl.CPU_COOLING_STATE, CPUThermalControl.MIN_COOLING_STATE, log_func=None)

        # Test current temp increasing
        file_content[CPUThermalControl.CPU_TEMP_FILE] = instance.temp_low
        instance.run(0)
        mock_write_file.assert_called_with(CPUThermalControl.CPU_COOLING_STATE, 6, log_func=None)

        # Test current temp decreasing
        instance.run(instance.temp_low + 1)
        mock_write_file.assert_called_with(CPUThermalControl.CPU_COOLING_STATE, 4, log_func=None)

        # Test current temp increasing and current cooling state is already the max
        file_content[CPUThermalControl.CPU_TEMP_FILE] = 85
        file_content[CPUThermalControl.CPU_COOLING_STATE] = CPUThermalControl.MAX_COOLING_STATE
        instance.run(84)
        mock_write_file.assert_called_with(CPUThermalControl.CPU_COOLING_STATE, CPUThermalControl.MAX_COOLING_STATE, log_func=None)

        # Test current temp decreasing and current cooling state is already the max
        file_content[CPUThermalControl.CPU_COOLING_STATE] = CPUThermalControl.MIN_COOLING_STATE
        instance.run(86)
        mock_write_file.assert_called_with(CPUThermalControl.CPU_COOLING_STATE, CPUThermalControl.MIN_COOLING_STATE, log_func=None)
