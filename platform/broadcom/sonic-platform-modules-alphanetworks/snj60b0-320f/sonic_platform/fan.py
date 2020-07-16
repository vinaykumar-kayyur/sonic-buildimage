#!/usr/bin/env python

#############################################################################
#
# Module contains an implementation of SONiC Platform Base API and
# provides the fan status which are available in the platform
#
#############################################################################

try:
    from sonic_platform_base.fan_base import FanBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

class Alpha_Fan(FanBase):
    """Platform-specific Fan class"""

    FAN_MOD_NAME = 'snj60b0_320f_fpga'
    FAN_FRONT_RPM_MAX = 21000
    FAN_REAR_RPM_MAX = 19000
    FAN_SPEED_TOLERANCE_PERCENTAGE = 10
    NUM_FANTRAYS = 6
    FANS_PERTRAY = 2
    BASE_VAL_PATH = '/sys/bus/i2c/devices/0-005e/{0}'
    FAN_DUTY_PATH = '/sys/bus/i2c/devices/0-005e/fan_pwm'

    def __init__(self, fan_index):
        self.index = fan_index + 1
        FanBase.__init__(self)
        
        self.fantray_index = (fan_index)/self.FANS_PERTRAY + 1
        self.fan_index_intray = self.index - ((self.fantray_index-1)*self.FANS_PERTRAY)

    def get_name(self):
        """
        Retrieves the name of the device

        Returns:
            string: The name of the device
        """
        return "FAN {}".format(self.index)

    def get_status(self):
        """
        Retrieves the operational status of the device

        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        status = 0
        attr = 'fan' + str(self.fantray_index) + '_fault'
        node = self.BASE_VAL_PATH.format(attr)
        try:
            with open(node, 'r') as fault:
                status = int(fault.read())
        except IOError as e:
            print "Error: %s"%str(e)
            return False
        return False if (status > 0) else True

    def get_presence(self):
        """
        Retrieves the presence of the device

        Returns:
            bool: True if device is present, False if not
        """
        status = 0
        attr = 'fan' + str(self.fantray_index) + '_present'
        node = self.BASE_VAL_PATH.format(attr)
        try:
            with open(node, 'r') as presence_status:
                status = int(presence_status.read())
        except IOError as e:
            print "Error: %s"%str(e)
            return None
        return status == 1

    def get_direction(self):
        """
        Retrieves the direction of fan

        Returns:
            A string, either FAN_DIRECTION_INTAKE or FAN_DIRECTION_EXHAUST
            depending on fan direction
        """
        direction = ""
        attr = 'fan' + str(self.fantray_index) + '_direction'
        node = self.BASE_VAL_PATH.format(attr)
        try:
            with open(node, 'r') as fan_dir:
                direction = int(fan_dir.read())
        except IOError as e:
            print "Error: %s"%str(e)
            return self.FAN_DIRECTION_INTAKE
        if direction == 1:
            return self.FAN_DIRECTION_INTAKE

        return self.FAN_DIRECTION_EXHAUST

    def get_speed(self):
        """
        Retrieves the speed of fan as a percentage of full speed

        Returns:
            An integer, the percentage of full fan speed, in the range 0 (off)
                 to 100 (full speed)
        """
        frpm = 0
        attr = 'fan' + str(self.fantray_index) + '_{}_speed_rpm'.format('front' if (self.fan_index_intray==1) else 'rear')
        node = self.BASE_VAL_PATH.format(attr)
        try:
            with open(node, 'r') as speed:
                frpm = int(speed.read())
        except IOError as e:
            print "Error: %s"%str(e)
            return 0

        speed = 0
        if self.fan_index_intray == 1:
            speed = (frpm * 100) / self.FAN_FRONT_RPM_MAX
        else:
            speed =  (frpm * 100) / self.FAN_REAR_RPM_MAX

        if speed > 100:
            speed = 100
        
        return speed

    def get_speed_rpm(self):
        """
        Retrieves the speed of fan in RPM

        Returns:
            An integer, representing speed of the FAN in rpm
        """
        frpm = 0
        attr = 'fan' + str(self.fantray_index) + '_{}_speed_rpm'.format('front' if (self.fan_index_intray==1) else 'rear')
        node = self.BASE_VAL_PATH.format(attr)
        try:
            with open(node, 'r') as speed:
                frpm = int(speed.read())
        except IOError as e:
            print "Error: %s"%str(e)
            return 0
        
        return frpm

    def get_target_speed(self):
        """
        Retrieves the target (expected) speed of the fan

        Returns:
            An integer, the percentage of full fan speed, in the range 0 (off)
                 to 100 (full speed)
        """
        duty = 0
        node = self.FAN_DUTY_PATH
        try:
            with open(node, 'r') as fan_duty:
                duty = int(fan_duty.read())
                duty = duty * 100 / 255
        except IOError:
            duty = 0
        return duty

    def set_speed(self, speed):
        """
        Sets the fan speed

        Args:
            speed: An integer, the percentage of full fan speed to set fan to,
                   in the range 0 (off) to 100 (full speed)

        Returns:
            A boolean, True if speed is set successfully, False if not
        """
        if speed < 0 or speed > 100:
            return False

        node = self.FAN_DUTY_PATH
        speed = int(round(speed * 255.0 / 100))
        try:
            with open(node, 'w') as fan_duty:
                fan_duty.write(str(speed))
        except IOError:
            return False
        return True

    def get_speed_tolerance(self):
        """
        Retrieves the speed tolerance of the fan

        Returns:
            An integer, the percentage of variance from target speed which is
                 considered tolerable
        """        
        return self.FAN_SPEED_TOLERANCE_PERCENTAGE

    def set_status_led(self, color):
        """
        Sets the state of the fan module status LED

        Args:
            color: A string representing the color with which to set the
                   fan module status LED

        Returns:
            bool: True if status LED state is set successfully, False if not
        """
        from .chassis import Chassis
        fanled = Chassis.get_fanled()
        return fanled.update_status()

    def get_status_led(self):
        """
        Gets the state of the fan status LED

        Returns:
            A string, one of the predefined STATUS_LED_COLOR_* strings above
        """
        from .chassis import Chassis
        fanled = Chassis.get_fanled()
        return fanled.get_status()
