#!/bin/bash
# Copyright (C) 2016 Ingrasys, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

INTERVAL=5
I2C_UTILS="/usr/sbin/i2c_utils.sh"


# TBD:  LED status monitor
function _led_monitor {
    ${I2C_UTILS} i2c_led_fan_status_set >/dev/null
    ${I2C_UTILS} i2c_led_psu_status_set >/dev/null
    ${I2C_UTILS} i2c_led_fan_tray_status_set >/dev/null
}

# Core Temp send to BMC
function _coretemp_to_bmc {
    local temp=0
    local ipv6=0
    
    #get coretemp
    temp=`cat /sys/class/hwmon/hwmon0/temp2_input`
    temp=$(( $temp / 1000))
    
    
    # TBD: Must remove on Beta
    #script -q -c "redis-cli -h fe80::046:8aff:fe00:0000%eth0 hset platina host.temp.units.C $temp > /dev/null"
}

# main function
function _main {
    while true
    do
        #TBD: System LED controlled by BMC
        _led_monitor
        
        # Core Temp send to BMC
        _coretemp_to_bmc
        # Sleep while still handling signals
        sleep $INTERVAL &
        wait $!
    done
}

_main