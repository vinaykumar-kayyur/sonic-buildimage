#! /bin/bash

VERBOSE=no

function debug()
{
    /usr/bin/logger "WATCHDOG-CONTROL : $1"
    if [[ x"${VERBOSE}" == x"yes" ]]; then
        echo `date` "- $1"
    fi
}


function disable_watchdog()
{
    # Disable Watchdog Timer
    debug "Disable Watchdog during the bootup"
    if [[ -e /usr/local/bin/platform_watchdog_disable.sh ]]; then
        /usr/local/bin/platform_watchdog_disable.sh
}

disable_watchdog
