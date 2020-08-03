#!/bin/bash

SERVICE="physyncd"
PEER="swss"
DEBUGLOG="/tmp/swss-physyncd-debug.log"
LOCKFILE="/tmp/swss-physyncd-lock"

function debug()
{
    /usr/bin/logger $1
    /bin/echo `date` "- $1" >> ${DEBUGLOG}
}

function lock_service_state_change()
{
    debug "Locking ${LOCKFILE} from ${SERVICE} service"

    exec {LOCKFD}>${LOCKFILE}
    /usr/bin/flock -x ${LOCKFD}
    trap "/usr/bin/flock -u ${LOCKFD}" 0 2 3 15

    debug "Locked ${LOCKFILE} (${LOCKFD}) from ${SERVICE} service"
}

function unlock_service_state_change()
{
    debug "Unlocking ${LOCKFILE} (${LOCKFD}) from ${SERVICE} service"
    /usr/bin/flock -u ${LOCKFD}
}

function check_warm_boot()
{
    SYSTEM_WARM_START=`/usr/bin/redis-cli -n 6 hget "WARM_RESTART_ENABLE_TABLE|system" enable`
    SERVICE_WARM_START=`/usr/bin/redis-cli -n 6 hget "WARM_RESTART_ENABLE_TABLE|${SERVICE}" enable`
    # SYSTEM_WARM_START could be empty, always make WARM_BOOT meaningful.
    if [[ x"$SYSTEM_WARM_START" == x"true" ]] || [[ x"$SERVICE_WARM_START" == x"true" ]]; then
        WARM_BOOT="true"
    else
        WARM_BOOT="false"
    fi
}

function wait_for_database_service()
{
    # Wait for redis server start before database clean
    until [[ $(/usr/bin/docker exec database redis-cli ping | grep -c PONG) -gt 0 ]];
        do sleep 1;
    done

    # Wait for configDB initialization
    until [[ $(/usr/bin/docker exec database redis-cli -n 4 GET "CONFIG_DB_INITIALIZED") ]];
        do sleep 1;
    done
}

function getBootType()
{
    case "$(cat /proc/cmdline | grep -o 'SONIC_BOOT_TYPE=\S*' | cut -d'=' -f2)" in
    warm*)
        TYPE='warm'
        ;;
    fastfast)
        TYPE='fastfast'
        ;;
    fast*)
        TYPE='fast'
        ;;
    *)
        TYPE='cold'
    esac
    echo "${TYPE}"
}

start() {
    debug "Starting ${SERVICE} service..."

    lock_service_state_change

    mkdir -p /host/warmboot

    wait_for_database_service
    check_warm_boot

    debug "Warm boot flag: ${SERVICE} ${WARM_BOOT}."

    if [[ x"$WARM_BOOT" == x"true" ]]; then
        # Leave a mark for syncd scripts running inside docker.
        touch /host/warmboot/warm-starting
    else
        rm -f /host/warmboot/warm-starting
    fi

    # start service docker
    /usr/bin/${SERVICE}.sh start
    debug "Started ${SERVICE} service..."

    unlock_service_state_change
}

wait() {
    /usr/bin/${SERVICE}.sh wait
}

stop() {
    debug "Stopping ${SERVICE} service..."

    lock_service_state_change
    check_warm_boot
    debug "Warm boot flag: ${SERVICE} ${WARM_BOOT}."

    if [[ x"$WARM_BOOT" == x"true" ]]; then
        TYPE=warm
    else
        TYPE=cold
    fi

    if [[ x$TYPE != x"cold" ]]; then
        debug "${TYPE} shutdown physyncd process ..."
        /usr/bin/docker exec -i physyncd /usr/bin/syncd_request_shutdown --${TYPE}

        # wait until syncd quits gracefully
        while docker top physyncd | grep -q /usr/bin/physyncd; do
            sleep 0.1
        done

        /usr/bin/docker exec -i physyncd /bin/sync
        debug "Finished ${TYPE} shutdown physyncd process ..."
    fi

    /usr/bin/${SERVICE}.sh stop
    debug "Stopped ${SERVICE} service..."

    unlock_service_state_change
}

case "$1" in
    start|wait|stop)
        $1
        ;;
    *)
        echo "Usage: $0 {start|wait|stop}"
        exit 1
        ;;
esac
