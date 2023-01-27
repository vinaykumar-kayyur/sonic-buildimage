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

    def get_speed_rpm(self):
        if self.is_psu_fan:
            return super().get_speed_rpm()
        else:
            divisor = 15000000
            mask_low = 0xff
            ret = super().get_speed_rpm()
            # revert ret
            ret = (ret >> 8) + ((ret & mask_low) << 8)
            return int(divisor/ret)

    def get_target_speed(self):
        if self.is_psu_fan:
            return None

        return super().get_target_speed()

    def get_status_led(self):
        if self.is_psu_fan:
            return "N/A"

        led_device_name = "FANTRAY{}".format(self.fantray_index) + "_LED"

        if led_device_name not in self.pddf_obj.data.keys():
            # Implement a generic status_led color scheme
            if self.get_status():
                return self.STATUS_LED_COLOR_GREEN
            else:
                return self.STATUS_LED_COLOR_OFF

        device_name = self.pddf_obj.data[led_device_name]['dev_info']['device_name']
        self.pddf_obj.create_attr('device_name', device_name,  self.pddf_obj.get_led_path())
        self.pddf_obj.create_attr('index', str(self.fantray_index-1), self.pddf_obj.get_led_path())
        self.pddf_obj.create_attr('dev_ops', 'get_status',  self.pddf_obj.get_led_path())
        color = self.pddf_obj.get_led_color()
        return (color)

