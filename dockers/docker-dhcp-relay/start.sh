#!/usr/bin/env bash

function wait_until_iface_exists
{
    IFACE=$1

    echo "Waiting for interface ${IFACE}..."

    # Wait for the interface to come up (i.e., 'ip link show' returns 0)
    until ip link show $IFACE > /dev/null 2>&1; do
        sleep 1
    done

    echo "Interface ${IFACE} is created"
}

# Remove stale rsyslog PID file if it exists
rm -f /var/run/rsyslogd.pid

# Start rsyslog
supervisorctl start rsyslogd

# Wait for all interfaces to come up before starting the DHCP relay agent(s)
sonic-cfggen -d -t /usr/share/sonic/templates/wait_for_intf.sh.j2 > /usr/bin/wait_for_intf.sh
chmod +x /usr/bin/wait_for_intf.sh
/usr/bin/wait_for_intf.sh

# Start the DHCP relay agent(s)
supervisorctl start isc-dhcp-relay:*
