#!/bin/bash
#
# role-config.sh
#
# Script to perform tasks which configure device based on its role as determined by its minigraph
# To be run by role-config.service
#

# Disable DHCP relay service if device does not require it
DHCP_RELAY_SERVICE_START_FILE=/etc/sonic/role/dhcp_relay
DEVICE_ROLE=`sonic-cfggen -m /etc/sonic/minigraph.xml -v "minigraph_devices[minigraph_hostname]['type']"`

if [ $DEVICE_ROLE == "ToRRouter" ]; then
    echo "Device requires DHCP relay service. Ensuring start file exists..."
    touch $DHCP_RELAY_SERVICE_START_FILE
else
    echo "Device does not require DHCP relay service. Deleting start file..."
    rm -f $DHCP_RELAY_SERVICE_START_FILE
fi


# Disable teamd service if device does not require it
TEAMD_SERVICE_START_FILE=/etc/sonic/role/teamd
NUM_PORTCHANNELS=`sonic-cfggen -m /etc/sonic/minigraph.xml -v "minigraph_portchannels.keys() | count"`

if [ $NUM_PORTCHANNELS -gt 0 ]; then
    echo "Device requires teamd service. Ensuring start file exists..."
    touch $TEAMD_SERVICE_START_FILE
else
    echo "Device does not require teamd service. Deleting start file..."
    rm -f $TEAMD_SERVICE_START_FILE
fi

