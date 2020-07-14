#!/usr/bin/env python
#
# led_control.py
# 
# Platform-specific LED control functionality for SONiC
#

# try:
#     from sonic_led.led_control_base import LedControlBase
#     import swsssdk
# except ImportError, e:
#     raise ImportError (str(e) + " - required module not found")

import time
import glob
import os.path

class LedControlBase(object):
#    __metaclass__ = abc.ABCMeta

#    @abc.abstractmethod
    def port_link_state_change(self, port, state):
        """
        Called when port link state changes. Update port link state LED here.

        :param port: A string, SONiC port name (e.g., "Ethernet0")
        :param state: A string, the port link state (either "up" or "down")
        """
        return

### Goreme specified ###
read_fan_fault = 0
is_fan_all_OK = 0
read_power_status = 0
is_power_all_OK = 0
is_thermal_high = 0
is_reset_button_push = 0
##########################

def sysled_task():
    while True:
        system_led_check()
        time.sleep(5)
        
########## Goreme System LED checking
def system_led_check():
    global read_fan_fault, read_power_status, is_fan_all_OK, is_power_all_OK, is_thermal_high, is_reset_button_push
    is_fan_all_OK = 1
    is_power_all_OK = 0
    is_thermal_high = 0
    is_reset_button_push = 0

    with open("/sys/bus/i2c/devices/0-005e/fan1_led", "r") as f11:
        read_fan_led = int(f11.read())
        if read_fan_led == 1:
            is_fan_all_OK = 1
        else:
            is_fan_all_OK = 0

    with open("/sys/bus/i2c/devices/0-005e/sys_pwr", "r") as f11:
        read_pau_led = int(f11.read())
        if read_pau_led == 1:
            is_power_all_OK = 1
        else:
            is_power_all_OK = 0

    if os.path.exists("/sys/bus/i2c/devices/3-004d/hwmon/"):
        with open("/sys/bus/i2c/devices/3-004d/hwmon/hwmon2/temp1_input", "r") as f3:
            is_thermal_high = f3.read()
            if int(is_thermal_high) >= 70000:
                is_thermal_high = 1
            else:
                is_thermal_high = 0
    else:
        node = glob.glob("/sys/bus/i2c/devices/18-004d/hwmon/hwmon*")
        node = node[0] + "/temp1_input"
        with open(node, "r") as f3:
            is_thermal_high = f3.read()
            if int(is_thermal_high) >= 70000:
                is_thermal_high = 1
            else:
                is_thermal_high = 0

    with open("/sys/bus/i2c/devices/0-005e/sys_status", "w") as f2:
        if is_reset_button_push == 1:
            f2.write("3")
        elif is_fan_all_OK == 0 or is_power_all_OK == 0 or is_thermal_high == 1:
            f2.write("4")
        else:
            f2.write("1")

    return
##########
    
        
class LedControl(LedControlBase):
    """Platform specific LED control class"""

    # Constructor
    def __init__(self):
        # Initialize all front-panel status LEDs to green
        with open("/sys/bus/i2c/devices/0-005e/sys_locator", "w") as f:
            f.write("1")
        with open("/sys/bus/i2c/devices/0-005e/sys_status", "w") as f:
            f.write("1")

        sysled_task()    

        # Initialize: Turn all front panel QSFP LEDs off
        # # for qsfp_index in range(self.QSFP_BREAKOUT_START_IDX, self.QSFP_BREAKOUT_END_IDX + 1):
        # #     for lane in range(1, 5):
        # #         led_sysfs_path = self.LED_SYSFS_PATH_BREAKOUT_CAPABLE.format(qsfp_index, lane)
        # #         with open(led_sysfs_path, 'w') as led_file:
        # #             led_file.write("%d" % self.LED_COLOR_OFF)

        # # for qsfp_index in range(self.QSFP_NO_BREAKOUT_START_IDX, self.QSFP_NO_BREAKOUT_END_IDX + 1):
        # #     led_sysfs_path = self.LED_SYSFS_PATH_NO_BREAKOUT.format(qsfp_index)
        # #     with open(led_sysfs_path, 'w') as led_file:
        # #         led_file.write("%d" % self.LED_COLOR_OFF)
