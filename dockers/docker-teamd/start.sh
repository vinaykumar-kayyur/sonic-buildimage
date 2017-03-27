#!/bin/bash

. config.sh

TEAMD_CONF_PATH=/etc/teamd

function start_app {
    if [ -d $TEAMD_CONF_PATH ]; then
        for f in $TEAMD_CONF_PATH/*; do
            teamd -f $f -d
        done
    fi
    teamsyncd &
}

function clean_up {
    if [ -d $TEAMD_CONF_PATH ]; then
        for f in $TEAMD_CONF_PATH/*; do
            teamd -f $f -k
        done
    fi
    pkill -9 teamsyncd
    service rsyslog stop
    exit
}

trap clean_up SIGTERM SIGKILL

rm -f /var/run/rsyslogd.pid
service rsyslog start

start_app
read
