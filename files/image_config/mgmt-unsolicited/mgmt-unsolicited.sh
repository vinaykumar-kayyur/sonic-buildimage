#!/bin/bash

# When static IP is configured, or an interface with static IP has a link up event -
# send GARP/unsolicited NA with the new IPv4/IPv6 address

function wait_interface_status_up() {
    # Make sure the networking service is running
    INTERFACE=$1
    if [ ! -e /sys/class/net/$INTERFACE/operstate ]; then
        return 1
    fi
    local -i _COUNTER="1"
    local -ir _MAX_WAITING_DURATION="30"

    local -r _TIMEOUT="1s"

    while [[ "${_COUNTER}" -le "${_MAX_WAITING_DURATION}" ]]; do
        INTERFACE_STATUS="$(cat /sys/class/net/$INTERFACE/operstate)"

        if [[ "${INTERFACE_STATUS}" == up ]] ; then
            return 0
        fi

        let "_COUNTER++"
        sleep "${_TIMEOUT}"
    done

    return 0
}

# Exit if feature is disabled
FEATURE_STATE=$(sonic-db-cli CONFIG_DB hget 'DEVICE_METADATA|localhost' mgmt_unsolicited_state)
if [[ $FEATURE_STATE == disabled ]]; then
    logger -t "mgmt-unsolicited" "Feature is disabled"
    exit 0
fi

# Arguments given by '/etc/network/interfaces' call
PROTOCOL=$1
INTERFACE=$2
ADDRESS=$3

if [[ $PROTOCOL == ipv4 ]]; then
    CMD="arping -c 1 -U -i $INTERFACE $ADDRESS"
elif [[ $PROTOCOL == ipv6 ]]; then
    # Need version 1.8>= of libndp-tools for '-T' flag
    CMD="ndptool -t na -U -i $INTERFACE -T $ADDRESS send"
else
    logger -t "mgmt-unsolicited" "Protocl isn't ipv4 or ipv6"
    logger -t "mgmt-unsolicited" "Protocl: $PROTOCOL"
    exit 1
fi

wait_interface_status_up $INTERFACE
RET_VAL=$?
if [ $RET_VAL -ne 0 ]; then
    logger -t "mgmt-unsolicited" -p "Warning" "Networking service has not configured the mgmt interfaces properly"
    exit $RET_VAL
fi

logger -t "mgmt-unsolicited" "Executing command: $CMD"
RESPONSE="$(sudo $CMD 2>&1)"
RET_VAL=$?

if [ $RET_VAL -ne 0 ]; then
    if [[ $PROTOCOL == ipv6 ]] || echo $RESPONSE | grep -q -v "Timeout"; then
        logger -t "mgmt-unsolicited" -p "Warning" "$RESPONSE"
    fi
fi
