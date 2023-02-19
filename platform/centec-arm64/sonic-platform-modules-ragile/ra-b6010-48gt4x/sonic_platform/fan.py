#!/usr/bin/env python

import json
import math
import os.path
import time

try:
    from sonic_platform_base.fan_base import FanBase
    from .redfish_api import Redfish_Api
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

FAN_NAME_LIST = ["Fan1", "Fan2"]

class Fan(FanBase):
    """Platform-specific Fan class"""

    def __init__(self, fan_tray_index, fan_index=0):
        self.fan_index = fan_index
        self.fan_tray_index = fan_tray_index
        self.redfish = Redfish_Api()
        self.pinf = self.redfish.get_thermal()
        self._fan_list = []
        FanBase.__init__(self)
        self.begin = time.time()

    def get_power_3s(self):
        self.elapsed = time.time()
        if self.elapsed - self.begin < 3:
            pass
        else:
            self.pinf = self.redfish.get_thermal()
        self.begin = time.time()

    def get_speed_pwm(self):
        self.get_power_3s()
        ctrl = self.pinf["Fans"]
        output = ctrl[self.fan_index]
        speed = output.get("Oem").get("Ragile").get("FanSpeedLevelPercents")
        return int(speed)

    def get_speed_rpm(self):
        self.get_power_3s()
        ctrl = self.pinf["Fans"]
        output = ctrl[self.fan_index]
        speed = output.get("Reading")
        return int(speed)

    def get_high_critical_threshold(self):
        self.get_power_3s()
        ctrl = self.pinf["Fans"]
        output = ctrl[self.fan_index]
        high = output.get("UpperThresholdFatal")
        return int(high)

    def get_low_critical_threshold(self):
        self.get_power_3s()
        ctrl = self.pinf["Fans"]
        output = ctrl[self.fan_index]
        low = output.get("LowerThresholdFatal")
        return int(low)

    def set_speed_pwm(self, speed):
        post_url = '/redfish/v1/Chassis/1/Thermal/Actions/Oem/Ragile/Fan.SetSpeed'
        playload = {}
        playload["FanName"] = "Fan0"
        playload["FanSpeedLevelPercents"] = str(speed)
        return self.redfish.post_odata(post_url, playload)

    def get_status_led(self):
        self.get_power_3s()
        ctrl = self.pinf["Fans"]
        output = ctrl[self.fan_index]
        led = output.get("Oem").get("Ragile").get("IndicatorLEDColor")
        return led

    def set_status_led(self, color):
        playload = {}
        led = {}
        led_list = []
        led["IndicatorLEDColor"] = color
        led["LEDType"] = "fan"
        led_list.append(led)
        playload["LEDs"] = led_list
        # boardsLed
        return self.redfish.post_boardLed(playload)

    def get_direction(self):
        self.get_power_3s()
        ctrl = self.pinf["Fans"]
        output = ctrl[self.fan_index]
        airflow = output.get("Oem").get("Ragile").get("AirFlow")
        return airflow

    def get_name(self):
        fan_name = FAN_NAME_LIST[self.fan_index]
        return "Fantray{}_{}".format(self.fan_tray_index, fan_name)

    def get_presence(self):
        self.get_power_3s()
        ctrl = self.pinf["Fans"]
        output = ctrl[self.fan_index]
        if output.get("Status").get("Status").get("State") == "Enabled":
            return True
        return False

    def get_status(self):
        self.get_power_3s()
        ctrl = self.pinf["Fans"]
        output = ctrl[self.fan_index]
        if output.get("Status").get("Status").get("Health") == "OK":
            return True
        return False

    def get_high_critical_threshold(self):
        self.get_power_3s()
        ctrl = self.pinf["Fans"]
        output = ctrl[self.fan_index]
        high = output.get("UpperThresholdFatal")
        return high

    def get_low_critical_threshold(self):
        self.get_power_3s()
        ctrl = self.pinf["Fans"]
        output = ctrl[self.fan_index]
        low = output.get("LowerThresholdFatal")
        return low

    def get_speed(self):
        self.get_power_3s()
        ctrl = self.pinf["Fans"]
        output = ctrl[self.fan_index]
        speed = output.get("Oem").get("Ragile").get("FanSpeedLevelPercents")
        return speed
