#############################################################################
# Edgecore
#
# Thermal contains an implementation of SONiC Platform Base API and
# provides the thermal device status which are available in the platform
#
#############################################################################

import os
import os.path
import glob
from collections import namedtuple

try:
    from sonic_platform_base.thermal_base import ThermalBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

Threshold = namedtuple('Threshold', ['high_crit', 'high_err', 'high_warn',
                       'low_warn', 'low_err', 'low_crit'], defaults=[0]*6)


class Thermal(ThermalBase):
    """Platform-specific Thermal class"""

    THERMAL_NAME_LIST = (
        "Main Board 0x48",
        "CPU Board 0x4B",
        "Fan Board 0x4A"
    )
    CPU_THERMAL_NAME = "CPU Core temp"
    SYSFS_PATH = "/sys/bus/i2c/devices"
    THRESHOLDS = {
        0: Threshold(55.0, 50.0, 45.0),
        1: Threshold(55.0, 50.0, 45.0),
        2: Threshold(55.0, 50.0, 45.0)
    }

    def __init__(self, thermal_index=0, is_cpu=False):
        self.SYSFS_PATH = "/sys/bus/i2c/devices"
        self.index = thermal_index
        self.is_cpu = is_cpu

        if self.is_cpu:
            self.cpu_paths = glob.glob('/sys/devices/platform/coretemp.0/hwmon/hwmon*/temp*_input')
            self.cpu_path_idx = 0

        # Set hwmon path
        i2c_path = {
            0: "14-0048/hwmon/hwmon*/",
            1: "24-004b/hwmon/hwmon*/",
            2: "25-004a/hwmon/hwmon*/"
        }.get(self.index, None)

        self.hwmon_path = "{}/{}".format(self.SYSFS_PATH, i2c_path)
        self.ss_key = self.THERMAL_NAME_LIST[self.index]
        self.ss_index = 1

    def __read_txt_file(self, file_path):
        for filename in glob.glob(file_path):
            try:
                with open(filename, 'r') as fd:
                    data =fd.readline().rstrip()
                    return data
            except IOError as e:
                pass

        return None

    def __get_temp(self, temp_file):
        temp_file_path = os.path.join(self.hwmon_path, temp_file)
        raw_temp = self.__read_txt_file(temp_file_path)
        if raw_temp is not None:
            return float(raw_temp)/1000
        else:
            return 0

    def __get_max_temp(self, paths):
        max_temp = -1.0
        max_idx = 0
        for i, path in enumerate(paths):
            read_temp = self.__get_temp(path)
            if(read_temp > max_temp):
                max_temp = read_temp
                max_idx = i
        return max_temp, max_idx

    def __get_cpu_threshold(self, type):
        path = self.cpu_paths[self.cpu_path_idx]
        high_warn = self.__get_temp(path.replace('_input', '_max'))
        if type == 'high_warn':
            return high_warn
        high_crit = self.__get_temp(path.replace('_input', '_crit'))
        if type == 'high_crit':
            return high_crit
        if type == 'high_err':
            return (high_crit + high_warn) / 2
        return 0 # for all low_* thresholds

    def __try_get_threshold(self, type):
        if self.is_cpu:
            return self.__get_cpu_threshold(type)

        if self.index in self.THRESHOLDS:
            return getattr(self.THRESHOLDS[self.index], type)
        else:
            return None

    def get_temperature(self):
        """
        Retrieves current temperature reading from thermal
        Returns:
            A float number of current temperature in Celsius up to nearest thousandth
            of one degree Celsius, e.g. 30.125
        """
        if self.is_cpu:
            cpu_temp, self.cpu_path_idx = self.__get_max_temp(self.cpu_paths)
            return cpu_temp

        temp_file = "temp{}_input".format(self.ss_index)
        return self.__get_temp(temp_file)

    def get_name(self):
        """
        Retrieves the name of the thermal device
            Returns:
            string: The name of the thermal device
        """
        if self.is_cpu:
            return self.CPU_THERMAL_NAME
        return self.THERMAL_NAME_LIST[self.index]

    def get_presence(self):
        """
        Retrieves the presence of the Thermal
        Returns:
            bool: True if Thermal is present, False if not
        """
        if self.is_cpu:
            return True

        temp_file = "temp{}_input".format(self.ss_index)
        temp_file_path = os.path.join(self.hwmon_path, temp_file)
        raw_txt = self.__read_txt_file(temp_file_path)
        if raw_txt is not None:
            return True
        else:
            return False

    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        if self.is_cpu:
            return True

        file_str = "temp{}_input".format(self.ss_index)
        file_path = os.path.join(self.hwmon_path, file_str)
        raw_txt = self.__read_txt_file(file_path)
        if raw_txt is None:
            return False
        else:
            return int(raw_txt) != 0

    def get_high_critical_threshold(self):
        return self.__try_get_threshold('high_crit')

    def get_low_critical_threshold(self):
        return self.__try_get_threshold('low_crit')

    def get_high_threshold(self):
        return self.__try_get_threshold('high_err')

    def get_low_threshold(self):
        return self.__try_get_threshold('low_err')

    def get_high_warning_threshold(self):
        return self.__try_get_threshold('high_warn')

    def get_low_warning_threshold(self):
        return self.__try_get_threshold('low_warn')
