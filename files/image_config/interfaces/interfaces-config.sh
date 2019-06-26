#!/bin/bash

NS=$1

if [ -z "$(ip netns)" ]; then
    ifdown --force eth0
    sonic-cfggen -d -t /usr/share/sonic/templates/interfaces.j2 > /etc/network/interfaces 
    [ -f /var/run/dhclient.eth0.pid ] && kill `cat /var/run/dhclient.eth0.pid` && rm -f /var/run/dhclient.eth0.pid
    systemctl restart networking
    ifdown lo && ifup lo
else
    INTF_LIST=`redis-cli $NS -n 4 KEYS 'LOOPBACK_INTERFACE*'`    
    for ENTRY in $INTF_LIST; do
        IFS='|' read -ra ADDR_ARRAY <<< "$ENTRY"
        ADDR=${ADDR_ARRAY[2]}   
        namespace $NS ip addr add $ADDR dev lo
    done
fi



