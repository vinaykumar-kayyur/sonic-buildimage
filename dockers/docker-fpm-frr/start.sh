#!/bin/bash

dpkg-reconfigure -f noninteractive tzdata

rm -f /var/run/rsyslogd.pid
service rsyslog start
service frr start
fpmsyncd &
