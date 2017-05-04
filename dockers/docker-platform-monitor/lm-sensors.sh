#!/usr/bin/env bash
#
# Based off /etc/init.d/lm-sensors
#

/usr/bin/sensors -s > /dev/null 2>&1
/usr/bin/sensors > /dev/null 2>&1

