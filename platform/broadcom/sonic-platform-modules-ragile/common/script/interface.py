import sonic_platform

class Interface():
    def __init__(self):
        self.chassis = sonic_platform.platform.Platform().get_chassis()
        self.fan_list = self.chassis.get_all_fans()
        self.thermal_list = self.chassis.get_all_thermals()
        self.psu_list = self.chassis.get_all_psus()

    # Device
    def get_productname(self):
        return self.chassis.get_name()

    # Thermal
    def get_thermal_temp_max(self, name):
        for thermal in self.thermal_list:
            if name == thermal.get_name():
                return thermal.get_high_threshold()

    def get_thermal_temp_min(self, name):
        for thermal in self.thermal_list:
            if name == thermal.get_name():
                return thermal.get_low_threshold()

    def get_thermal_temp(self, name):
        for thermal in self.thermal_list:
            if name == thermal.get_name():
                return thermal.get_temperature()
    # Fans
    def set_fan_speed_pwm(self, speed):
        for fan in self.fan_list:
            fan.set_speed(speed)

    def get_fan_status(self):
        for fan in self.fan_list:
            if fan.get_status() == False:
                return False
        return True

    def get_fan_presence(self):
        for fan in self.fan_list:
            if fan.get_presence() == False:
                return False
        return True

    def set_fan_board_led(self, color):
        for fan in self.fan_list:
            if fan.set_status_led(color) == False:
                return False
        return True

    def get_fan_speed_rpm(self, name):
        for fan in self.fan_list:
            if name == fan.get_name():
                return fan.get_speed_rpm()
        return 0

    # def get_fan_rpm_max(self):
    #     for fan in self.fan_list:
    #         if name == fan.get_name():
    #             return fan.get_speed_rpm()
    #     return 0

    def get_airflow(self):
        tmp1 = self.fan_list[0].get_direction()
        tmp2 = self.fan_list[0].get_direction()
        for fan in self.fan_list:
            tmp1 = fan.get_direction()
            if tmp1 != tmp2:
                return "exhaust"
            tmp2 = tmp1
        return tmp2
    # Psus
    def get_psu_status(self):
        for psu in self.psu_list:
            if psu.get_status() == False:
                return False
            if psu.get_powergood_status() == False:
                return False

        return True

    def set_psu_board_led(self, color):
        for psu in self.psu_list:
            if psu.set_status_led(color) == False:
                return False
        return True

