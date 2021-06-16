#!/bin/bash

function check_asic_status() {
    chassis_sup=0
    if [ -f /etc/sonic/chassisdb.conf ]; then
        chassis_sup=1
    fi

    #Ignore
    if [[ -z $DEV ]]; then
        if [[ $1 == "start" ]]; then
            return 0
        else
            return 1
        fi
    fi

    if [[ $1 == "start" && $chassis_sup -eq 0 ]]; then
        return 0
    elif [[ $1 == "wait" && $chassis_sup -eq 1 ]]; then

        /usr/local/bin/asic_status.py $DEV
        if [[ $? = 0 ]]; then
            debug "$SERVICE successfully detected asic $DEV..."
            return 0
        fi
        debug "$SERVICE failed to detect asic $DEV..."
        return 1
    fi
    debug "$SERVICE start skipped during systemd $1 for $DEV..."
    return 1
}
