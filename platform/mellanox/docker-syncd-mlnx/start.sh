#!/usr/bin/env bash

if [ -d /var/warmboot/syncd ]; then
    echo 1000 > /proc/sys/kernel/ns_last_pid
fi

rm -f /var/run/rsyslogd.pid

supervisorctl start rsyslogd

supervisorctl start syncd

supervisorctl start mlnx-sfpd
