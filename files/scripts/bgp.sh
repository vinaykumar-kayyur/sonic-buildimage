#!/bin/bash

SERVICE="bgp"
DEBUGLOG="/tmp/bgp_debug.log"

function debug()
{
    /usr/bin/logger $1
    /bin/echo `date` "- $1" >> ${DEBUGLOG}
}

function check_warm_boot()
{
    SYSTEM_WARM_START=`/usr/bin/redis-cli -n 6 hget "WARM_RESTART_ENABLE_TABLE|system" enable`
    SERVICE_WARM_START=`/usr/bin/redis-cli -n 6 hget "WARM_RESTART_ENABLE_TABLE|${SERVICE}" enable`
    if [[ x"$SYSTEM_WARM_START" == x"true" ]] || [[ x"$SERVICE_WARM_START" == x"true" ]]; then
        WARM_BOOT="true"
    else
        WARM_BOOT="false"
    fi
}

function validate_restore_count()
{
    if [[ x"$WARM_BOOT" == x"true" ]]; then
        RESTORE_COUNT=`/usr/bin/redis-cli -n 6 hget "WARM_RESTART_TABLE|bgp" restore_count`
        # We have to make sure db data has not been flushed.
        if [[ -z "$RESTORE_COUNT" ]]; then
            WARM_BOOT="false"
        fi
    fi
}

function check_fast_boot ()
{
    if [[ $($SONIC_DB_CLI STATE_DB GET "FAST_REBOOT|system") == "1" ]]; then
        FAST_BOOT = "true"
    else
        FAST_BOOT = "false"
		fi
}

start() {
    debug "Starting ${SERVICE} service..."

    check_warm_boot
    validate_restore_count

    check_fast_boot

    debug "Warm boot flag: ${SERVICE} ${WARM_BOOT}."
    debug "Fast boot flag: ${SERVICE} ${Fast_BOOT}."

    # start service docker
    /usr/bin/${SERVICE}.sh start
    debug "Started ${SERVICE} service..."

}

attach() {
    /usr/bin/${SERVICE}.sh attach
}

stop() {
    debug "Stopping ${SERVICE} service..."

    check_warm_boot
    check_fast_boot
    debug "Warm boot flag: ${SERVICE} ${WARM_BOOT}."
    debug "Fast boot flag: ${SERVICE} ${FAST_BOOT}."

    # Kill bgpd to start the bgp graceful restart procedure
    if [[ x"$WARM_BOOT" == x"true" ]] || [[ x"$FAST_BOOT" == x"true" ]]; then
        debug "Kill zebra first"
        /usr/bin/docker exec -i bgp pkill -9 zebra
        /usr/bin/docker exec -i bgp pkill -9 bgpd || [ $? == 1 ]
    fi

    /usr/bin/${SERVICE}.sh stop
    debug "Stopped ${SERVICE} service..."

}

case "$1" in
    start|attach|stop)
        $1
        ;;
    *)
        echo "Usage: $0 {start|attach|stop}"
        exit 1
        ;;
esac
