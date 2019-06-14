#!/bin/bash

start () {
    # Move external links into assigned frontend namespaces
    # eth0  - eth15: namespace2
    # eth16 - eth31: namespace3
    # eth32 - eth47: namespace4
    # eth48 - eth63: namespace5
    for NS in `seq 2 5`; do
        for NUM in `seq 1 16`; do
            ORIG="eth$((16 * $(($NS - 2)) + $NUM - 1))"
            TEMP="ethTemp999"
            NEW="eth$(($NUM + 16))"
            ip link set dev $ORIG down
            ip link set dev $ORIG name $TEMP # rename to prevent conflicts before renaming in new namespace
            ip link set dev $TEMP netns namespace$NS
            sudo ip netns exec namespace$NS ip link set $TEMP name $NEW # rename to final interface name
            sudo ip netns exec namespace$NS ip link set $NEW up 
        done
    done

    # Connect all backend namespaces to frontend namespaces
    for BACKEND in `seq 0 1`; do
        for FRONTEND in `seq 2 5`; do
            for LINK in `seq 1 8`; do
                BACK_NAME="eth$((8 * $(($FRONTEND - 2)) + $LINK))"
                FRONT_NAME="eth$((8 * $BACKEND + $LINK))" 
                TEMP_BACK="ethBack999"
                TEMP_FRONT="ethFront999"
                
                ip link add $TEMP_BACK type veth peer name $TEMP_FRONT # temporary name to prevent conflicts between interfaces
                ip link set dev $TEMP_BACK netns namespace$BACKEND
                ip link set dev $TEMP_FRONT netns namespace$FRONTEND 
    
                sudo ip netns exec namespace$BACKEND ip link set $TEMP_BACK name $BACK_NAME
                sudo ip netns exec namespace$FRONTEND ip link set $TEMP_FRONT name $FRONT_NAME

                sudo ip netns exec namespace$BACKEND ip link set $BACK_NAME up
                sudo ip netns exec namespace$FRONTEND ip link set $FRONT_NAME up
            done
        done
    done
}

stop() {
    for NS in `seq 2 5`; do
        for NUM in `seq 1 16`; do
            TEMP="eth999"
            OLD="eth$(($NUM + 16))"
            NAME="eth$((16 * $(( $NS - 2)) + $NUM - 1))"
            sudo ip netns exec namespace$NS ip link set dev $OLD down
            sudo ip netns exec namespace$NS ip link set dev $OLD name $TEMP
            sudo ip netns exec namespace$NS ip link set dev $TEMP netns 1
            ip link set dev $TEMP name $NAME
            ip link set dev $NAME up
        done
    done

    for NS in `seq 0 1`; do
        for NUM in `seq 1 32`; do
            sudo ip netns exec namespace$NS ip link set dev eth$NUM down
            sudo ip netns exec namespace$NS ip link delete dev eth$NUM
        done
    done
}

case "$1" in
    start|stop)
        $1
        ;;
    *)
        echo "Usage: $0 {start|stop}"
        ;;
esac

