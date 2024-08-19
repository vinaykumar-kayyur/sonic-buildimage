#!/bin/bash

# When static IP is configured, or an interface with static IP has a link up event -
# send GARP/unsolicited NA with the new IPv4/IPv6 address

function wait_networking_service_done() {
    # Make sure the networking service is running
    local -i _COUNTER="1"
    local -ir _MAX_WAITING_DURATION="30"

    local -r _TIMEOUT="1s"

    while [[ "${_COUNTER}" -le "${_MAX_WAITING_DURATION}" ]]; do
        NETWORKING_STATUS="$(systemctl is-active networking 2>&1)"

        if [[ "${NETWORKING_STATUS}" == active || "${NETWORKING_STATUS}" == inactive ]] ; then
            return 0
        elif [[ "${NETWORKING_STATUS}" == failed ]] ; then
            return 1
        fi

        let "_COUNTER++"
        sleep "${_TIMEOUT}"
    done

    return 1
}

# Exit if feature is disabled
FEATURE_STATE=${FEATURE_STATE:-`sonic-cfggen -H -v MGMT_UNSOLICITED.general.state`}
if [[ $FEATURE_STATE == disabled ]]; then
    echo "mgmt-unsolicited - Feature is disabled"
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
    echo "mgmt-unsolicited - Protocl isn't ipv4 or ipv6"
    echo "mgmt-unsolicited - Protocl: $PROTOCOL"
    exit 1
fi

wait_networking_service_done
RET_VAL=$?
if [ $RET_VAL -ne 0 ]; then
    echo "mgmt-unsolicited: Networking service has not configured the mgmt interfaces properly"
    exit $RET_VAL
fi

sudo $CMD
