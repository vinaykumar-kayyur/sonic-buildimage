#!/bin/bash -e

# Set correct platform string

HWSKU=$(sonic-cfggen -m -v DEVICE_METADATA.localhost.hwsku)
platform=$(find /usr/share/sonic/device -name $HWSKU | sed 's/.*\(x86.*\)\/.*/\1/')

mkdir -p /host
echo "onie_platform=$platform" > /host/machine.conf

# generate configuration

if [ -r /etc/sonic/minigraph.xml ]; then
   sonic-cfggen -m -H --write-to-db
fi

[ -d /etc/sonic ] || mkdir -p /etc/sonic

SYSTEM_MAC_ADDRESS=$(ip link show eth0 | grep ether | awk '{print $2}')
sonic-cfggen -a '{"DEVICE_METADATA":{"localhost": {"mac": "'$SYSTEM_MAC_ADDRESS'"}}}' --print-data > /etc/sonic/init_cfg.json

if [ -f /etc/sonic/config_db.json ]; then
    sonic-cfggen -j /etc/sonic/config_db.json -j /etc/sonic/init_cfg.json --print-data > /tmp/config_db.json
    mv /tmp/config_db.json /etc/sonic/config_db.json
else
    # generate and merge buffers configuration into config file
    sonic-cfggen -t /usr/share/sonic/device/vswitch/buffers.json.j2 > /tmp/buffers.json
    sonic-cfggen -j /etc/sonic/init_cfg.json -j /tmp/buffers.json --print-data > /etc/sonic/config_db.json
fi

mkdir -p /etc/swss/config.d/

rm -f /var/run/rsyslogd.pid

supervisorctl start rsyslogd

mkdir -p /var/run/redis

supervisorctl start redis-server

/usr/bin/configdb-load.sh

# from interfaces-config.sh
# not adding usb0 interface for bfn platform
# to add support for ipv6
sysctl -w net.ipv6.conf.all.disable_ipv6=0
ifdown --force eth0
sonic-cfggen -d -t /usr/share/sonic/templates/interfaces.j2 > /etc/network/interfaces
[ -f /var/run/dhclient.eth0.pid ] && kill `cat /var/run/dhclient.eth0.pid` && rm -f /var/run/dhclient.eth0.pid
service networking restart
ifdown lo && ifup lo
#

supervisorctl start syncd

supervisorctl start orchagent

supervisorctl start portsyncd

supervisorctl start intfsyncd

supervisorctl start neighsyncd

supervisorctl start teamsyncd

# started by quagga below
# supervisorctl start fpmsyncd

supervisorctl start portmgrd

supervisorctl start intfmgrd

supervisorctl start vlanmgrd

# started by quagga below
# supervisorctl start zebra

supervisorctl start buffermgrd

# Start arp_update when VLAN exists
VLAN=`sonic-cfggen -d -v 'VLAN.keys() | join(" ") if VLAN'`
if [ "$VLAN" != "" ]; then
    supervisorctl start arp_update
fi


# from teamd start.sh

TEAMD_CONF_PATH=/etc/teamd

rm -rf $TEAMD_CONF_PATH
mkdir -p $TEAMD_CONF_PATH

SONIC_ASIC_TYPE=$(sonic-cfggen -y /etc/sonic/sonic_version.yml -v asic_type)

if [ "$SONIC_ASIC_TYPE" == "mellanox" ]; then
    MAC_ADDRESS=$(sonic-cfggen -d -v DEVICE_METADATA.localhost.mac)
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

#rsyslog already included above
#rm -f /var/run/rsyslogd.pid
#supervisorctl start rsyslogd

supervisorctl start teamd
#

# from quagga start.sh
mkdir -p /etc/quagga
sonic-cfggen -d -y /etc/sonic/deployment_id_asn_map.yml -t /usr/share/sonic/templates/bgpd.conf.j2 > /etc/quagga/bgpd.conf
sonic-cfggen -d -t /usr/share/sonic/templates/zebra.conf.j2 > /etc/quagga/zebra.conf

sonic-cfggen -d -t /usr/share/sonic/templates/isolate.j2 > /usr/sbin/bgp-isolate
chown root:root /usr/sbin/bgp-isolate
chmod 0755 /usr/sbin/bgp-isolate

sonic-cfggen -d -t /usr/share/sonic/templates/unisolate.j2 > /usr/sbin/bgp-unisolate
chown root:root /usr/sbin/bgp-unisolate
chmod 0755 /usr/sbin/bgp-unisolate

mkdir -p /var/sonic
echo "# Config files managed by sonic-config-engine" > /var/sonic/config_status

# rm -f /var/run/rsyslogd.pid

supervisorctl start bgpcfgd

# started already
# supervisorctl start rsyslogd

# Start Quagga processes

supervisorctl start zebra

supervisorctl start bgpd

supervisorctl start fpmsyncd

