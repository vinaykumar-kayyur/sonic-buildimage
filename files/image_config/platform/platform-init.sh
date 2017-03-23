#!/bin/bash
#
# platform-init.sh
#
# Script to perform tasks which configure platform upon first boot
# To be run by platform-init.service if it detects first boot
#

PLATFORM=`sonic-cfggen -v platform`

if [ -n $PLATFORM ]; then
    echo "SONiC platform: $PLATFORM"

    echo "Copying default minigraph for $PLATFORM to /etc/sonic/"
    cp /usr/share/sonic/device/$PLATFORM/minigraph.xml /etc/sonic/

    if [ -d /host/platform/$PLATFORM ]; then
        echo "Installing platform-dependent packages for $PLATFORM..."
        dpkg -i /host/platform/$PLATFORM/*.deb
    fi
else
    echo "SONiC platform unknown. Could not install platform-dependent packages."
fi

