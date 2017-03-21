#!/bin/bash
#
# device-config.sh
#
# Script to perform tasks which configure device upon first boot
# To be run on first boot by device-config.service
#

# Install platform-dependent packages
echo "Installing platform-dependent packages..."

PLATFORM=`sonic-cfggen -v platform`

if [ -n $PLATFORM ]; then
    echo "SONiC platform: $PLATFORM"

    cp /usr/share/sonic/device/$platform/minigraph.xml /etc/sonic/

    if [ -d /host/platform/$platform ]; then
        dpkg -i /host/platform/$platform/*.deb
    fi
else
    echo "SONiC platform unknown. Could not install platform-dependent packages."
fi

# Disable DHCP relay service if device does not require it
DEVICE_ROLE=`sonic-cfggen -m /etc/sonic/minigraph.xml -v "minigraph_devices[minigraph_hostname]['type']"`

if [ $DEVICE_ROLE != "ToRRouter" ]; then
    echo "Device does not require DHCP relay. Disabling DHCP relay service..."
    systemctl disable dhcp_relay.service
fi


# Disable teamd service if device does not require it
NUM_PORTCHANNELS=`sonic-cfggen -m /etc/sonic/minigraph.xml -v "minigraph_portchannels.keys() | count"`
if [ $NUM_PORTCHANNELS -eq 0 ]; then
    echo "Device does not require teamd. Disabling teamd service..."
    systemctl disable teamd.service
fi

