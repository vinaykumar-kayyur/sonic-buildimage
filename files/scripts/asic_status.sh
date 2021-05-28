#!/bin/bash

function check_asic_status() {
    python3 /usr/local/bin/asic_status.py $DEV
    if [[ $? = 0 ]]; then
        debug "$SERVICE successfully detected asic $DEV..."
        return 0
    fi
    debug "$SERVICE failed to detect asic $DEV..."
    return 1
}

function start_service() {
    chassis_sup=0
    if [ -f /etc/sonic/chassisdb.conf ]; then
        chassis_sup=1
    fi

    if [[ $1 == "start" && $chassis_sup -eq 0 ]]; then
        # start service docker
        /usr/bin/${SERVICE}.sh start $DEV
        debug "Started ${SERVICE}$DEV service..."
    elif [[ $1 == "wait" && $chassis_sup -eq 1 ]]; then
        # check asic status
        check_asic_status

        # start service docker
        /usr/bin/${SERVICE}.sh start $DEV
        debug "Started ${SERVICE}$DEV service..."
    fi
}
