#!/usr/bin/env bash

function wait_for_intf_up {
    INTF_NAME=$1

    until [[ `ip link show $INTF_NAME | grep 'state UP'` ]]; do
        sleep 0.1;
    done
}

function restore_arp_to_kernel {
    ARP_FILE='/arp.json.1'
    NUM_ENTRIES=`jq 'length' $ARP_FILE`

    for i in $( seq 0 $(($NUM_ENTRIES - 1)) ); do

        # For the ith object, get the first key
        # 'jq' sorts the keys by default so this should always be
        # the 'NEIGH_TABLE' key, not the 'OP' key
        KEY=`jq ".[$i] | keys[0]" $ARP_FILE`
        
        # For all 'jq' commands below, use '-r' for raw output
        # to prevent double quoting

        # For the object associated with the 'NEIGH_TABLE' key
        # store the value of the 'neigh' field (the MAC address)
        MAC=`jq -r ".[$i][$KEY][\"neigh\"]" $ARP_FILE`

        # Split the 'NEIGH_TABLE' key with delimiter ':' and take the
        # second item from the result array which is the device name
        DEVICE=`echo $KEY | jq -r ". / \":\" | .[1]"`

        # Same as for VLAN, but take the third item which is the IP
        IP=`echo $KEY | jq -r ". / \":\" | .[2]"`

        wait_for_intf_up $DEVICE
        ip neigh replace "$IP" dev "$DEVICE" lladdr "$MAC" nud stale
    done
}

if [[ -f /restore-kernel ]]; then
    restore_arp_to_kernel
    rm -f /restore-kernel
fi