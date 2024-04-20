#! /bin/bash -x

# A script to call /usr/local/bin/fsio-rw-sync and update sync time to STATE_DB upon successful return

STORAGEMON_INFO_TABLE="STORAGEMON_INFO"
fsstats_sync_interval="fsstats_sync_interval"
DEFAULT_SLEEP_TIME=3600

FSSTATS_TABLE="FSSTATS_SYNC"
fsstats_sync_time="successful_sync_time"

function debug()
{
    /usr/bin/logger "$0 : $1"
    if [[ x"${VERBOSE}" == x"yes" ]]; then
        echo "$(date) $0: $1"
    fi
}

function get_sync_interval()
{
    redis-cli -n 4 HGET $STORAGEMON_INFO_TABLE $fsstats_sync_interval
}

function set_fsstats_sync()
{
    redis-cli -n 6 HSET $FSSTATS_TABLE $fsstats_sync_time "$1"
}

function sync_fsio_stats()
{
    while true
    do
        # Getting the sleep time every loop enables us to change it dynamically without having to restart the process.

        rc=$(get_sync_interval)
        SLEEP_TIME=$DEFAULT_SLEEP_TIME

        if [ ! -z "${rc}" ]; then
            SLEEP_TIME=$rc
        fi
        
        /usr/local/bin/fsio-rw-sync
        if [ $? -eq 0 ]; then
            set_fsstats_sync $(date '+%Y-%m-%d::%H:%M:%S')
        else
           VERBOSE="yes" debug "FSIO R/W Sync Failed"
        fi

        sleep $SLEEP_TIME
    done
}

sync_fsio_stats
