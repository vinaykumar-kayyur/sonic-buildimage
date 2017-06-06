#!/usr/bin/env bash

ASIC=`sonic-cfggen -y /etc/sonic/sonic_version.yml -v asic_type`

MAC_ADDRESS=`ip link show eth0 | grep ether | awk '{print $2}'`

# Create a folder for SsWW record files
mkdir -p /var/log/swss
ORCHAGENT_ARGS="-d /var/log/swss "

# Set orchagent pop batch size to 8192
ORCHAGENT_ARGS+="-b 8192 "

# Add platform specific arguments if necessary
if [ "$ASIC" == "broadcom" ]; then
    ORCHAGENT_ARGS+="-m $MAC_ADDRESS"
elif [ "$ASIC" == "cavium" ]; then
    ORCHAGENT_ARGS+="-m $MAC_ADDRESS"
elif [ "$HWSKU" == "Accton-AS7712-32X" ]; then
    ORCHAGENT_ARGS+="-m $MAC_ADDRESS"
else
    echo "Unsupported HWSKU:$HWSKU. Exiting..." > /dev/stderr
    exit 1
fi

exec /usr/bin/orchagent ${ORCHAGENT_ARGS}

