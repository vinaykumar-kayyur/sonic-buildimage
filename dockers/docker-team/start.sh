#!/bin/bash

TEAMD_CONF_PATH=/etc/teamd

function clean_up {
	pkill -9 teamd
	pkill -9 teamsyncd
	service rsyslog stop
	exit
}

trap clean_up SIGTERM SIGKILL

# Remove rsyslogd pid file if it exists
[ -e /var/run/rsyslogd.pid ] && rm /var/run/rsyslogd.pid
service rsyslog start

if [ -d $TEAMD_CONF_PATH ]; then
	for f in $TEAMD_CONF_PATH/*; do
		teamd -f $f -d
	done
fi

teamsyncd &

read
