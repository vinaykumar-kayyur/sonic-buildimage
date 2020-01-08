#!/bin/bash

SERVICE="bgp"
DEBUGLOG="/tmp/bgp_debug.log"
LOCKFILE="/tmp/bgp-lock"

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
    STATE_DBID_PORT=`python -c 'from swsssdk import _get_redis_dbid_port; print _get_redis_dbid_port("STATE_DB")'`
    SYSTEM_WARM_START=`/usr/bin/redis-cli $STATE_DBID_PORT hget "WARM_RESTART_ENABLE_TABLE|system" enable`
    SERVICE_WARM_START=`/usr/bin/redis-cli $STATE_DBID_PORT hget "WARM_RESTART_ENABLE_TABLE|${SERVICE}" enable`
    if [[ x"$SYSTEM_WARM_START" == x"true" ]] || [[ x"$SERVICE_WARM_START" == x"true" ]]; then
        WARM_BOOT="true"
    else
        WARM_BOOT="false"
    fi
}

function validate_restore_count()
{
    if [[ x"$WARM_BOOT" == x"true" ]]; then
        STATE_DBID_PORT=`python -c 'from swsssdk import _get_redis_dbid_port; print _get_redis_dbid_port("STATE_DB")'`
        RESTORE_COUNT=`/usr/bin/redis-cli $STATE_DBID_PORT hget "WARM_RESTART_TABLE|orchagent" restore_count`
        # We have to make sure db data has not been flushed.
        if [[ -z "$RESTORE_COUNT" ]]; then
            WARM_BOOT="false"
        fi
    fi
}

function wait_for_database_service()
{
    # Wait for redis server start before database clean
    ping_pong_db_insts

    # Wait for configDB initialization
    until [[ $(/usr/bin/docker exec database redis-cli `python -c 'from swsssdk import _get_redis_dbid_port; print _get_redis_dbid_port("CONFIG_DB")'` GET "CONFIG_DB_INITIALIZED") ]];
        do sleep 1;
    done
}

start() {
    debug "Starting ${SERVICE} service..."

    lock_service_state_change

    wait_for_database_service
    check_warm_boot
    validate_restore_count

    debug "Warm boot flag: ${SERVICE} ${WARM_BOOT}."

    # start service docker
    /usr/bin/${SERVICE}.sh start
    debug "Started ${SERVICE} service..."

    # Unlock has to happen before reaching out to peer service
    unlock_service_state_change
}

attach() {
    startPeerService
    /usr/bin/${SERVICE}.sh attach
}

stop() {
    debug "Stopping ${SERVICE} service..."

    [[ -f ${LOCKFILE} ]] || /usr/bin/touch ${LOCKFILE}

    lock_service_state_change
    check_warm_boot
    debug "Warm boot flag: ${SERVICE} ${WARM_BOOT}."

		# Kill bgpd to start the bgp graceful restart procedure, otherwise it sends Notification to peer
		debug "Stopping ${SERVICE} service..."
		/usr/bin/docker exec -i bgp pkill -9 zebra
		/usr/bin/docker exec -i bgp pkill -9 bgpd || [ $? == 1 ]
		
    /usr/bin/${SERVICE}.sh stop
    debug "Stopped ${SERVICE} service..."

    # Unlock has to happen before reaching out to peer service
    unlock_service_state_change
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
