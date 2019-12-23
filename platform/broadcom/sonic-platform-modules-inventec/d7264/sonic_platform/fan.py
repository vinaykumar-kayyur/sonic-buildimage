#!/usr/bin/env python

#############################################################################
# Inventec d7264
#
# Module contains an implementation of SONiC Platform Base API and
# provides the FAN information
#
# version: 1.0
#############################################################################

try:
    import os
    import math
    from sonic_platform_base.fan_base import FanBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


###############
# Global
###############
HWMON_PATH      = "/sys/class/hwmon/hwmon2/"

class Fan(FanBase):
    """Platform-specific Fan class"""

    def __init__(self, index, is_psu_fan=False):
        self.is_psu_fan = is_psu_fan

        if self.is_psu_fan:
            self.psu_index                      = index + 1
            self.psu_fan_pwm                    = "pwm_psu{}".format(self.psu_index)
            self.psu_fan_rpm                    = "rpm_psu{}".format(self.psu_index)
        else:
            self.fan_index                      = index + 1
            self.fan_pwm                        = "pwm{}".format(self.fan_index)
            self.fan_status_led_green_color     = "fan_led_grn{}".format(self.fan_index)
            self.fan_status_led_red_color       = "fan_led_red{}".format(self.fan_index)
            self.fan_front_rpm                  = "fan{}_input".format(self.fan_index * 2 - 1)
            self.fan_rear_rpm                   = "fan{}_input".format(self.fan_index * 2)
            self.fan_gpi                        = "fan_gpi"


#######################
# private function
#######################

    def __get_attr_value(self, attr_path):

        retval = 'ERR'
        if (not os.path.isfile(attr_path)):
            return retval

        try:
            with open(attr_path, 'r') as fd:
                retval = fd.read()
        except Exception as error:
            logging.error("Unable to open ", attr_path, " file !")

        retval = retval.rstrip(' \t\n\r')
        return retval


    ####################
    # Device base
    ####################

    def get_name(self):
        """
        Retrieves the name of the device

        Returns:
            string: The name of the device
        """
        if self.is_psu_fan:
            return "PSU-{}_FAN".format(self.psu_index)
        else:
            return "FAN-{}".format(self.fan_index)

    def get_presence(self):
        """
        Retrieves the presence of the device

        Returns:
            bool: True if device is present, False if not

        Note:
            fan_gpi define 8 bits
            low byte means fan presense
            high byte means fan direction
        """
        if self.is_psu_fan:
            return True

        presence = False
        attr_path = HWMON_PATH + self.fan_gpi

        attr_rv = self.__get_attr_value(attr_path)
        if (attr_rv != 'ERR'):
            not_presence_bit = 1 << (self.fan_index - 1)
            if not (int(attr_rv, 16) & not_presence_bit):
                presence = True

        return presence

    def get_model(self):
        """
        Retrieves the model number (or part number) of the device

        Returns:
            string: Model/part number of device
        """
        raise NotImplementedError

    def get_serial(self):
        """
        Retrieves the serial number of the device

        Returns:
            string: Serial number of device
        """
        raise NotImplementedError

    def get_status(self):
        """
        Retrieves the operational status of the device

        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        status = False

        if self.is_psu_fan:
            attr_path_1 = HWMON_PATH + self.psu_fan_rpm
            attr_path_2 = HWMON_PATH + self.psu_fan_rpm
        else:
            attr_path_1 = HWMON_PATH + self.fan_front_rpm
            attr_path_2 = HWMON_PATH + self.fan_rear_rpm

        attr_rv_1 = self.__get_attr_value(attr_path_1)
        attr_rv_2 = self.__get_attr_value(attr_path_2)
        if (attr_rv_1 != 'ERR' and attr_rv_2 != 'ERR'):
            if (attr_rv_1 > 0 and attr_rv_2 > 0):
                status = True

        return status


    #################
    # fan base
    #################

    def get_direction(self):
        """
        Retrieves the direction of fan

        Returns:
            A string, either FAN_DIRECTION_INTAKE or FAN_DIRECTION_EXHAUST
            depending on fan direction

        Note:
            fan_gpi define 8 bits
            low byte means fan presense
            high byte means fan direction
        """
        if self.is_psu_fan:
            return "unknown"

        direction = self.FAN_DIRECTION_INTAKE
        attr_path = HWMON_PATH + self.fan_gpi

        attr_rv = self.__get_attr_value(attr_path)
        if (attr_rv != 'ERR'):
            attr_rv = int(attr_rv,16) >> 4
            direction_bit = 1 << (self.fan_index - 1)
            if (attr_rv & direction_bit):
                direction = self.FAN_DIRECTION_EXHAUST

        return direction

    def get_speed(self):
        """
        Retrieves the speed of fan as a percentage of full speed

        Returns:
            An integer, the percentage of full fan speed, in the range 0 (off)
                 to 100 (full speed)
        """
        pwm = 0
        pwm_range = 255  #0-255
        speed = 0

        if self.is_psu_fan:
            attr_path = HWMON_PATH + self.psu_fan_pwm
        else:
            attr_path = HWMON_PATH + self.fan_pwm

        attr_rv = self.__get_attr_value(attr_path)
        if (attr_rv != 'ERR'):
            pwm = int(attr_rv)
            speed = math.ceil(float(pwm * 100 / pwm_range))

        return int(speed)

    def get_target_speed(self):
        """
        Retrieves the target (expected) speed of the fan

        Returns:
            An integer, the percentage of full fan speed, in the range 0 (off)
                 to 100 (full speed)
        """
        raise NotImplementedError

    def get_speed_tolerance(self):
        """
        Retrieves the speed tolerance of the fan

        Returns:
            An integer, the percentage of variance from target speed which is
                 considered tolerable
        """
        raise NotImplementedError

    def set_speed(self, speed):
        """
        Sets the fan speed

        Args:
            speed: An integer, the percentage of full fan speed to set fan to,
                   in the range 0 (off) to 100 (full speed)

        Returns:
            A boolean, True if speed is set successfully, False if not
        """
        raise NotImplementedError

    def set_status_led(self, color):
        """
        Sets the state of the fan module status LED

        Args:
            color: A string representing the color with which to set the
                   fan module status LED

        Returns:
            bool: True if status LED state is set successfully, False if not
        """
        raise NotImplementedError

    def get_status_led(self):
        """
        Gets the state of the fan status LED

        Returns:
            A string, one of the predefined STATUS_LED_COLOR_* strings above
        """
        if self.is_psu_fan:
            return "unknown"

        on = "1"
        attr_grn_path = HWMON_PATH + self.fan_status_led_green_color
        attr_red_path = HWMON_PATH + self.fan_status_led_red_color

        attr_grn_rv = self.__get_attr_value(attr_grn_path)
        attr_red_rv = self.__get_attr_value(attr_red_path)
        if (attr_grn_rv != 'ERR' and attr_red_rv != 'ERR'):
            if (attr_grn_rv == on):
                return self.STATUS_LED_COLOR_GREEN
            elif (attr_red_rv == on):
                return self.STATUS_LED_COLOR_RED
            else:
                return self.STATUS_LED_COLOR_OFF
