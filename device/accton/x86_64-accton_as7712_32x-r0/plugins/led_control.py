#!/usr/bin/env python
#
# led_control.py
# 
# Platform-specific LED control functionality for SONiC
#

try:
    from sonic_led.led_control_base import LedControlBase
except ImportError, e:
    raise ImportError (str(e) + " - required module not found")


class LedControl(LedControlBase):
    """Platform specific LED control class"""

    SONIC_PORT_NAME_PREFIX = "Ethernet"

    LED_SYSFS_PATH = "/sys/bus/platform/devices/accton_as7712_32x_led/leds/accton_as7712_32x_led::port{0}_led{1}/brightness"

    QSFP_START_IDX = 0
    QSFP_END_IDX = 31

    LED_COLOR_OFF = 0
    LED_COLOR_GREEN = 16
    LED_COLOR_YELLOW = 14

    def _port_name_to_qsfp_index(self, port_name):
        # Strip "Ethernet" off port name
        if not port_name.startswith(self.SONIC_PORT_NAME_PREFIX):
            return -1

        sonic_port_num = int(port_name[len(self.SONIC_PORT_NAME_PREFIX):])

        # SONiC port nums are 0-based and increment by 4
        return ((sonic_port_num/4) + 0)

    # Concrete implementation of port_link_state_change() method
    def port_link_state_change(self, port, state):
        qsfp_index = self._port_name_to_qsfp_index(port)
        
        # Ignore invalid QSFP indices
        if not (self.QSFP_START_IDX <= qsfp_index <= self.QSFP_END_IDX):
            return
        # Light all 4 lanes for non-breakout
        led_sysfs_paths = [ self.LED_SYSFS_PATH.format(qsfp_index, 0), 
        		self.LED_SYSFS_PATH.format(qsfp_index, 1),
        		self.LED_SYSFS_PATH.format(qsfp_index, 2),
        		self.LED_SYSFS_PATH.format(qsfp_index, 3) ]

        for led_sysfs_path in led_sysfs_paths:
            led_file = open(led_sysfs_path, "w")
            if state == "up":
                led_file.write("%d" % self.LED_COLOR_GREEN)
            else:
                led_file.write("%d" % self.LED_COLOR_OFF)

            led_file.close()

    # Constructor
    def __init__(self):
        # Initialize: Turn all front panel QSFP LEDs off
        for qsfp_index in range(self.QSFP_START_IDX, self.QSFP_END_IDX + 1):
            for lane in range(0, 4):
                led_sysfs_path = self.LED_SYSFS_PATH.format(qsfp_index, lane)
                with open(led_sysfs_path, 'w') as led_file:
                    led_file.write("%d" % self.LED_COLOR_OFF)


