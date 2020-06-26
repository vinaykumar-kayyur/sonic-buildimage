#!/usr/bin/env python

#############################################################################
# Celestica
#
# Module contains an implementation of SONiC Platform Base API and
# provides the fan status which are available in the platform
#
#############################################################################

import json
import math
import os.path
import inspect

try:
    from sonic_platform_base.fan_base import FanBase
    from common import Common
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class Fan(FanBase):
    """Platform-specific Fan class"""

    def __init__(self, index, drawer_index, is_psu_fan=False, psu_index=0, conf=None):
        FanBase.__init__(self)

        self.fan_index = index
        self.drawer_index = drawer_index

        self._config = conf
        self._api_common = Common()
        self._name = self.get_name()
        self._is_psu_fan = is_psu_fan

        # self.is_psu_fan = is_psu_fan
        # if self.is_psu_fan:
        #     self.psu_index = psu_index
        #     self.psu_i2c_num = PSU_I2C_MAPPING[self.psu_index]["num"]
        #     self.psu_i2c_addr = PSU_I2C_MAPPING[self.psu_index]["addr"]
        #     self.psu_hwmon_path = PSU_HWMON_PATH.format(
        #         self.psu_i2c_num, self.psu_i2c_addr)

    def get_direction(self):
        """
        Retrieves the direction of fan
        Returns:
            A string, either FAN_DIRECTION_INTAKE or FAN_DIRECTION_EXHAUST
            depending on fan direction
        """
        direction = self.FAN_DIRECTION_NOT_APPLICABLE
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)

        if self.get_presence() and config.get('oper_type') == Common.OPER_IMPI:
            cmd = config['command'][self.fan_index]
            full_cmd = config['template'].format(
                config['command'][self.fan_index])
            status, result = self._api_common.run_command(full_cmd)
            direction = eval(config['formula'].format(
                result)) if status else direction

        return direction

    def get_speed(self):
        """
        Retrieves the speed of fan as a percentage of full speed
        Returns:
            An integer, the percentage of full fan speed, in the range 0 (off)
                 to 100 (full speed)

        Note:
            speed = pwm_in/255*100
        """
        speed = 0
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)

        if self._is_psu_fan:
            pass
        elif self.get_presence():
            if config.get('oper_type') == Common.OPER_IMPI:
                max_rpm = config['max_rear'] if 'R' in self._name else config['max_front']
                cmd = config['command'][self.fan_index]
                full_cmd = config['template'].format(
                    config['command'][self.fan_index])
                status, result = self._api_common.run_command(full_cmd)
                speed_raw = eval(config['formula'].format(
                    result)) if status else speed
                speed = float(speed_raw) / max_rpm * 100.0

        return int(speed)

    def get_target_speed(self):
        """
        Retrieves the target (expected) speed of the fan
        Returns:
            An integer, the percentage of full fan speed, in the range 0 (off)
                 to 100 (full speed)

        Note:
            0   : when PWM mode is not in use
            pwm : when pwm mode is not use
        """
        target_speed = Common.NULL_VAL
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)

        if config.get('oper_type') == Common.OPER_FIXED:
            target_speed = config["value"]

        return target_speed

    def get_speed_tolerance(self):
        """
        Retrieves the speed tolerance of the fan
        Returns:
            An integer, the percentage of variance from target speed which is
                 considered tolerable
        """
        speed_tolerance = Common.NULL_VAL
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)

        if config.get('oper_type') == Common.OPER_FIXED:
            speed_tolerance = config["value"]

        return speed_tolerance

    # def set_speed(self, speed):
    #     """
    #     Sets the fan speed
    #     Args:
    #         speed: An integer, the percentage of full fan speed to set fan to,
    #                in the range 0 (off) to 100 (full speed)
    #     Returns:
    #         A boolean, True if speed is set successfully, False if not

    #     Note:
    #         Depends on pwm or target mode is selected:
    #         1) pwm = speed_pc * 255             <-- Currently use this mode.
    #         2) target_pwm = speed_pc * 100 / 255
    #          2.1) set pwm{}_enable to 3

    #     """
    #     pwm = speed * 255 / 100
    #     if not self.is_psu_fan and self.get_presence():
    #         chip = self.emc2305_chip_mapping[self.fan_index]
    #         device = chip['device']
    #         fan_index = chip['index_map']
    #         sysfs_path = "%s%s/%s" % (
    #             EMC2305_PATH, device, EMC2305_FAN_PWM)
    #         sysfs_path = sysfs_path.format(fan_index[self.drawer_index])
    #         return self.__write_txt_file(sysfs_path, int(pwm))

    #     return False

    # def set_status_led(self, color):
    #     """
    #     Sets the state of the fan module status LED
    #     Args:
    #         color: A string representing the color with which to set the
    #                fan module status LED
    #     Returns:
    #         bool: True if status LED state is set successfully, False if not
    #     """
    #     set_status_led = False
    #     if not self.is_psu_fan:
    #         s1, s2 = False, False
    #         try:
    #             if color == self.STATUS_LED_COLOR_GREEN:
    #                 s1 = self.__set_gpio_value(
    #                     self.dx010_fan_gpio[self.drawer_index+1]['color']['red'], 1)
    #                 s2 = self.__set_gpio_value(
    #                     self.dx010_fan_gpio[self.drawer_index+1]['color']['green'], 0)

    #             elif color == self.STATUS_LED_COLOR_RED:
    #                 s1 = self.__set_gpio_value(
    #                     self.dx010_fan_gpio[self.drawer_index+1]['color']['red'], 0)
    #                 s2 = self.__set_gpio_value(
    #                     self.dx010_fan_gpio[self.drawer_index+1]['color']['green'], 1)

    #             elif color == self.STATUS_LED_COLOR_OFF:
    #                 s1 = self.__set_gpio_value(
    #                     self.dx010_fan_gpio[self.drawer_index+1]['color']['red'], 1)
    #                 s2 = self.__set_gpio_value(
    #                     self.dx010_fan_gpio[self.drawer_index+1]['color']['green'], 1)
    #             set_status_led = s1 and s2
    #             return set_status_led
    #         except IOError:
    #             return False

    #     return set_status_led

    def get_name(self):
        """
        Retrieves the name of the device
            Returns:
            string: The name of the device
        """
        name = Common.NULL_VAL
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)

        if config.get('oper_type') == Common.OPER_FIXED_LIST:
            name = config["value"][self.fan_index]

        return name

    def get_presence(self):
        """
        Retrieves the presence of the FAN
        Returns:
            bool: True if FAN is present, False if not
        """
        present = False
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)

        if config.get('oper_type') == Common.OPER_IMPI:
            cmd = config['command'][self.fan_index]
            full_cmd = config['template'].format(
                config['command'][self.fan_index])
            status, result = self._api_common.run_command(full_cmd)
            present = eval(config['formula'].format(
                result)) if status else present

        return present

    def get_model(self):
        """
        Retrieves the model number (or part number) of the device
        Returns:
            string: Model/part number of device
        """
        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)
        model = Common.NULL_VAL

        if self.get_presence() and config.get('oper_type') == Common.OPER_IMPI:
            cmd = config['command'][self.fan_index]
            full_cmd = config['template'].format(
                config['command'][self.fan_index])
            status, result = self._api_common.run_command(full_cmd)
            model = eval(config['formula'].format(
                result)) if status else model

        return model

    def get_serial(self):
        """
        Retrieves the serial number of the device
        Returns:
            string: Serial number of device
        """
        # if self.is_psu_fan:
        #     return NULL_VAL

        f_name = inspect.stack()[0][3]
        config = self._config.get(f_name)
        serial = Common.NULL_VAL

        if self.get_presence() and config.get('oper_type') == Common.OPER_IMPI:
            cmd = config['command'][self.fan_index]
            full_cmd = config['template'].format(
                config['command'][self.fan_index])
            status, result = self._api_common.run_command(full_cmd)
            serial = eval(config['formula'].format(
                result)) if status else serial

        return serial

    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        return self.get_presence() and self.get_speed() > 10
