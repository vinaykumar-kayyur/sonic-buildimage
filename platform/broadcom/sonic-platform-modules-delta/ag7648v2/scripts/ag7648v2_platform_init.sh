#!/bin/bash

#platform init script for Delta ag7648v2

#fan speed monitor start
/usr/share/sonic/device/x86_64-delta_ag7648v2-r0/fancontrol.service /usr/share/sonic/device/x86_64-delta_ag7648v2-r0/fancontrol &

# On Delta-ag7648v2 platform,
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

