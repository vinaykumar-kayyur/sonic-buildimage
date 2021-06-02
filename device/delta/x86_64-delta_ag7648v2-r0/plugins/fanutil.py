#############################################################################
# Delta-AG7648v2
#
# Module contains an implementation of SONiC Fans Base API and
# provides the Fans status which are available in the platform
#
#############################################################################

try:
    import os.path
    import syslog
    import subprocess
    from glob import glob
    from sonic_fan.fan_base import FanBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

def log_err(msg):
    syslog.openlog("fanutil")
    syslog.syslog(syslog.LOG_ERR, msg)
    syslog.closelog()

class FanUtil(FanBase):
    """Platform-specific FanUtil class"""
    MAX_FAN_PER_DRAWER = 2
    EEPROM_BASE_BUS_NUM = 20
    FAN_NUM = 5
    GET_HWSKU_CMD = "sonic-cfggen -d -v DEVICE_METADATA.localhost.hwsku"
    sku_without_fan_direction = ['Delta-ag7648v2']
    sku_with_unpluggable_fan = [ ]

    def __init__(self):
        FanBase.__init__(self)

        self.sku_name = self._get_sku_name()
        self.fan_path = "/sys/bus/i2c/drivers/emc2305/26-002c/"
        self.fan_path_rear = "/sys/bus/i2c/drivers/emc2305/26-002d/"
        self.fan_path_eeprom = "/sys/bus/i2c/devices/{}-0050/eeprom"

        if self.sku_name in self.sku_with_unpluggable_fan:
            self.fan_status = None
            self.unpluggable_fan = True
        else:
            self.fan_status = "fan{}_status"
            self.unpluggable_fan = False
        self.fan_get_speed = "fan{}_input"
        self.fan_set_speed = "fan{}_input_percentage"
        if self.sku_name in self.sku_without_fan_direction:
            self.fan_direction = None
        else:
            self.fan_direction = "system/fan_dir"

        self.num_of_fan = self.FAN_NUM

    def _get_sku_name(self):
        p = subprocess.Popen(self.GET_HWSKU_CMD, shell=True, universal_newlines=True, stdout=subprocess.PIPE)
        out, err = p.communicate()
        return out.rstrip('\n')

    def _convert_fan_index_to_drawer_index(self, index):
        return (index + self.MAX_FAN_PER_DRAWER - 1) / self.MAX_FAN_PER_DRAWER

    def _read_file(self,file_path, file_pattern, index=0):
        return_value = 0
        try:
            with open(os.path.join(file_path, file_pattern.format(index)), 'r') as file_to_read:
                return_value = int(file_to_read.read())
        except IOError:
            log_err("Read file {} failed".format(self.fan_path + file_pattern.format(index)))
            return return_value

        return return_value

    def get_num_fans(self):
        return self.num_of_fan

    def get_status(self, index):
        if not self.get_presence(index):
            return False

        return self.get_speed(index) != 0

    def get_presence(self, index):
        if index > self.num_of_fan:
            raise RuntimeError(
                "index ({}) shouldn't be greater than number of fans ({})".format(index, self.num_of_fan))
        if self.unpluggable_fan:
            return True

        eeprom_path = self.fan_path_eeprom.format(index + self.EEPROM_BASE_BUS_NUM)

        try:
            with open(eeprom_path, 'r') as eeporm:
                return True
        except IOError as e:
                #print ("Error: unable to open file: %s" % str(e))
                return False
        return False

    def get_direction(self, index):
        return self.FAN_DIRECTION_EXHAUST

    def get_speed(self, index):
        speed = self._read_file(self.fan_path,self.fan_get_speed, index)
        return speed

    def get_speed_rear(self, index):
        speed = self._read_file(self.fan_path_rear,self.fan_get_speed, index)
        return speed

    def set_speed(self, val):
        print("Setting fan speed is not allowed !")
        return False

        if speed < 0 or speed > 100:
            print("Error: Invalid speed %d. Please provide a valid speed percentage" % speed)
            return False

        status = True
        for index in range(1,self.num_of_fan+1):
            try:
                with open(os.path.join(self.fan_path, self.fan_set_speed.format(index)), 'w') as fan_percentage:
                    fan_percentage.write(str(val))
            except (ValueError, IOError):
                log_err("Read file {} failed".format(self.fan_path + self.fan_set_speed.format(index)))
                status = False

            try:
                with open(os.path.join(self.fan_path_rear, self.fan_set_speed.format(index)), 'w') as fan_percentage:
                    fan_percentage.write(str(val))
            except (ValueError, IOError):
                log_err("Read file {} failed".format(self.fan_path + self.fan_set_speed.format(index)))
                status = False
        return status
