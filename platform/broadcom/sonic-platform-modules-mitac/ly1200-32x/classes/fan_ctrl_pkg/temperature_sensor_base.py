#! /usr/bin/env python
# coding:utf-8

import abc


class TempSensorBase:
    """ Base class for TemperatureSensor """

    __metaclass__ = abc.ABCMeta
 
    name = " "
    get_temp_cmd = " "
    max_temp = 0

    @abc.abstractmethod
    def get_temp(self):
        """ Get sensor temperature """
        pass

    @abc.abstractmethod
    def get_pwm(self, temperature, fan_zone_thermal):
        """ Get the fan speed """
        pass
    
    @abc.abstractmethod
    def hysteresis(self, cur_pwm, fan_zone, fan_zone_thermal):
        """ Determine whether the sensor temperature is lower than
        the hysteresis temperature to reduce the fan speed. """
        pass
