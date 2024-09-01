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

function send_unsolicited_announcement() {
    PROTOCOL=$1
    INTERFACE=$2
    ADDRESS=$3

    if [[ $PROTOCOL == ipv4 ]]; then
        CMD="arping -c 1 -U -i $INTERFACE $ADDRESS"
    elif [[ $PROTOCOL == ipv6 ]]; then
        # Need version 1.8>= of libndp-tools for '-T' flag
        CMD="ndptool -t na -U -i $INTERFACE -T $ADDRESS send"
    else
        logger -t "mgmt-unsolicited" -p "Warning" "Protocl isn't ipv4 or ipv6"
        logger -t "mgmt-unsolicited" -p "Warning" "Protocl: $PROTOCOL"
        exit 1
    fi

    # Verify that the interface is up
    wait_interface_status_up $INTERFACE
    RET_VAL=$?
    if [ $RET_VAL -ne 0 ]; then
        logger -t "mgmt-unsolicited" -p "Warning" "Interface $INTERFACE has no operstate"
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
}

# Exit if feature is disabled
FEATURE_STATE=$(sonic-db-cli CONFIG_DB hget 'DEVICE_METADATA|localhost' mgmt_unsolicited_state)
if [[ $FEATURE_STATE == disabled ]]; then
    logger -t "mgmt-unsolicited" "Feature is disabled"
    exit 0
fi

if [ "$#" -eq 1 ]; then
    # Cable connection event
    INTERFACE=$1
    logger -t "mgmt-unsolicited" "Detected cable connection - running script with interface $INTERFACE"
    # Get static IP addresses from DB
    STATIC_ADDRESS_KEYS=$(sonic-db-cli CONFIG_DB keys 'MGMT_INTERFACE|*')
    for STATIC_ADDRESS_KEY in $STATIC_ADDRESS_KEYS; do
        # Parse DB information
        DB_INTERFACE=$(echo "$STATIC_ADDRESS_KEY" | cut -d "|" -f2)
        if [[ $INTERFACE != $DB_INTERFACE ]]; then
            continue
        fi
        ADDRESS=$(echo "$STATIC_ADDRESS_KEY" | cut -d "|" -f3)
        ADDRESS="${ADDRESS%\/*}"
        case "$ADDRESS" in
            *.*)
                PROTOCOL="ipv4"
                ;;
            *:*)
                PROTOCOL="ipv6"
                ;;
            *)
                logger -t "mgmt-unsolicited" -p "Warning" "Protocl isn't ipv4 or ipv6"
                logger -t "mgmt-unsolicited" -p "Warning" "Protocl: $PROTOCOL"
                exit 1
                ;;
        esac
        send_unsolicited_announcement $PROTOCOL $INTERFACE $ADDRESS
    done
elif [ "$#" -eq 3 ]; then
    # Configuring interface using ip commands (such as configuration, init, ifup)
    send_unsolicited_announcement $1 $2 $3
else
    logger -t "mgmt-unsolicited" -p "Warning" "Wrong arguments given - Specify only the interface name, or specify protocol, interface name and IP address"
    exit 1
fi