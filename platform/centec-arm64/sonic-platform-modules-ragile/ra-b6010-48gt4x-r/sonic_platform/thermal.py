#!/usr/bin/env python

import os
import re
import os.path
import time

try:
    from sonic_platform_base.thermal_base import ThermalBase
    from .redfish_api import Redfish_Api
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class Thermal(ThermalBase):
    """Platform-specific Thermal class"""

    def __init__(self, thermal_index):
        ThermalBase.__init__(self)
        self.index = thermal_index
        self.high_threshold = float(112)
        self.redfish = Redfish_Api()
        pinf = self.redfish.get_thermal()
        self.begin = time.time()

    def get_power_3s(self):
        self.elapsed = time.time()
        if self.elapsed - self.begin < 3:
            pass
        else:
            self.pinf = self.redfish.get_thermal()
        self.begin = time.time()

    def get_temperature(self):
        self.get_power_3s()
        ctrl = self.pinf["Temperatures"]
        output = ctrl[self.index]
        temp = output.get("ReadingCelsius")
        return temp

    def get_high_threshold(self):
        self.get_power_3s()
        ctrl = self.pinf["Temperatures"]
        output = ctrl[self.index]
        temp = output.get("UpperThresholdFatal")
        return temp

    def get_low_threshold(self):
        self.get_power_3s()
        ctrl = self.pinf["Temperatures"]
        output = ctrl[self.index]
        temp = output.get("LowerThresholdFatal")
        return temp

    def get_high_critical_threshold(self):
        self.get_power_3s()
        ctrl = self.pinf["Temperatures"]
        output = ctrl[self.index]
        temp = output.get("UpperThresholdFatal")
        return temp

    def get_low_critical_threshold(self):
        self.get_power_3s()
        ctrl = self.pinf["Temperatures"]
        output = ctrl[self.index]
        temp = output.get("LowerThresholdFatal")
        return temp

    def get_name(self):
        self.get_power_3s()
        ctrl = self.pinf["Temperatures"]
        output = ctrl[self.index].get("Name")
        name = output.split("/",3)[2]
        return "{}".format(name)

    def get_presence(self):
        self.get_power_3s()
        ctrl = self.pinf["Temperatures"]
        output = ctrl[self.index]
        if output.get("Status").get("Status").get("State") == "Enabled":
            return True

    def get_status(self):
        self.get_power_3s()
        ctrl = self.pinf["Temperatures"]
        output = ctrl[self.index]
        if output.get("Status").get("Health") == "OK":
            return True

    def set_sys_led(self, color):
        playload = {}
        led = {}
        led_list = []
        led["IndicatorLEDColor"] = color
        led["LEDType"] = "sys"
        led_list.append(led)
        playload["LEDs"] = led_list
        # boardsLed
        return self.redfish.post_boardLed(playload)
