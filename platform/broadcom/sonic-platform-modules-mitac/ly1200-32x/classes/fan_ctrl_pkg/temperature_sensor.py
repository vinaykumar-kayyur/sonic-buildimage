#! /usr/bin/env python
# coding:utf-8

try:
    import subprocess
    from .temperature_sensor_base import TempSensorBase as Base
    from .fan_utility import *
except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))

class TemperatureSensor(Base):
    """ TemperatureSensor class for fan utility """

    def __init__(self, temp_name, fan_zone):
        self.name = temp_name
        self.get_temp_cmd = fan_zone[temp_name]['cmd']
        self.max_temp = fan_zone[temp_name]['max_temp']
        self.zone_id = fan_zone['ZONE_ID']
        self.status = 'GOOD'

    @property
    def get_temp(self):

        msg_header = "[ZONE_%d] Sensor %s" % (self.zone_id, self.name)
        cmd = self.get_temp_cmd + " 2>/dev/null"
        try:
            temperature = subprocess.check_output(["/bin/bash", "-c", cmd]).strip()
            if self.status == 'FAULT':
                WARN("%s: status=RECOVER. reason=temperature is %s deg C." % (msg_header, temperature))

            self.status = 'GOOD'
            return float(temperature)
        except (ValueError, subprocess.CalledProcessError) as e:
            if self.status == 'GOOD':
                WARN("%s: status=ERROR. reason=read sensor failed." % msg_header)

            self.status = 'FAULT'
            return float(self.max_temp)

    def get_pwm(self, temperature, fan_zone_thermal):

        pwm = max(fan_zone_thermal['PWM'])
        for i in range(len(list(fan_zone_thermal[self.name]))):
            if temperature < fan_zone_thermal[self.name][i][0]:
                pwm = fan_zone_thermal[self.name][i][1]
                break
        return pwm

    def hysteresis(self, cur_pwm, temperature, fan_zone_thermal):

        pre_pwm = fan_zone_thermal[str(cur_pwm)]['PRE_PWM']
        if temperature <= (fan_zone_thermal[str(pre_pwm)][self.name] - 2):
            return True
        else:
            return False
