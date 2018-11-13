#!/usr/bin/env bash

rm -f /var/run/rsyslogd.pid
rm -f /var/run/teamd/*

if [[ x"$WARM_BOOT" != x"true" ]]; then
    for pc in `ip link show | grep PortChannel | awk -F "[ :]" '{print $3}'`;
        do ip link delete dev $pc
    done
fi

mkdir -p /var/warmboot/teamd

supervisorctl start rsyslogd

supervisorctl start teammgrd

supervisorctl start teamsyncd
