#!/bin/bash
# This script is invoked by topology.service only
# for multi-asic virtual platform. For multi-asic platform 
# multiple Database instances are present 
# and HWKSU information is retrieved from first database instance.
#

start() {
    TOPOLOGY_SCRIPT="topology.sh"
    PLATFORM=`sonic-cfggen -H -v DEVICE_METADATA.localhost.platform`
    HWSKU=${HWSKU:-`sonic-cfggen -d -v 'DEVICE_METADATA["localhost"]["hwsku"]' 2>&1`}
    if [[ $? -ne 0 ]]; then
            if [[ -f "/etc/sonic/minigraph.xml" ]]; then
                HWSKU=`sonic-cfggen -m /etc/sonic/minigraph.xml -v "DEVICE_METADATA['localhost']['hwsku']" 2>&1`
                if [[ $? -ne 0 ]]; then
                    echo "Failed to get HWSKU"
                    exit
                fi
            fi
    fi
    /usr/share/sonic/device/$PLATFORM/$HWSKU/$TOPOLOGY_SCRIPT start
}
stop() {
    TOPOLOGY_SCRIPT="topology.sh"
    PLATFORM=`sonic-cfggen -H -v DEVICE_METADATA.localhost.platform`
    HWSKU=${HWSKU:-`sonic-cfggen -d -v 'DEVICE_METADATA["localhost"]["hwsku"]' 2>&1`}
    if [[ $? -ne 0 ]]; then
            if [[ -f "/etc/sonic/minigraph.xml" ]]; then
                HWSKU=`sonic-cfggen -m /etc/sonic/minigraph.xml -v "DEVICE_METADATA['localhost']['hwsku']" 2>&1`
                if [[ $? -ne 0 ]]; then
                    echo "Failed to get HWSKU"
                    exit
                fi
            fi
    fi
    /usr/share/sonic/device/$PLATFORM/$HWSKU/$TOPOLOGY_SCRIPT stop
}

# read SONiC immutable variables
[ -f /etc/sonic/sonic-environment ] && . /etc/sonic/sonic-environment

case "$1" in
    start|stop)
        $1
        ;;
    *)
        echo "Usage: $0 {start|stop}"
        ;;
esac
