from sonic_platform_base.psu_base import PsuBase
from sonic_platform_base.fan_base import FanBase
import commands

class PsuLed(PsuBase):
    _psu_list = None

    def __init__(self):
        self._psu_list = []
        STATUS_LED_COLOR_GREEN = "green"
        STATUS_LED_COLOR_AMBER = "amber"
        STATUS_LED_COLOR_RED = "red"
        STATUS_LED_COLOR_OFF = "off"
        self.value_map = {
            "on": 1,
            "off": 0,
            "faulty": 4
        }
        self.color_map = {
            0: self.STATUS_LED_COLOR_OFF,
            1: self.STATUS_LED_COLOR_GREEN,
            4: self.STATUS_LED_COLOR_AMBER
        }

        # check i2c bus order
        status, output = commands.getstatusoutput("i2cdetect -l | grep I801 | grep i2c-0")
        if output:
            # order 0
            self._path = "/sys/bus/i2c/devices/0-005e/sys_pwr"
        else:
            # order 1
            self._path = "/sys/bus/i2c/devices/1-005e/sys_pwr"            

    def update_status(self):
        is_power_all_OK = True
        for psu in self._psu_list:
            if not psu.get_presence() or not psu.get_status():
                is_power_all_OK = False
        
        status = self.value_map["on"] if is_power_all_OK else self.value_map["faulty"]  
        try:
            with open(self._path, 'w') as psu_led:
                psu_led.write(str(status))
        except IOError:
            return False

        return True
    
    def get_status(self):
        status = 0
        try:
            with open(self._path, 'r') as psu_led:
                status = int(psu_led.read())
        except IOError:
            return False

        return self.color_map[status]
        

class FanLed(FanBase):
    _fan_list = None
    _path = None

    def __init__(self):
        self._fan_list = []
        self.value_map = {
            "on": 1,
            "off": 0,
            "faulty": 4
        }
        self.color_map = {
            0: self.STATUS_LED_COLOR_OFF,
            1: self.STATUS_LED_COLOR_GREEN,
            4: self.STATUS_LED_COLOR_AMBER
        }

        # check i2c bus order
        status, output = commands.getstatusoutput("i2cdetect -l | grep I801 | grep i2c-0")
        if output:
            # order 0
            self._path = "/sys/bus/i2c/devices/0-005e/fan1_led"
        else:
            # order 1
            self._path = "/sys/bus/i2c/devices/1-005e/fan1_led"            

    def update_status(self):
        is_fan_all_OK = True
        for fan in self._fan_list:
            if not fan.get_status():
                is_fan_all_OK = False
        
        status = self.value_map["on"] if is_fan_all_OK else self.value_map["faulty"]
        try:
            with open(self._path, 'w') as psu_led:
                psu_led.write(str(status))
        except IOError:
            return False

        return True
    
    def get_status(self):
        status = 0
        try:
            with open(self._path, 'r') as fan_led:
                status = int(fan_led.read())
        except IOError:
            return False

        return self.color_map[status]