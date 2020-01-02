#!/bin/bash
# This script is invoked by topology.service only
# for multi-asic virtual platform. This expects
# multiple Database instances and HWKSU information
# is retrieved from first database instance.
#

start() {
	DB_FIRST_INSTANCE="/var/run/redis0/redis.sock"
	TOPOLOGY_SCRIPT="topology.sh"
	PLATFORM=`sonic-cfggen -H -v DEVICE_METADATA.localhost.platform -s $DB_FIRST_INSTANCE`
	HWSKU=`sonic-cfggen -d -v 'DEVICE_METADATA["localhost"]["hwsku"]' -s $DB_FIRST_INSTANCE`
        /usr/share/sonic/device/$VS_PLATFORM/$HWSKU/$TOPOLOGY_SCRIPT start
}
stop() {
        DB_FIRST_INSTANCE="/var/run/redis0/redis.sock"
        TOPOLOGY_SCRIPT="topology.sh"
        PLATFORM=`sonic-cfggen -H -v DEVICE_METADATA.localhost.platform -s $DB_FIRST_INSTANCE`
        HWSKU=`sonic-cfggen -d -v 'DEVICE_METADATA["localhost"]["hwsku"]' -s $DB_FIRST_INSTANCE`
        /usr/share/sonic/device/$VS_PLATFORM/$HWSKU/$TOPOLOGY_SCRIPT stop 
}

case "$1" in
    start|stop)
        $1
        ;;
    *)
        echo "Usage: $0 {start|stop}"
        ;;
esac
