#!/bin/bash

#platform init script for Delta agv848v1

#Auto fan speed control start
/usr/share/sonic/device/x86_64-delta_agv848v1-r0/fancontrol.service /usr/share/sonic/device/x86_64-delta_agv848v1-r0/fancontrol &

# On Delta-agv848v1 platform,
# syseeprom is on the I2C address 0x54
# we have to create an eeprom I2C device before getting syseeprom data.
#
# The purpose of getting syseeprom information here
# is to store data in syseeprom_cache.
# After that, we can read "syseeprom_cache" directly when executing command
# "show platform syseeprom", "sudo decode-syseeprom", "show version".

echo eeprom 0x54 > /sys/bus/i2c/devices/i2c-1/new_device
decode-syseeprom
exit 0

