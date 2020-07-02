import commands

class Led(object):
    STATUS_LED_COLOR_GREEN = "green"
    STATUS_LED_COLOR_AMBER = "amber"
    STATUS_LED_COLOR_OFF = "off"

    value_map = {
        "on": 1,
        "off": 0,
        "faulty": 4
    }
    color_map = {
        0: STATUS_LED_COLOR_OFF,
        1: STATUS_LED_COLOR_GREEN,
        4: STATUS_LED_COLOR_AMBER
    }

    _path = ''
    _psu_set = set()
    _fan_set = set()

    def __init__(self):
        # check i2c bus order
        status, output = commands.getstatusoutput("i2cdetect -l | grep I801 | grep i2c-0")
        if output:
            # order 0
            self._path = "/sys/bus/i2c/devices/0-005e/"
        else:
            # order 1
            self._path = "/sys/bus/i2c/devices/1-005e/"
        
    def update_status(self):
        value = self.get_status_value()
        
        try:
            with open(self.led_path, 'w') as led:
                led.write(str(value))
        except IOError:
            return False
            
        return True

    def get_status(self):
        status = 0
        try:
            with open(self.led_path, 'r') as led:
                status = int(led.read())
        except IOError:
            return False

        return self.color_map[status]


class Alpha_PsuLed(Led):
    def __init__(self):
        super(Alpha_PsuLed, self).__init__()
        self.led_path = self._path + "sys_pwr"
    
    def add_psu(self, psu):
        self._psu_set.add(psu)

    def get_status_value(self):
        status = self.value_map["faulty"]
        from .chassis import NUM_PSU
        if len(self._psu_set) == NUM_PSU:
            is_power_all_OK = True
            for psu in self._psu_set:
                if not psu.get_presence() or not psu.get_status():
                    is_power_all_OK = False
            
            status = self.value_map["on"] if is_power_all_OK else self.value_map["faulty"]  
        return status


class Alpha_FanLed(Led):
    def __init__(self):
        super(Alpha_FanLed, self).__init__()
        self.led_path = self._path + "fan1_led"

    def add_fan(self, fan):
        self._fan_set.add(fan)

    def get_status_value(self):
        status = self.value_map["faulty"]
        from .chassis import NUM_FAN
        if len(self._fan_set) == NUM_FAN:
            is_fan_all_OK = True
            for fan in self._fan_set:
                if not fan.get_status():
                    is_fan_all_OK = False
        
            status = self.value_map["on"] if is_fan_all_OK else self.value_map["faulty"]
        return status
