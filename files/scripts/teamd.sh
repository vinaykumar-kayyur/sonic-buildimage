#!/bin/bash

SERVICE="teamd"
DEBUGLOG="/tmp/teamd-debug.log"

function debug()
{
    /bin/echo `date` "- $1" >> ${DEBUGLOG}
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

function clean_up_tables()
{
    redis-cli -n $1 EVAL "
    local tables = {$2}
    for i = 1, table.getn(tables) do
        local matches = redis.call('KEYS', tables[i])
        for j,name in ipairs(matches) do
            redis.call('DEL', name)
        end
    end" 0
}

start() {
    debug "Starting ${SERVICE} service..."

    wait_for_database_service

    clean_up_tables 6 "LAG_TABLE*"

    /usr/bin/${SERVICE}.sh start
    /usr/bin/${SERVICE}.sh attach
}


stop() {
    debug "Stopping ${SERVICE} service..."
    /usr/bin/${SERVICE}.sh stop
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
