#!/usr/bin/env python
#
# led_control.py
#
# Platform-specific LED control functionality for SONiC
#
try:
    from sonic_led.led_control_base import LedControlBase
    import swsssdk
    import threading
    import os
    import logging
    import struct
    import time
    from socket import *
    from select import *
    import sonic_platform.platform
    import sonic_platform.chassis
except ImportError, e:
    raise ImportError(str(e) + " - required module not found")
smbus_present = 1
try:
    import smbus
except ImportError, e:
    smbus_present = 0

class LedControl(LedControlBase):
    """Platform specific LED control class"""
    # Constructor
    def __init__(self):
        self.chassis = sonic_platform.platform.Platform().get_chassis()
        self._initDefaultConfig()

    def _initDefaultConfig(self):
        # For the D1 box the port leds are controlled by Trident3 LED program
        # The fan tray leds will be managed with the new thermalctl daemon / chassis class based API
        # leaving only the system leds to be done old style
        self._initSystemLed()

    def _initSystemLed(self):
        # Front Panel System LEDs setting
        fan_green=0x0
        fan_amber=0x0
        psu_green=0x0
        psu_amber=0x0
        Fan_green_led_gpio_path = "/sys/class/gpio/fanLedGreen"
        Fan_amber_led_gpio_path = "/sys/class/gpio/fanLedAmber"
        Psu_green_led_gpio_path = "/sys/class/gpio/psuLedGreen"
        Psu_amber_led_gpio_path = "/sys/class/gpio/psuLedAmber"

        # Write sys led
        if smbus_present == 0:
            print " PMON LED SET ERROR ->  smbus present = 0  "
        else:
            bus = smbus.SMBus(0)
            DEVICE_ADDRESS = 0x41
            DEVICEREG = 0x7
            bus.write_byte_data(DEVICE_ADDRESS, DEVICEREG, 0x02)

        while True:
            
            # Front Panel FAN Panel LED setting in register 0x08
            if ( self.chassis.get_fan(0).get_status() == self.chassis.get_fan(1).get_status()  == True ):
                if fan_amber == 0x1:
                    value=0
                    try:
                        gpio_file = open(Fan_amber_led_gpio_path +"/value", 'w')
                        gpio_file.write(str(value))
                        gpio_file.close()
                        fan_amber = 0x0
                    except IOError as e:
                        print "error: unable to open gpio fanLedAmper: %s" % str(e)

                value=1
                try:
                    gpio_file = open(Fan_green_led_gpio_path +"/value", 'w')
                    gpio_file.write(str(value))
                    gpio_file.close()
                    fan_green = 0x1
                except IOError as e:
                    print "error: unable to open gpio fanLedGreen: %s" % str(e)
            else:
                if fan_green == 0x1:
                    value=0
                    try:
                        gpio_file = open(Fan_green_led_gpio_path +"/value", 'w')
                        gpio_file.write(str(value))
                        gpio_file.close()
                        fan_green = 0x0
                    except IOError as e:
                        print "error: unable to open gpio fanLedGreen: %s" % str(e)
                    
                value=1
                try:
                    gpio_file = open(Fan_amber_led_gpio_path +"/value", 'w')
                    gpio_file.write(str(value))
                    gpio_file.close()
                    fan_amper = 0x1
                except IOError as e:
                    print "error: unable to open gpio fanLedAmper: %s" % str(e)
            
            
            # Front Panel PSU Panel LED setting in register 0x09
            if ( self.chassis.get_psu(0).get_status() == self.chassis.get_psu(1).get_status() == True ):
                if psu_amber == 0x1:
                    value=0
                    try:
                        gpio_file = open(Psu_amber_led_gpio_path +"/value", 'w')
                        gpio_file.write(str(value))
                        gpio_file.close()
                        psu_amber = 0x0
                    except IOError as e:
                        print "error: unable to open gpio psuLedAmber: %s" % str(e)
                value=1
                try:
                    gpio_file = open(Psu_green_led_gpio_path +"/value", 'w')
                    gpio_file.write(str(value))
                    gpio_file.close()
                    psu_green = 0x1
                except IOError as e:
                    print "error: unable to open gpio psuLedGreen: %s" % str(e)
            else:
                if  psu_green == 0x1:
                    value=0
                    try:
                        gpio_file = open(Psu_green_led_gpio_path +"/value", 'w')
                        gpio_file.write(str(value))
                        gpio_file.close()
                        psu_green = 0x0
                    except IOError as e:
                        print "error: unable to open gpio psuLedGreen: %s" % str(e)
                value=1
                try:
                    gpio_file = open(Psu_amber_led_gpio_path +"/value", 'w')
                    gpio_file.write(str(value))
                    gpio_file.close()
                    psu_amber = 0x1
                except IOError as e:
                    print "error: unable to open gpio psuLedAmber: %s" % str(e)

            time.sleep(6)

   # Helper method to map SONiC port name to index
    def _port_name_to_index(self, port_name):
        # Strip "Ethernet" off port name
        if not port_name.startswith(self.SONIC_PORT_NAME_PREFIX):
            return -1
        port_idx = int(port_name[len(self.SONIC_PORT_NAME_PREFIX):])
        return port_idx

    # called when port states change- implementation of port_link_state_change() method if needed
    def port_link_state_change(self, portname, state):
        return

