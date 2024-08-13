#!/bin/bash

ntp_default_file='/etc/default/ntpsec'
ntp_temp_file='/tmp/ntp.orig'

reboot_type='cold'

function get_database_reboot_type()
{
    SYSTEM_WARM_START=`sonic-db-cli STATE_DB hget "WARM_RESTART_ENABLE_TABLE|system" enable`
    SYSTEM_FAST_START=`sonic-db-cli STATE_DB hget "FAST_RESTART_ENABLE_TABLE|system" enable`

    if [[ x"${SYSTEM_WARM_START}" == x"true" ]]; then
        reboot_type='warm'
    elif [[ x"${SYSTEM_FAST_START}" == x"true" ]]; then
        reboot_type='fast'
    fi
}

function modify_ntp_default
{
    cp ${ntp_default_file} ${ntp_temp_file}
    sed -e "$1" ${ntp_temp_file} >${ntp_default_file}
}

sonic-cfggen -d -t /usr/share/sonic/templates/ntp.conf.j2 >/etc/ntpsec/ntp.conf
sonic-cfggen -d -t /usr/share/sonic/templates/ntp.keys.j2 >/etc/ntpsec/ntp.keys
chmod o-r /etc/ntp.keys

get_database_reboot_type
echo "Disabling NTP long jump for reboot type ${reboot_type} ..."
modify_ntp_default "s/NTPD_OPTS=\"-g -N\"/NTPD_OPTS=\"-x -N\"/"

#Check for NTP_KEYS or NTP_SERVERS in CONFIG_DB 
ntp_config=$(redis-cli -n 4 keys *NTP_*)
if [ -n "$ntp_config" ]; then
    echo "Server information present in CONFIG_DB, NTP is restarted"
    systemctl --no-block restart ntp
else
    echo "No server information present in CONFIG_DB, NTP is not restarted"
fi
    

