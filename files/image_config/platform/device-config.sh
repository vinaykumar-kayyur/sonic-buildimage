#!/bin/bash
#
# device-config.sh
#
# Script to perform tasks which configure device based on its role, etc.
# To be run by device-config.service
#

# Disable DHCP relay service if device does not require it
DEVICE_ROLE=`sonic-cfggen -m /etc/sonic/minigraph.xml -v "minigraph_devices[minigraph_hostname]['type']"`

if [ $DEVICE_ROLE == "ToRRouter" ]; then
    echo "Device requires DHCP relay. Enabling DHCP relay service..."
    systemctl enable dhcp_relay.service
else
    echo "Device does not require DHCP relay. Disabling DHCP relay service..."
    systemctl disable dhcp_relay.service
fi


# Disable teamd service if device does not require it
NUM_PORTCHANNELS=`sonic-cfggen -m /etc/sonic/minigraph.xml -v "minigraph_portchannels.keys() | count"`

if [ $NUM_PORTCHANNELS -gt 0 ]; then
    echo "Device requires teamd. Enabling teamd service..."
    systemctl enable teamd.service
else
    echo "Device does not require teamd. Disabling teamd service..."
    systemctl disable teamd.service
fi

