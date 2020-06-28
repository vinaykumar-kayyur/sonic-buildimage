#!/bin/bash

DISABLE_COREDUMP_CONF="/etc/sysctl.d/50-disable-coredump.conf"

if [ "$(redis-cli -n 4 HGET "COREDUMP|config" "enabled")" = "false" ] ; then
   echo "kernel.core_pattern=" > ${DISABLE_COREDUMP_CONF}
else
   rm -f ${DISABLE_COREDUMP_CONF}
fi

# Read sysctl conf files again
systemctl restart systemd-sysctl

exit 0
