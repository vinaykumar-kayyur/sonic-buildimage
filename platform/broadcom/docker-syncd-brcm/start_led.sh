#!/usr/bin/env bash

PLATFORM_DIR=/usr/share/sonic/platform
SYNCD_SOCKET_FILE=/var/run/sswsyncd/sswsyncd.socket
LED_PROC_INIT_SOC=${PLATFORM_DIR}/led_proc_init.soc

# Function: wait until syncd has created the socket for bcmcmd to connect to
wait_syncd() {
    while true; do
        if [ -e ${SYNCD_SOCKET_FILE} ]; then
            break
        fi
        sleep 1
    done

    # wait until bcm sdk is ready to get a request
    counter=0
    while true; do
        /usr/bin/bcmcmd -t 1 "show unit" | grep BCM >/dev/null 2>&1
        rv=$?
        if [ $rv -eq 0 ]; then
            break
        fi
        counter=$((counter+1))
        if [ $counter -ge 60 ]; then
            echo "syncd is not ready to take commands after $counter re-tries; Exiting!"
            break
        fi
        sleep 1
    done
}

# If this platform has an initialization file for the Broadcom LED microprocessor, load it
if [[ -r "$LED_PROC_INIT_SOC" && ! -f /var/warmboot/warm-starting ]]; then
    wait_syncd
    /usr/bin/bcmcmd -t 60 "rcload $LED_PROC_INIT_SOC"
fi

wait_syncd
# Run the command and store the output in a variable, ignoring errors
output=$(/usr/bin/bcmcmd -t 1 "show unit" 2>/dev/null | grep BCM)

# Check if the output contains either "BCM56960" or "BCM56970" or "BCM56971"
if [[ $output == *"BCM56960"* || $output == *"BCM56970"* || $output == *"BCM56971"* ]]; then
    /usr/bin/bcmcmd "mod RTAG7_PORT_BASED_HASH 0 391 OFFSET_ECMP=0xa" >/dev/null 2>&1
fi
