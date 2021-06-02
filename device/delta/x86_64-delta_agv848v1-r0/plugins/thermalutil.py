#############################################################################
# Delta-AGV848v1
#
# Module contains an implementation of SONiC Thermal Base API and
# provides the thermal sensor status which are available in the platform
#
#############################################################################

try:
    import os.path
    import syslog
    import subprocess
    from sonic_thermal.thermal_base import ThermalBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

def log_info(msg):
    syslog.openlog("thermalutil")
    syslog.syslog(syslog.LOG_INFO, msg)
    syslog.closelog()

hwsku_dict_thermal = {'Delta-agv848v1': 0}

class ThermalUtil(ThermalBase):
    """Platform-specific Thermalutil class"""
    GET_HWSKU_CMD = "sonic-cfggen -d -v DEVICE_METADATA.localhost.hwsku"
    thermal_name = ["System Board 1", "System Board 2", "CPU Board", "Fan control Board","PSU1","PSU2"]
    thermal_path = ["/sys/bus/i2c/drivers/lm75/4-004d/hwmon/",
                    "/sys/bus/i2c/drivers/lm75/4-004e/hwmon/",
                    "/sys/bus/i2c/drivers/lm75/4-004f/hwmon/",
                    "/sys/bus/i2c/drivers/lm75/27-004f/hwmon/",
                    "/sys/bus/i2c/devices/6-0058/",
                    "/sys/bus/i2c/devices/7-0058/"]
    THERMAL_NUM = 6
    self.PSU_START = 5

    def _get_sku_name(self):
        p = subprocess.Popen(self.GET_HWSKU_CMD, shell=True, universal_newlines=True, stdout=subprocess.PIPE)
        out, err = p.communicate()
        return out.rstrip('\n')

    def __init__(self):
        sku = self._get_sku_name()
        self.thermal_temp = "{}/temp1_input"
        self.thermal_psutemp = "temp1_input"
        self.number_of_thermals = self.THERMAL_NUM

    def show_thermal_temp_values(self, index):
        return self.get_name(index-1),  self.get_temperature(index-1)

    def get_num_thermals(self):
        return self.number_of_thermals

    def get_name(self, index):
        if index >= self.number_of_thermals:
            raise RuntimeError("index ({}) shouldn't be greater than {}".format(index, self.number_of_thermals))
        return self.thermal_name[index]

    def get_temperature(self, index):
        if self.__index < self.PSU_START-1:
            FileList = os.listdir(self.thermal_path[self.__index])
            temp1_path = self.thermal_temp.format(FileList[0])
        else:
            temp1_path = self.thermal_psutemp

        try:
            with open(os.path.join(self.thermal_path[self.__index], temp1_path), 'r') as file_to_read:
                return_value = int(file_to_read.read())
        except IOError:
            return_value = 0
        return float(return_value/1000)
