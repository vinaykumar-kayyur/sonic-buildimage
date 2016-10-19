#!/bin/bash

function clean_up {
    service syncd stop
    service rsyslog stop
    exit
}

trap clean_up SIGTERM SIGKILL

# Remove rsyslogd pid file if it exists
[ -e /var/run/rsyslogd.pid ] && rm /var/run/rsyslogd.pid
service rsyslog start
service syncd start

read
