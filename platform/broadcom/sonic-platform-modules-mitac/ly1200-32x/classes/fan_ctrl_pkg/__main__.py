#! /usr/bin/env python
# coding:utf-8

try:
    import time
    from .temperature_sensor import TemperatureSensor
    from .fan_utility import *
except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))


def main(zone_conf, temp_conf, log_file, debug_mode, simulate_mode):

    fan_util = FanUtility(zone_conf, temp_conf, log_file, debug_mode, simulate_mode)

    fan_util.validate_configuration()

    fan_util.dump_runtime_info()

    INFO("Starting fan control service...")

    sensor_instance = [(TemperatureSensor(name, fan_util.fan_zone)) for name in fan_util.fan_zone['TEMP_LIST']]

    while True:
        pwm = []
        temp = {}

        for instance in sensor_instance:
            temp[instance.name] = instance.get_temp
            pwm.append(instance.get_pwm(temp[instance.name], fan_util.fan_zone_thermal))

        current_pwm = fan_util.pwm_value
        new_pwm = max(pwm)
        
        apply_pwm = True
        if new_pwm < current_pwm:
            for instance in sensor_instance:
                if not instance.hysteresis(current_pwm, temp[instance.name], fan_util.fan_zone_thermal):
                    apply_pwm = False
                    break
            if apply_pwm:
                fan_util.pwm_value = new_pwm

        elif new_pwm > current_pwm:
            fan_util.pwm_value = new_pwm

        fan_util.dump_runtime_info(temp, new_pwm if apply_pwm else current_pwm)
        time.sleep(fan_util.fan_zone['INTERVAL'])
