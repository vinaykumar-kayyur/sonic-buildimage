#!/usr/bin/env python

#############################################################################
# Mellanox
#
# Module contains an implementation of SONiC Platform Base API and
# provides the FANs status which are available in the platform
#
#############################################################################

import os.path

try:
    from sonic_platform_base.fan_base import FanBase
except ImportError as e:
    raise ImportError (str(e) + "- required module not found")

LED_ON = 1
LED_OFF = 0

PWM_MAX = 255

class Fan(FanBase):
    """Platform-specific Fan class"""
    def __init__(self, fan_index, drawer_index = 1, psu_fan = False):
        # API index is starting from 0, Mellanox platform index is starting from 1
        self.index = fan_index + 1
        self.drawer_index = drawer_index + 1

        self.is_psu_fan = psu_fan

        self.fan_path = "/var/run/hw-management/thermal/"
        self.led_path = "/var/run/hw-management/led/"
        
        self.fan_min_speed_path = "fan{}_min".format(self.index)
        if self.is_psu_fan == False:
            self.fan_speed_get_path = "fan{}_speed_get".format(self.index)
            self.fan_speed_set_path = "fan{}_speed_set".format(self.index)
            self.fan_presence_path = "fan{}_status".format(self.drawer_index)
            self.fan_max_speed_path = "fan{}_max".format(self.index)
        else:
            self.fan_speed_get_path = "psu{}_fan1_speed_get".format(self.index)
            self.fan_presence_path = "psu{}_fan1_speed_get".format(self.index)
            self.fan_max_speed_path = "psu{}_max".format(self.index)
        self.fan_status_path = "fan{}_fault".format(self.index)
        self.fan_green_led_path = "led_fan{}_green".format(self.drawer_index)
        self.fan_red_led_path = "led_fan{}_red".format(self.drawer_index)
        self.fan_pwm_path = "pwm1"

    def get_status(self):
        """
        Retrieves the operational status of fan

        Returns:
            bool: True if fan is operating properly, False if not
        """
        status = 0
        if self.is_psu_fan:
            status = 1
        else:
            try:
                with open(os.path.join(self.fan_path, self.fan_status_path), 'r') as fault_status:
                    status = int(fault_status.read())
            except (ValueError, IOError):
                status = 0

        return status == 1

    def get_presence(self):
        """
        Retrieves the presence status of fan

        Returns:
            bool: True if fan is present, False if not
        """
        status = 0
        if self.is_psu_fan:
            if os.path.exists(os.path.join(self.fan_path, self.fan_presence_path)):
                status = 1
            else:
                status = 0
        else:
            try:
                with open(os.path.join(self.fan_path, self.fan_presence_path), 'r') as presence_status:
                    status = int(presence_status.read())
            except (ValueError, IOError):
                status = 0

        return status == 1
    
    def _get_min_speed_in_rpm(self):
        speed = 0
        try:
            with open(os.path.join(self.fan_path, self.fan_min_speed_path), 'r') as min_fan_speed:
                speed = int(min_fan_speed.read())
        except (ValueError, IOError):
            speed = 0
        
        return speed
    
    def _get_max_speed_in_rpm(self):
        speed = 0
        try:
            with open(os.path.join(self.fan_path, self.fan_max_speed_path), 'r') as max_fan_speed:
                speed = int(max_fan_speed.read())
        except (ValueError, IOError):
            speed = 0
        
        return speed

    def get_speed(self):
        """
        Retrieves the speed of fan

        Returns:
            int: percentage of the max fan speed
        """
        speed = 0
        try:
            with open(os.path.join(self.fan_path, self.fan_speed_get_path), 'r') as fan_curr_speed:
                speed_in_rpm = int(fan_curr_speed.read())
        except (ValueError, IOError):
            speed_in_rpm = 0
        
        max_speed_in_rpm = self._get_max_speed_in_rpm()
        
        if self.is_psu_fan:
            speed = 100*speed_in_rpm/max_speed_in_rpm
        else: 
            min_speed_in_rpm = self._get_min_speed_in_rpm()
            speed = 100*speed_in_rpm/max_speed_in_rpm

        return speed

    def get_target_speed(self):
        """
        Retrieves the expected speed of fan

        Returns:
            int: percentage of the max fan speed
        """
        speed = 0

        if self.is_psu_fan:
            # Not like system fan, psu fan speed can not be modified, so target speed is N/A 
            return speed
        try:
            with open(os.path.join(self.fan_path, self.fan_speed_set_path), 'r') as fan_pwm:
                pwm = int(fan_pwm.read())
        except (ValueError, IOError):
            pwm = 0
        
        speed = int(round(pwm*100.0/PWM_MAX))
        
        return speed

    def set_speed(self, speed):
        """
        Set fan speed to expected value

        Returns:
            bool: True if set success, False if fail. 
        """
        status = True
        pwm = int(round(PWM_MAX*speed/100.0))

        if self.is_psu_fan:
            #PSU fan speed is not setable.
            return False
        
        try:
            with open(os.path.join(self.fan_path, self.fan_speed_set_path), 'w') as fan_pwm:
                print pwm
                length = fan_pwm.write(str(pwm))
                print length
        except (ValueError, IOError):
            print "failed to open file"
            status = False

        return status == True

    def set_status_led(self, color):
        """
        Set led to expected color

        Returns:
            bool: True if set success, False if fail. 
        """
        if self.is_psu_fan:
            # PSU fan led status is not able to set
            return False
        status = False
        if color == 'green':
            try:
                with open(os.path.join(self.led_path, self.fan_green_led_path), 'w') as fan_led:
                    fan_led.write(str(LED_ON))
            except (ValueError, IOError):
                status = False
        elif color == 'red':
            try:
                with open(os.path.join(self.led_path, self.fan_red_led_path), 'w') as fan_led:
                    fan_led.write(str(LED_ON))
            except (ValueError, IOError):
                status = False
        elif color == 'off':
            try:
                with open(os.path.join(self.led_path, self.fan_green_led_path), 'w') as fan_led:
                    fan_led.write(str(LED_OFF))
            except (ValueError, IOError):
                status = False

            try:
                with open(os.path.join(self.led_path, self.fan_red_led_path), 'w') as fan_led:
                    fan_led.write(str(LED_OFF))
            except (ValueError, IOError):
                status = False
        else:
            pass

        return status == True

    def get_speed_tolerance(self):
        """
        Retrieves the speed tolerance of the fan

        Returns:
            An integer, the percentage of variance from target speed which is
                 considered tolerable
        """
        # The tolerance value not decided yet, discussing with low-level team
        pass