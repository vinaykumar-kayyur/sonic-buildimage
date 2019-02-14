#!/bin/bash -e

CURRENT_TIMEZONE=`cat /etc/timezone`
TIMEZONE=`sonic-cfggen -d -v DEVICE_METADATA[\'localhost\'][\'timezone\']`

if [ ! $TIMEZONE == "" ]
then
    sudo bash -c "echo $TIMEZONE > /etc/timezone"
    sudo bash -c "dpkg-reconfigure -f noninteractive tzdata"
    sudo bash -c "systemctl restart rsyslog"
    sudo bash -c "systemctl restart cron"
fi
