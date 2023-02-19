#!/usr/bin/env python

import json
import math
import os.path
import time

try:
    from sonic_platform_base.fan_drawer_base import FanDrawerBase
    from sonic_platform.fan import Fan
    from .redfish_api import Redfish_Api
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class FanDrawer(FanDrawerBase):

    FANS_PER_FANTRAY = 2

    def __init__(self, fantray_index=0):
        FanDrawerBase.__init__(self)
        self.fantrayindex = fantray_index
        self.redfish = Redfish_Api()
        self.pinf = self.redfish.get_thermal()
        self.begin = time.time()
        for i in range(self.FANS_PER_FANTRAY):
            self._fan_list.append(Fan(fantray_index, i))

    def get_power_3s(self):
        self.elapsed = time.time()
        if self.elapsed - self.begin < 3:
            pass
        else:
            self.pinf = self.redfish.get_thermal()
        self.begin = time.time()

    def get_name(self):
        return "FanTray{}".format(self.fantrayindex)

    def get_presence(self):
        self.get_power_3s()
        ctrl = self.pinf["Fans"]
        output = ctrl[self.fantrayindex]
        if output.get("Status").get("Status").get("State") == "Enabled":
            return True

    def get_status(self):
        self.get_power_3s()
        ctrl = self.pinf["Fans"]
        output = ctrl[self.fantrayindex]
        if output.get("Status").get("Status").get("Health") == "OK":
            return True

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

