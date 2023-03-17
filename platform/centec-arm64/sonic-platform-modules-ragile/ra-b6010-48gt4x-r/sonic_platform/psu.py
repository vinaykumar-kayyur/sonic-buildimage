#!/usr/bin/env python

import time
import imp
import os

try:
    from sonic_platform_base.psu_base import PsuBase
    from sonic_py_common import device_info
    from .redfish_api import Redfish_Api
except ImportError as e:
    raise ImportError("%s - required module not found" % e)

class Psu(PsuBase):
    """Platform-specific Psu class"""

    def __init__(self, index=0):
        PsuBase.__init__(self)
        self.redfish = Redfish_Api()
        self.pinf = self.redfish.get_power()
        self.psu_index = index
        self._fan_list = []
        self._thermal_list = []
        self.begin = time.time()

    def get_power_3s(self):
        self.elapsed = time.time()
        if self.elapsed - self.begin < 3:
            pass
        else:
            self.pinf = self.redfish.get_power()
        self.begin = time.time()

    def get_presence(self):
        return True

    def get_powergood_status(self):
        self.get_power_3s()
        ctrl = self.pinf["PowerSupplies"]
        output = ctrl[self.psu_index]
        if output.get("Status").get("Health") == "OK":
            return True
        else:
            return False

    def get_serial(self):
        self.get_power_3s()
        ctrl = self.pinf["PowerSupplies"]
        output = ctrl[self.psu_index]
        serial = output.get("SerialNumber")
        return serial

    def get_model(self):
        self.get_power_3s()
        ctrl = self.pinf["PowerSupplies"]
        output = ctrl[self.psu_index]
        model = output.get("Model")
        return model

    def get_revision(self):
        self.get_power_3s()
        ctrl = self.pinf["PowerSupplies"]
        output = ctrl[self.psu_index]
        manufacturer = output.get("Manufacturer")
        return manufacturer

    def get_voltage(self):
        self.get_power_3s()
        ctrl = self.pinf["PowerSupplies"]
        output = ctrl[self.psu_index]
        voltage = output.get("Oem").get("Ragile").get("OutputVoltage")
        return voltage

    def get_input_current(self):
        self.get_power_3s()
        ctrl = self.pinf["PowerSupplies"]
        output = ctrl[self.psu_index]
        current = output.get("Oem").get("Ragile").get("OutputAmperage")
        return current

    def get_input_voltage(self):
        self.get_power_3s()
        ctrl = self.pinf["PowerSupplies"]
        output = ctrl[self.psu_index]
        voltage = output.get("Oem").get("Ragile").get("OutputVoltage")
        return voltage

    def get_current(self):
        self.get_power_3s()
        ctrl = self.pinf["PowerSupplies"]
        output = ctrl[self.psu_index]
        current = output.get("Oem").get("Ragile").get("OutputAmperage")
        return current

    def get_power(self):
        self.get_power_3s()
        ctrl = self.pinf["PowerSupplies"]
        output = ctrl[self.psu_index]
        current = output.get("Oem").get("Ragile").get("OutputAmperage")
        voltage = output.get("Oem").get("Ragile").get("OutputVoltage")
        power = float(current)*float(voltage)
        return round(power,2)

    def get_temperature(self):
        return None

    def get_status_led(self):
        return "BuildIn"
        self.get_power_3s()
        ctrl = self.pinf["PowerSupplies"]
        output = ctrl[self.psu_index]
        led = output.get("Oem").get("Ragile").get("IndicatorLEDColor")
        return led

    def set_status_led(self, color):
        playload = {}
        led = {}
        led_list = []
        led["IndicatorLEDColor"] = color
        led["LEDType"] = "pwr"
        led_list.append(led)
        playload["LEDs"] = led_list
        # boardsLed
        return self.redfish.post_boardLed(playload)
