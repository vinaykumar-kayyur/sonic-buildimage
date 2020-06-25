#!/usr/bin/env bash

PLATFORM_DIR=/usr/share/sonic/platform
HWSKU_DIR=/usr/share/sonic/hwsku


# Remove stale files if they exist
rm -f /var/run/rsyslogd.pid

supervisorctl start rsyslogd

mkdir -p /etc/sai.d/

# Create/Copy the sai.profile to /etc/sai.d/sai.profile
if [ -f $HWSKU_DIR/pai.profile.j2 ]; then
    sonic-cfggen -d -t $HWSKU_DIR/pai.profile.j2 > /etc/sai.d/pai.profile
else
    if [ -f $HWSKU_DIR/pai.profile ]; then
        cp $HWSKU_DIR/pai.profile /etc/sai.d/pai.profile
    fi
fi

# Create/Copy the gearbox configs to /etc/sai.d/sai.profile
if [[ x"$sonic_asic_platform" == x"broadcom" ]]; then
    if [ -d $HWSKU_DIR/gearbox ]; then
        cp $HWSKU_DIR/gearbox/*.bcm /etc/sai.d/.
    fi
fi

supervisorctl start physyncd

