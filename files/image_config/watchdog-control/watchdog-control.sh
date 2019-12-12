#! /bin/bash

VERBOSE=no

function debug()
{
    /usr/bin/logger "$0 : $1"
    if [[ x"${VERBOSE}" == x"yes" ]]; then
        echo "$(date) $0: $1"
    fi
}


function disable_watchdog()
{
    # Disable Watchdog Timer
    debug "Disabling Watchdog during the bootup"
    if [[ -e /usr/local/bin/platform_watchdog_disable.sh ]]; then
        /usr/local/bin/platform_watchdog_disable.sh
    fi
}

disable_watchdog
