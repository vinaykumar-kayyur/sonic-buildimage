#!/usr/bin/env bash

dpkg-reconfigure -f noninteractive tzdata

rm -f /var/run/rsyslogd.pid

supervisorctl start rsyslogd

supervisorctl start saiserver
