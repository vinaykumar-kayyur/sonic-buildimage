#######################################################
# 
# led.py
# Python implementation of the Class led
# Original author: support@ragilenetworks.com
# 
#######################################################
from devicebase import devicebase

class led(devicebase):
    def __init__(self, conf = None):
        if conf is not  None:
            self.name = conf.get('name', None)
            self.led_attrs_config = conf.get('led_attrs', None)
            self.led_config = conf.get('led', None)

    def set_color(self, color, blink):
        status = self.led_attrs_config.get(color, None)
        if status == None:
            return False
        if blink == True:
            blink_status = self.led_attrs_config.get('flash', None)
        elif blink == False:
            blink_status = self.led_attrs_config.get('light', None)
        if blink_status == None:
            return False

        mask = self.led_attrs_config.get('mask', 0xff)

        if isinstance(self.led_config, list):
            for led_config_index in self.led_config:
                ret, value = self.get_value(led_config_index)
                if (ret == False) or (value is None):
                    return False
                setval = (int(value) & ~mask) | (status & blink_status)
                ret, val = self.set_value(led_config_index, setval)
        else:
            ret, value = self.get_value(self.led_config)
            if (ret == False) or (value is None):
                return False
            setval = (int(value) & ~mask) | (status & blink_status)
            ret, val = self.set_value(self.led_config, setval)
        return ret

    def get_color():
        pass

    def get_location():
        pass

    def get_name():
        pass


    def set_location():
        pass

    def set_name():
        pass
