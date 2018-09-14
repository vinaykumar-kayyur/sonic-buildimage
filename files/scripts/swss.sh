#!/bin/bash

SERVICE="swss"

function check_warm_boot()
{
    SYSTEM_WARM_START=`/usr/bin/redis-cli -n 4 hget "WARM_RESTART|system" enable`
    SERVICE_WARM_START=`/usr/bin/redis-cli -n 4 hget "WARM_RESTART|${SERVICE}" enable`
    if [[ x"$SYSTEM_WARM_START" == x"true" ]] || [[ x"$SERVICE_WARM_START" == x"true" ]]; then
        WARM_START="true"
    else
        WARM_START="false"
    fi
}

function validate_restart_count()
{
    if [[ x"$WARM_START" == x"true" ]]; then
        RESTART_COUNT=`/usr/bin/redis-cli -n 6 hget "WARM_RESTART_TABLE|orchagent" restart_count`
        # We have to make sure db data has not been flushed.
        if [[ -z "$RESTART_COUNT" ]]; then
            WARM_START="false"
        fi
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

start() {
    wait_for_database_service
    check_warm_boot
    validate_restart_count

    # Don't flush DB during warm boot
    if [[ x"$WARM_START" != x"true" ]]; then
        /usr/bin/docker exec database redis-cli -n 0 FLUSHDB
        /usr/bin/docker exec database redis-cli -n 1 FLUSHDB
        /usr/bin/docker exec database redis-cli -n 2 FLUSHDB
        /usr/bin/docker exec database redis-cli -n 5 FLUSHDB
        /usr/bin/docker exec database redis-cli -n 6 FLUSHDB

        # platform specific tasks
        if [ x$sonic_asic_platform == x'mellanox' ]; then
            FAST_BOOT=1
            /usr/bin/mst start
            /usr/bin/mlnx-fw-upgrade.sh
            /etc/init.d/sxdkernel start
            /sbin/modprobe i2c-dev
            /etc/mlnx/mlnx-hw-management start
        elif [ x$sonic_asic_platform == x'cavium' ]; then
            /etc/init.d/xpnet.sh start
        fi
    fi

    # start swss and syncd docker
    /usr/bin/swss.sh start
    if [[ x"$WARM_START" != x"true" ]]; then
        /usr/bin/syncd.sh start
    fi
    /usr/bin/swss.sh attach
}

stop() {
    check_warm_boot

    /usr/bin/swss.sh stop

    # if warm start enabled, just stop swss docker, then return
    if [[ x"$WARM_START" != x"true" ]]; then
        /usr/bin/syncd.sh stop

        # platform specific tasks
        if [ x$sonic_asic_platform == x'mellanox' ]; then
            /etc/mlnx/mlnx-hw-management stop
            /etc/init.d/sxdkernel stop
            /usr/bin/mst stop
        elif [ x$sonic_asic_platform == x'cavium' ]; then
            /etc/init.d/xpnet.sh stop
            /etc/init.d/xpnet.sh start
        fi
    fi
}

case "$1" in
    start|stop)
        $1
        ;;
    *)
        echo "Usage: $0 {start|stop}"
        exit 1
        ;;
esac
