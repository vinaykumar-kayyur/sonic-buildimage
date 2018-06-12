#!/usr/bin/env bash

TEAMD_CONF_PATH=/etc/teamd

rm -rf $TEAMD_CONF_PATH
mkdir -p $TEAMD_CONF_PATH

SONIC_ASIC_TYPE=$(sonic-cfggen -y /etc/sonic/sonic_version.yml -v asic_type)

if [ "$SONIC_ASIC_TYPE" == "mellanox" ]; then
    MAC_ADDRESS=$(od -vt x1 -An /sys/bus/i2c/devices/8-0051/eeprom | xargs printf "0x%s " | xargs printf "%02x:" | awk 'BEGIN { FS=":"; i=8+1+2+1} {while(i<NF) {type=$i; len=("0x"$(i+1));if(type!="24") {i=i+2+len} else {print substr($0, (i+1)*3+1, len*3-1); break}}}')
else
    MAC_ADDRESS=$(ip link show eth0 | grep ether | awk '{print $2}')
fi

# Align last byte
if [ "$SONIC_ASIC_TYPE" == "mellanox" -o "$SONIC_ASIC_TYPE" == "centec" ]; then
    last_byte=$(python -c "print '$MAC_ADDRESS'[-2:]")
    aligned_last_byte=$(python -c "print format(int(int('$last_byte', 16) & 0b11000000), '02x')")  # put mask and take away the 0x prefix
    MAC_ADDRESS=$(python -c "print '$MAC_ADDRESS'[:-2] + '$aligned_last_byte'")                    # put aligned byte into the end of MAC
fi

for pc in `sonic-cfggen -d -v "PORTCHANNEL.keys() | join(' ') if PORTCHANNEL"`; do
    sonic-cfggen -d -a '{"pc":"'$pc'","hwaddr":"'$MAC_ADDRESS'"}' -t /usr/share/sonic/templates/teamd.j2 > $TEAMD_CONF_PATH/$pc.conf
    # bring down all member ports before starting teamd
    for member in $(sonic-cfggen -d -v "PORTCHANNEL['$pc']['members'] | join(' ')" ); do
        if [ -L /sys/class/net/$member ]; then
            ip link set $member down
        fi
    done
done

mkdir -p /var/sonic
echo "# Config files managed by sonic-config-engine" > /var/sonic/config_status

rm -f /var/run/rsyslogd.pid

supervisorctl start rsyslogd

supervisorctl start teamd
