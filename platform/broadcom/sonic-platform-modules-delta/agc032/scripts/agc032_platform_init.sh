#!/bin/bash

#platform init script for Delta agc032

#fan speed monitor start
/usr/share/sonic/device/x86_64-delta_agc032-r0/fancontrol.service /usr/share/sonic/device/x86_64-delta_agc032-r0/fancontrol &

#Get syseeprom information
echo 0 |sudo tee /sys/devices/platform/delta-agc032-cpupld.0/cpu_i2c_mux_sel
decode-syseeprom
echo 1 |sudo tee /sys/devices/platform/delta-agc032-cpupld.0/cpu_i2c_mux_sel

exit 0

