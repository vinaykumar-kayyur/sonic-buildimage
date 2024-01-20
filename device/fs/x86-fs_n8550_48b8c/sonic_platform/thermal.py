#############################################################################
# FS
#
# Thermal contains an implementation of SONiC Platform Base API and
# provides the thermal device status which are available in the platform
#
#############################################################################

import os
import os.path
import glob

try:
    from sonic_platform_base.thermal_base import ThermalBase
    from .helper import DeviceThreshold
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

PSU_I2C_PATH = "/sys/bus/i2c/devices/{}-00{}/"
PSU_I2C_MAPPING = {
    0: {
        "bus": 17,
        "addr": "59"
    },
    1: {
        "bus": 13,
        "addr": "5b"
    },
}

PSU_CPLD_I2C_MAPPING = {
    0: {
        "bus": 17,
        "addr": "51"
    },
    1: {
        "bus": 13,
        "addr": "53"
    },
}


class Thermal(ThermalBase):
    """Platform-specific Thermal class"""

    THERMAL_NAME_LIST = []
    PSU_THERMAL_NAME_LIST = []
    SYSFS_PATH = "/sys/bus/i2c/devices"
    CPU_SYSFS_PATH = "/sys/devices/platform"

    def __init__(self, thermal_index=0, is_psu=False, psu_index=0):
        self.index = thermal_index
        self.is_psu = is_psu
        self.psu_index = psu_index

        if self.is_psu:
            psu_i2c_bus = PSU_I2C_MAPPING[psu_index]["bus"]
            psu_i2c_addr = PSU_I2C_MAPPING[psu_index]["addr"]
            self.psu_hwmon_path = PSU_I2C_PATH.format(psu_i2c_bus,
                                                      psu_i2c_addr)
            psu_i2c_bus = PSU_CPLD_I2C_MAPPING[psu_index]["bus"]
            psu_i2c_addr = PSU_CPLD_I2C_MAPPING[psu_index]["addr"]
            self.cpld_path = PSU_I2C_PATH.format(psu_i2c_bus, psu_i2c_addr)

        # Add thermal name
        self.THERMAL_NAME_LIST.append("Temp sensor 1")
        self.THERMAL_NAME_LIST.append("Temp sensor 2")
        self.THERMAL_NAME_LIST.append("Temp sensor 3")
        self.THERMAL_NAME_LIST.append("Temp sensor 4")
        self.THERMAL_NAME_LIST.append("CPU Package Temp")
        self.THERMAL_NAME_LIST.append("CPU Core 0 Temp")
        self.THERMAL_NAME_LIST.append("CPU Core 1 Temp")
        self.THERMAL_NAME_LIST.append("CPU Core 2 Temp")
        self.THERMAL_NAME_LIST.append("CPU Core 3 Temp")
        self.PSU_THERMAL_NAME_LIST.append("PSU-1 temp sensor 1")
        self.PSU_THERMAL_NAME_LIST.append("PSU-2 temp sensor 1")

        self.conf = DeviceThreshold(self.get_name())
        # Default thresholds
        self.default_threshold = {
            self.THERMAL_NAME_LIST[0] : {
                self.conf.HIGH_THRESHOLD_FIELD : '80.0',
                self.conf.LOW_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE,
                self.conf.HIGH_CRIT_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE,
                self.conf.LOW_CRIT_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE
            },
            self.THERMAL_NAME_LIST[1] : {
                self.conf.HIGH_THRESHOLD_FIELD : '80.0',
                self.conf.LOW_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE,
                self.conf.HIGH_CRIT_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE,
                self.conf.LOW_CRIT_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE
            },
            self.THERMAL_NAME_LIST[2] : {
                self.conf.HIGH_THRESHOLD_FIELD : '80.0',
                self.conf.LOW_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE,
                self.conf.HIGH_CRIT_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE,
                self.conf.LOW_CRIT_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE
            },
            self.THERMAL_NAME_LIST[3] : {
                self.conf.HIGH_THRESHOLD_FIELD : '80.0',
                self.conf.LOW_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE,
                self.conf.HIGH_CRIT_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE,
                self.conf.LOW_CRIT_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE
            },
            self.THERMAL_NAME_LIST[4] : {
                self.conf.HIGH_THRESHOLD_FIELD : '82.0',
                self.conf.LOW_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE,
                self.conf.HIGH_CRIT_THRESHOLD_FIELD : '104.0',
                self.conf.LOW_CRIT_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE
            },
            self.THERMAL_NAME_LIST[5] : {
                self.conf.HIGH_THRESHOLD_FIELD : '82.0',
                self.conf.LOW_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE,
                self.conf.HIGH_CRIT_THRESHOLD_FIELD : '104.0',
                self.conf.LOW_CRIT_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE
            },
            self.THERMAL_NAME_LIST[6] : {
                self.conf.HIGH_THRESHOLD_FIELD : '82.0',
                self.conf.LOW_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE,
                self.conf.HIGH_CRIT_THRESHOLD_FIELD : '104.0',
                self.conf.LOW_CRIT_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE
            },
            self.THERMAL_NAME_LIST[7] : {
                self.conf.HIGH_THRESHOLD_FIELD : '82.0',
                self.conf.LOW_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE,
                self.conf.HIGH_CRIT_THRESHOLD_FIELD : '104.0',
                self.conf.LOW_CRIT_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE
            },
            self.THERMAL_NAME_LIST[8] : {
                self.conf.HIGH_THRESHOLD_FIELD : '82.0',
                self.conf.LOW_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE,
                self.conf.HIGH_CRIT_THRESHOLD_FIELD : '104.0',
                self.conf.LOW_CRIT_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE
            },
            self.PSU_THERMAL_NAME_LIST[0] : {
                self.conf.HIGH_THRESHOLD_FIELD : '80.0',
                self.conf.LOW_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE,
                self.conf.HIGH_CRIT_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE,
                self.conf.LOW_CRIT_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE
            },
            self.PSU_THERMAL_NAME_LIST[1] : {
                self.conf.HIGH_THRESHOLD_FIELD : '80.0',
                self.conf.LOW_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE,
                self.conf.HIGH_CRIT_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE,
                self.conf.LOW_CRIT_THRESHOLD_FIELD : self.conf.NOT_AVAILABLE
            }
        }

        # Set hwmon path
        i2c_path = {
            0: {"hwmon_path":"15-0048/hwmon/hwmon*/", "ss_index":1},
            1: {"hwmon_path":"15-0049/hwmon/hwmon*/", "ss_index":1},
            2: {"hwmon_path":"15-004a/hwmon/hwmon*/", "ss_index":1},
            3: {"hwmon_path":"15-004b/hwmon/hwmon*/", "ss_index":1},
            4: {"hwmon_path":"coretemp.0/hwmon/hwmon*/", "ss_index":1},
            5: {"hwmon_path":"coretemp.0/hwmon/hwmon*/", "ss_index":2},
            6: {"hwmon_path":"coretemp.0/hwmon/hwmon*/", "ss_index":3},
            7: {"hwmon_path":"coretemp.0/hwmon/hwmon*/", "ss_index":4},
            8: {"hwmon_path":"coretemp.0/hwmon/hwmon*/", "ss_index":5}
        }.get(self.index, None)

        self.is_cpu = False
        if self.index in range(4,9):
            self.is_cpu = True
            self.hwmon_path = "{}/{}".format(self.CPU_SYSFS_PATH, i2c_path["hwmon_path"])
        else:
            self.hwmon_path = "{}/{}".format(self.SYSFS_PATH, i2c_path["hwmon_path"])
        self.ss_key = self.THERMAL_NAME_LIST[self.index]
        self.ss_index = i2c_path["ss_index"]

    def __read_txt_file(self, file_path):
        for filename in glob.glob(file_path):
            try:
                with open(filename, 'r') as fd:
                    data =fd.readline().strip()
                    if len(data) > 0:
                        return data
            except IOError as e:
                pass

        return None

    def __get_temp(self, temp_file):
        if not self.is_psu:
            temp_file_path = os.path.join(self.hwmon_path, temp_file)
        else:
            temp_file_path = temp_file

        raw_temp = self.__read_txt_file(temp_file_path)
        if raw_temp is not None:
            return float(raw_temp) / 1000
        else:
            return 0

    def __set_threshold(self, file_name, temperature):
        if self.is_psu:
            return True

        temp_file_path = os.path.join(self.hwmon_path, file_name)
        for filename in glob.glob(temp_file_path):
            try:
                with open(filename, 'w') as fd:
                    fd.write(str(temperature))
                    fd.flush()
                return True
            except IOError:
                return False

    def get_temperature(self):
        """
        Retrieves current temperature reading from thermal
        Returns:
            A float number of current temperature in Celsius up to nearest thousandth
            of one degree Celsius, e.g. 30.125
        """
        if not self.is_psu:
            temp_file = "temp{}_input".format(self.ss_index)
        else:
            temp_file = self.psu_hwmon_path + "psu_temp1_input"

        return self.__get_temp(temp_file)

    def get_high_critical_threshold(self):
        """
        Retrieves the high critical threshold temperature of thermal

        Returns:
            A float number, the high critical threshold temperature of thermal in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        value = self.conf.get_high_critical_threshold()
        if value != self.conf.NOT_AVAILABLE:
            return float(value)

        default_value = self.default_threshold[self.get_name()][self.conf.HIGH_CRIT_THRESHOLD_FIELD]
        if default_value != self.conf.NOT_AVAILABLE:
            return float(default_value)

        raise NotImplementedError

    def set_high_critical_threshold(self, temperature):
        """
        Sets the critical high threshold temperature of thermal

        Args :
            temperature: A float number up to nearest thousandth of one degree Celsius,
            e.g. 30.125

        Returns:
            A boolean, True if threshold is set successfully, False if not
        """
        try:
            value = float(temperature)
        except:
            return False

        try:
            self.conf.set_high_critical_threshold(str(value))
        except:
            return False

        return True

    def get_high_threshold(self):
        """
        Retrieves the high threshold temperature of thermal
        Returns:
            A float number, the high threshold temperature of thermal in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        value = self.conf.get_high_threshold()
        if value != self.conf.NOT_AVAILABLE:
            return float(value)

        default_value = self.default_threshold[self.get_name()][self.conf.HIGH_THRESHOLD_FIELD]
        if default_value != self.conf.NOT_AVAILABLE:
            return float(default_value)

        raise NotImplementedError

    def set_high_threshold(self, temperature):
        """
        Sets the high threshold temperature of thermal
        Args :
            temperature: A float number up to nearest thousandth of one degree Celsius,
            e.g. 30.125
        Returns:
            A boolean, True if threshold is set successfully, False if not
        """
        try:
            value = float(temperature)
        except:
            return False

        try:
            self.conf.set_high_threshold(str(value))
        except:
            return False

        return True

    def get_name(self):
        """
        Retrieves the name of the thermal device
            Returns:
            string: The name of the thermal device
        """
        if self.is_psu:
            return self.PSU_THERMAL_NAME_LIST[self.psu_index]
        else:
            return self.THERMAL_NAME_LIST[self.index]

    def get_presence(self):
        """
        Retrieves the presence of the PSU
        Returns:
            bool: True if PSU is present, False if not
        """
        if self.is_cpu:
            return True

        if self.is_psu:
            val = self.__read_txt_file(self.cpld_path + "psu_present")
            if val is not None:
                return int(val, 10) == 1
            else:
                return False

        temp_file = "temp{}_input".format(self.ss_index)
        temp_file_path = os.path.join(self.hwmon_path, temp_file)
        raw_txt = self.__read_txt_file(temp_file_path)
        return raw_txt != None

    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        if self.is_cpu:
            return True

        if self.is_psu:
            temp_file = self.psu_hwmon_path + "psu_temp_fault"
            psu_temp_fault = self.__read_txt_file(temp_file)
            if psu_temp_fault is None:
                psu_temp_fault = '1'
            return self.get_presence() and (not int(psu_temp_fault))

        file_str = "temp{}_input".format(self.ss_index)
        file_path = os.path.join(self.hwmon_path, file_str)

        raw_txt = self.__read_txt_file(file_path)
        if raw_txt is None:
            return False
        else:
            return int(raw_txt) != 0

    def get_model(self):
        """
        Retrieves the model number (or part number) of the device
        Returns:
            string: Model/part number of device
        """

        return "N/A"

    def get_serial(self):
        """
        Retrieves the serial number of the device
        Returns:
            string: Serial number of device
        """
        return "N/A"

    def get_position_in_parent(self):
        """
        Retrieves 1-based relative physical position in parent device. If the agent cannot determine the parent-relative position
        for some reason, or if the associated value of entPhysicalContainedIn is '0', then the value '-1' is returned
        Returns:
            integer: The 1-based relative physical position in parent device or -1 if cannot determine the position
        """
        return self.index+1

    def is_replaceable(self):
        """
        Retrieves whether thermal module is replaceable
        Returns:
            A boolean value, True if replaceable, False if not
        """
        return False

