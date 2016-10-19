#!/bin/bash

function clean_up {
    pkill -9 fpmsyncd
    service quagga stop
    service rsyslog stop
    exit
}

trap clean_up SIGTERM SIGKILL

# Remove rsyslogd pid file if it exists
[ -e RSYSLOGD_PIDFILE ] && rm RSYSLOGD_PIDFILE
service rsyslog start
service quagga start
fpmsyncd &
