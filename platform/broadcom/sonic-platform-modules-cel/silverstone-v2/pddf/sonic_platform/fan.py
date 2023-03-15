#!/usr/bin/env python
# @Company ：Celestica
# @Time    : 2023/2/18 15:43
# @Mail    : J_Talong@163.com yajiang@celestica.com
# @Author  : jiang tao
try:
    from sonic_platform_pddf_base.pddf_fan import PddfFan
    from . import helper
    import re
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

Fan_Direction_Cmd = "0x3a 0x62 {}"
Set_Pwm_Cmd = "0x3a 0x26 0x02 {} {}"
Disable_Fcs_mode = "0x3a 0x26 0x01 0x00"
Led_Manual_Control = "0x3a 0x42 0x02 0x00"
Set_Led_Color = "0x3a 0x39 0x02 {} {}"


class Fan(PddfFan):
    """PDDF Platform-Specific Fan class"""

    def __init__(self, tray_idx, fan_idx=0, pddf_data=None, pddf_plugin_data=None, is_psu_fan=False, psu_index=0):
        # idx is 0-based 
        PddfFan.__init__(self, tray_idx, fan_idx, pddf_data, pddf_plugin_data, is_psu_fan, psu_index)
        self.helper = helper.APIHelper()

    def get_presence(self):
        """
          Retrieves the presence of fan
        """
        return super().get_presence() and self.get_status()

    def get_direction(self):
        """
          Retrieves the direction of fan
 
          Returns:
               A string, either FAN_DIRECTION_INTAKE or FAN_DIRECTION_EXHAUST
               depending on fan direction
               Or N/A if fan removed or abnormal
        """
        if not self.get_status():
            return 'N/A'

        return super().get_direction()

    def get_speed(self):
        """
        Obtain the fan speed ratio (rpm/max rpm) according to the fan maximum rpm in the pd-plugin.json file
        (cause of the conversion, it needs to * 150)

        returns: if the value > 100, return the value of rpm. else return Speed/percentage of maximum speed.
        """
        fan_name = self.get_name()
        speed_rpm = self.get_speed_rpm()
        if "PSU" in fan_name:
            max_psu_fan_rpm = eval(self.plugin_data['PSU']['PSU_FAN_MAX_SPEED'])
            psu_speed_percentage = round(speed_rpm / max_psu_fan_rpm * 100)
            return speed_rpm if psu_speed_percentage > 100 else psu_speed_percentage

        speed_rpm = speed_rpm * 150
        # if use 'get_direction' to get the fan direction, it will make python maximum recursion depth exceeded.
        fan_index = int(re.findall(r"Fantray(\d+)_\d+", fan_name)[0])
        direction_cmd = Fan_Direction_Cmd.format(fan_index - 1)
        status, direction = self.helper.ipmi_raw(direction_cmd)
        if status:
            direction = str(int(direction, 16))
            f_r_fan = "Front" if fan_name.endswith("1") else "Rear"
            max_fan_rpm = eval(self.plugin_data['FAN']['FAN_MAX_RPM_SPEED'][direction][f_r_fan])
            speed_percentage = round(speed_rpm / max_fan_rpm * 100)
            return speed_rpm if speed_percentage > 100 else speed_percentage
        else:
            return 0

    def set_status_led(self, color):
        """
        Overwrite.
        Set fans status led
        return: True/False
        """
        if self.is_psu_fan:
            raise NotImplementedError
        else:
            # set LED mode to Manual Control
            status_ctl, result_ctl = self.helper.ipmi_raw(Led_Manual_Control)
            if not status_ctl:
                print("Fail! Set LED mode to Manual Control fail!")
            color_dict = {
                self.STATUS_LED_COLOR_OFF: "0",
                self.STATUS_LED_COLOR_GREEN: "1",
                self.STATUS_LED_COLOR_AMBER: "2",
            }
            color_data = color_dict.get(color.lower())
            if not color_data:
                print("Fail! Can't set fan%s status led to %s.Cause fan doesn't have this module"
                      % (self.fantray_index, color))
                return False
            set_color_cmd = Set_Led_Color.format(hex(self.fantray_index + 3), color_data)
            status, result = self.helper.ipmi_raw(set_color_cmd)
            if not status:
                print("Fail! Set fan%s to %s fail" % (self.fantray_index, color))
            return status

    def set_speed(self, speed):
        """
        Sets the fan speed(pwm)

        Args:
            speed: An integer, the percentage of full fan speed to set fan to,
                   in the range 0 (off) to 100 (full speed)

        Returns:
            A boolean, True if speed is set successfully, False if not
        """
        if speed < 20 or speed > 100:
            print("Error: Invalid speed %d. Please provide a valid speed percentage(20~100)" % speed)
            return False

        # Disable FCS auto control mode
        status, result = self.helper.ipmi_raw(Disable_Fcs_mode)
        if not status:
            print("Fail! Disable FCS auto control mode fail!")
            return status

        if self.is_psu_fan:
            psu_data = 7 if str(self.fans_psu_index) == "1" else 8
            set_pwm_cmd = Set_Pwm_Cmd.format(hex(psu_data), speed)
            status, result = self.helper.ipmi_raw(set_pwm_cmd)
            if not status:
                print("Fail! Set PSU%d speed=%d fail!" % (self.fans_psu_index, speed))
        else:
            set_pwm_cmd = Set_Pwm_Cmd.format(hex(self.fantray_index - 1), speed)
            status, result = self.helper.ipmi_raw(set_pwm_cmd)
            if not status:
                print("Fail! Set Fan%d speed=%d fail!" % (self.fantray_index, speed))
        return status
