try:
    from sonic_platform_pddf_base.pddf_fan import PddfFan
    from . import api
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class Fan(PddfFan):
    """PDDF Platform-Specific Fan class"""

    def __init__(self, tray_idx, fan_idx=0, pddf_data=None, pddf_plugin_data=None, is_psu_fan=False, psu_index=0):
        # idx is 0-based
        PddfFan.__init__(self, tray_idx, fan_idx, pddf_data, pddf_plugin_data, is_psu_fan, psu_index)
        self.pddf_obj = api.newapi()
    # Provide the functions/variables below for which implementation is to be overwritten
    # Since psu_fan airflow direction cant be read from sysfs, it is fixed as 'F2B' or 'intake'
    def get_direction(self):
        """
        Retrieves the direction of fan

        Returns:
            A string, either FAN_DIRECTION_INTAKE or FAN_DIRECTION_EXHAUST
            depending on fan direction
        """
        return self.FAN_DIRECTION_EXHAUST

    def get_presence(self):
        if not self.is_psu_fan:
            return super().get_presence()
        # psu-fan get_presence
        status = 0
        device = "PSU{}".format(self.fans_psu_index)
        output = self.pddf_obj.get_attr_name_output(device, "psu_present")
        if not output:
            return False

        mode = output['mode']
        status = output['status']

        vmap = self.plugin_data['PSU']['psu_present'][mode]['valmap']

        if status.rstrip('\n') in vmap:
            return vmap[status.rstrip('\n')]
        else:
            return False


    def get_speed_rpm(self):
        if self.is_psu_fan:
            return super().get_speed_rpm()
        else:
            ret = super().get_speed_rpm()
            if ret == 0 or ret == 0xffff:
                return 0
            divisor = 15000000
            mask_low = 0xff
            # revert ret
            ret = (ret >> 8) + ((ret & mask_low) << 8)
            return int(divisor/ret)

    def get_target_speed(self):
        if self.is_psu_fan:
            return None

        return super().get_target_speed()

    def get_speed_tolerance(self):
        """
        Retrieves the speed tolerance of the fan

        Returns:
            An integer, the percentage of variance from target speed which is
                 considered tolerable
        """
        # Fix the speed vairance to 10 percent. If it changes based on platforms, overwrite
        # this value in derived pddf fan class
        return 30


    def get_speed(self):
        """
        Retrieves the speed of fan as a percentage of full speed

        Returns:
            An integer, the percentage of full fan speed, in the range 0 (off)
                 to 100 (full speed)
        """
        if self.is_psu_fan:
            return super().get_speed()
        # TODO This calculation should change based on MAX FAN SPEED
        speed_rpm = self.get_speed_rpm()
        max_speed = int(self.plugin_data['FAN']['FAN_MAX_SPEED'])
        speed_percentage = round((speed_rpm*100)/max_speed)
        if speed_percentage > 100:
            speed_percentage = 100
        return speed_percentage

    def get_status(self):
        if self.is_psu_fan:
            return super().get_status()

        speed_rpm = self.get_speed_rpm()
        status = True if (speed_rpm >= 1000) else False
        return status

    def get_status_led(self):
        if self.is_psu_fan:
            return "N/A"

        presence_status = self.get_presence()
        if presence_status is False:
            return "N/A"

        led_device_name = "FANTRAY{}".format(self.fantray_index) + "_LED"

        if led_device_name not in self.pddf_obj.data.keys():
            # Implement a generic status_led color scheme
            if self.get_status():
                return self.STATUS_LED_COLOR_GREEN
            else:
                return self.STATUS_LED_COLOR_RED

        device_name = self.pddf_obj.data[led_device_name]['dev_info']['device_name']
        self.pddf_obj.create_attr('device_name', device_name,  self.pddf_obj.get_led_path())
        self.pddf_obj.create_attr('index', str(self.fantray_index-1), self.pddf_obj.get_led_path())
        self.pddf_obj.create_attr('dev_ops', 'get_status',  self.pddf_obj.get_led_path())
        color = self.pddf_obj.get_led_color()
        return (color)

