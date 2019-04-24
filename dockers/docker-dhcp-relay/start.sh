#!/usr/bin/env bash

CURRENT_HOSTNAME=`hostname`
HOSTNAME=`sonic-cfggen -d -v DEVICE_METADATA[\'localhost\'][\'hostname\']`

if [ "$?" == "0" ] && [ "$HOSTNAME" != "" ]; then
    echo $HOSTNAME > /etc/hostname
    hostname -F /etc/hostname

    tempfile=`mktemp -q -t hosts.XXXX`
    sed "/\s$CURRENT_HOSTNAME$/d" /etc/hosts > $tempfile
    echo "127.0.0.1 $HOSTNAME" >> $tempfile
    cat $tempfile > /etc/hosts ; rm $tempfile
fi

# Remove stale rsyslog PID file if it exists
rm -f /var/run/rsyslogd.pid

# Start rsyslog
supervisorctl start rsyslogd

# If our supervisor config has entries in the "isc-dhcp-relay" group...
if [ $(supervisorctl status | grep -c "^isc-dhcp-relay:") -gt 0 ]; then
    # Wait for all interfaces to come up and be assigned IPv4 addresses before
    # starting the DHCP relay agent(s). If an interface the relay should listen
    # on is down, the relay agent will not start. If an interface the relay
    # should listen on is up but does not have an IP address assigned when the
    # relay agent starts, it will not listen or send on that interface for the
    # lifetime of the process.
    /usr/bin/wait_for_intf.sh

    # Start all DHCP relay agent(s)
    supervisorctl start isc-dhcp-relay:*
fi
