#!/bin/bash

reboot_type='cold'

function get_database_reboot_type()
{
    SYSTEM_WARM_START=`/usr/bin/redis-cli -n 6 hget "WARM_RESTART_ENABLE_TABLE|system" enable`
    SYSTEM_FAST_START=`/usr/bin/redis-cli -n 6 get "FAST_REBOOT|system"`

    if [[ x"${SYSTEM_WARM_START}" == x"true" ]]; then
        reboot_type='warm'
    elif [[ x"${SYSTEM_FAST_START}" == x"1" ]]; then
        reboot_type='fast'
    fi
}

sonic-cfggen -d -t /usr/share/sonic/templates/ntp.conf.j2 >/etc/ntp.conf

get_database_reboot_type
if [[ x"${reboot_type}" == x"cold" ]]; then
    echo "Enabling NTP long jump for reboot type ${reboot_type} ..."
    sed -i "s/NTPD_OPTS='-x'/NTPD_OPTS='-g'/" /etc/default/ntp
else
    echo "Disabling NTP long jump for reboot type ${reboot_type} ..."
    sed -i "s/NTPD_OPTS='-g'/NTPD_OPTS='-x'/" /etc/default/ntp
fi

systemctl restart ntp
