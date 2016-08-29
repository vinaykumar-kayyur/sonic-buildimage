#!/bin/bash

. /host/machine.conf

MAC_ADDRESS=`ip link show eth0 | grep ether | awk '{print $2}'`

ORCHAGENT_ARGS=""

PORTSYNCD_ARGS="-p /usr/local/bin/port_config_cavm.ini"

service rsyslog start
orchagent $ORCHAGENT_ARGS &
sleep 5
portsyncd $PORTSYNCD_ARGS &
sleep 5
intfsyncd &
sleep 5
neighsyncd &
