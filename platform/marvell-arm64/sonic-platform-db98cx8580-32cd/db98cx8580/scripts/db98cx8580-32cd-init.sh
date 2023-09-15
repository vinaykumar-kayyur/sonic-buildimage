#!/bin/bash

# Platform init script for db98cx8580-32cd 

db98cx8580_profile()
{
    MAC_ADDR=$(fw_printenv -n ethaddr)
    find /usr/share/sonic/device/*db98cx* -name profile.ini | xargs sed -i "s/switchMacAddress=.*/switchMacAddress=$MAC_ADDR/g"
    echo "db98cx8540: Updating switch mac address ${MAC_ADDR}"
}

# - Main entry
db98cx8580_profile

# LOGIC to enumerate SFP eeprom devices - send 0x50 to kernel i2c driver - initialize devices
# the mux may be enumerated at number 4 or 5 so we check for the mux and skip if needed
# Get list of the mux channels
# Enumerate the SFP eeprom device on each mux channel
echo optoe2 0x50 > /sys/bus/i2c/devices/i2c-0/new_device
exit 0
