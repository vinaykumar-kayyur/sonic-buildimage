#!/usr/bin/env bash
#
# Based on /etc/init.d/syncd

CMD_SYNCD=/usr/bin/syncd

CMD_DSSERVE=/usr/bin/dsserve
CMD_DSSERVE_ARGS="$CMD_SYNCD --diag"

ENABLE_SAITHRIFT=0

PLATFORM_DIR=/usr/share/sonic/platform
HWSKU_DIR=/usr/share/sonic/hwsku

if [ -x $CMD_DSSERVE ]; then
    CMD=$CMD_DSSERVE
    CMD_ARGS=$CMD_DSSERVE_ARGS
else
    CMD=$CMD_SYNCD
fi

parse_yaml() {
    local prefix=$2
    local s='[[:space:]]*' w='[a-zA-Z0-9_]*' fs=$(echo @|tr @ '\034')
    sed -ne "s|^\($s\)\($w\)$s:$s\"\(.*\)\"$s\$|\1$fs\2$fs\3|p" \
         -e "s|^\($s\)\($w\)$s:$s\(.*\)$s\$|\1$fs\2$fs\3|p"  $1 |
    awk -F$fs '{
        indent = length($1)/2;
        vname[indent] = $2;
        for (i in vname) {if (i > indent) {delete vname[i]}}
        if (length($3) > 0) {
           vn=""; for (i=0; i<indent; i++) {vn=(vn)(vname[i])("_")}
           printf("%s%s%s=\"%s\"\n", "'$prefix'",vn, $2, $3);
        }
     }'
}

start_bcm()
{
    [ -e /dev/linux-bcm-knet ] || mknod /dev/linux-bcm-knet c 122 0
    [ -e /dev/linux-user-bde ] || mknod /dev/linux-user-bde c 126 0
    [ -e /dev/linux-kernel-bde ] || mknod /dev/linux-kernel-bde c 127 0
}

start_mlnx()
{
    [ -e /dev/sxdevs/sxcdev ] || ( mkdir -p /dev/sxdevs && mknod /dev/sxdevs/sxcdev c 231 193 )

    # Read MAC address and align the last 6 bits.
    MAC_ADDRESS=`ip link show eth0 | grep ether | awk '{print $2}'`
    last_byte=`python -c "print '$MAC_ADDRESS'[-2:]"`
    aligned_last_byte=`python -c "print format(int(int('$last_byte', 16) & 0b11000000), '02x')"`  # put mask and take away the 0x prefix
    ALIGNED_MAC_ADDRESS=`python -c "print '$MAC_ADDRESS'[:-2] + '$aligned_last_byte'"`          # put aligned byte into the end of MAC

    # Write MAC address into /tmp/profile file.
    cat $HWSKU_DIR/sai.profile > /tmp/sai.profile
    echo "DEVICE_MAC_ADDRESS=$ALIGNED_MAC_ADDRESS" >> /tmp/sai.profile
}

start_centec()
{
    [ -e /dev/linux_dal ] || mknod /dev/linux_dal c 198 0
    [ -e /dev/net/tun ] || ( mkdir -p /dev/net && mknod /dev/net/tun c 10 200 )

    # Read MAC address and align the last 6 bits.
    MAC_ADDRESS=`ip link show eth0 | grep ether | awk '{print $2}'`
    last_byte=`python -c "print '$MAC_ADDRESS'[-2:]"`
    aligned_last_byte=`python -c "print format(int(int('$last_byte', 16) & 0b11000000), '02x')"`  # put mask and take away the 0x prefix
    ALIGNED_MAC_ADDRESS=`python -c "print '$MAC_ADDRESS'[:-2] + '$aligned_last_byte'"`          # put aligned byte into the end of MAC

    # Write MAC address into /tmp/profile file.

    # Write MAC address into /tmp/profile file.
    cat $HWSKU_DIR/sai.profile > /tmp/sai.profile
    echo "DEVICE_MAC_ADDRESS=$ALIGNED_MAC_ADDRESS" >> /tmp/sai.profile
}

start_cavium()
{
    export XP_ROOT=/usr/bin/
}

case "$(cat /proc/cmdline)" in
    *fast-reboot*)
        FAST_REBOOT='yes'
        ;;
    *)
        FAST_REBOOT='no'
        ;;
esac

eval $(parse_yaml /etc/sonic/sonic_version.yml "sonic_")

if [ $sonic_asic_type == "broadcom" ]; then
    start_bcm
    CMD_ARGS+=" -p $HWSKU_DIR/sai.profile "
    if [ $FAST_REBOOT == "yes" ];
    then
      CMD_ARGS+=" -t fast "
    fi
elif [ $sonic_asic_type == "mellanox" ]; then
    start_mlnx
    CMD_ARGS+=" -p /tmp/sai.profile "
elif [ $sonic_asic_type == "cavium" ]; then
    CMD_ARGS+=" -p $HWSKU_DIR/sai.profile "
    start_cavium
elif [ $sonic_asic_type == "centec" ]; then
    start_centec
    CMD_ARGS+=" -p /tmp/sai.profile "
else
    echo "Unknown asic type $sonic_asic_type"
    exit 1
fi

if [ ${ENABLE_SAITHRIFT} == 1 ]; then
    CMD_ARGS+=" -r -m $HWSKU_DIR/port_config.ini"
fi

[ -r $PLATFORM_DIR/syncd.conf ] && . $PLATFORM_DIR/syncd.conf

exec ${CMD} ${CMD_ARGS}

