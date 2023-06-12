#!/bin/bash

# Current lldpd version has a bug.
# When lldpd starts it is in the pause state by default
# But then it execute 'lldpcli resume' to configure and unpause itself.
# When lldpd execute lldpcli, it doesn't check the return code
# Sometimes lldpcli returns failure, but lldpd doesn't catch it
# and keeps working paused and unconfigured. The fix below addresses the issue and
# pause lldpd operations until all interfaces are well configured, resume command will run in lldpmgrd

# wait until lldpd started
until [[ -e /var/run/lldpd.socket ]];
do
    sleep 1;
done

# Manually try to resume lldpd, until it's successful
while /bin/true;
do
    lldpcli -u /var/run/lldpd.socket -c /etc/lldpd.conf -c /etc/lldpd.d pause > /dev/null && break
    sleep 1
done
