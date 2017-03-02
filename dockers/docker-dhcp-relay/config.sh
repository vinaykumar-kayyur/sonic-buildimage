#!/bin/bash

MINIGRAPH_HOSTNAME=`sonic-cfggen -m /etc/sonic/minigraph.xml -v "minigraph_hostname"`
DEVICE_ROLE=`sonic-cfggen -m /etc/sonic/minigraph.xml -v "minigraph_devices['$MINIGRAPH_HOSTNAME']['type']"`

if [ $DEVICE_ROLE != "ToRRouter" ]; then
    echo "Device does not require DHCP relay. docker-dhcp-relay exiting..."
    exit 1
fi

sonic-cfggen -m /etc/sonic/minigraph.xml -t /usr/share/sonic/templates/isc-dhcp-relay.j2 > /etc/default/isc-dhcp-relay

