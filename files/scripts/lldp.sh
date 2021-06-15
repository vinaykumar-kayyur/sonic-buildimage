#!/bin/bash

. /usr/local/bin/asic_status.sh

function debug()
{
    /usr/bin/logger $1
    /bin/echo `date` "- $1" >> ${DEBUGLOG}
}

start() {
    debug "Starting ${SERVICE}$DEV service..."

    # Check asic status before starting docker
    check_asic_status start
    ASIC_STATUS=$?

    # start service docker
    if [[ $ASIC_STATUS == 0 ]]; then
        /usr/bin/${SERVICE}.sh start $DEV
        debug "Started ${SERVICE}$DEV service..."
    fi
}

wait() {
    # Check asic status before starting docker
    check_asic_status wait
    ASIC_STATUS=$?

    # start service docker
    if [[ $ASIC_STATUS == 0 ]]; then
        /usr/bin/${SERVICE}.sh start $DEV
        debug "Started ${SERVICE}$DEV service..."
    fi

    /usr/bin/${SERVICE}.sh wait $DEV
}

stop() {
    debug "Stopping ${SERVICE}$DEV service..."

    /usr/bin/${SERVICE}.sh stop $DEV
    debug "Stopped ${SERVICE}$DEV service..."
}

DEV=$2

SERVICE="lldp"
DEBUGLOG="/tmp/lldp-debug$DEV.log"

case "$1" in
    start|wait|stop)
        $1
        ;;
    *)
        echo "Usage: $0 {start|wait|stop}"
        exit 1
        ;;
esac
