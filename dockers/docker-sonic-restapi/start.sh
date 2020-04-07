#!/usr/bin/env bash

mkdir -p /var/sonic
echo "# Config files managed by sonic-config-engine" > /var/sonic/config_status

rm -f /var/run/rsyslogd.pid

supervisorctl start rsyslogd

SERVER_CERT=/etc/sonic/certificates/restapiserver.crt
SERVER_KEY=/etc/sonic/certificates/restapiserver.key
CLIENT_CERT=/etc/sonic/certificates/restapiclient.crt

while [ : ]
do
    if [[ -f $SERVER_CERT && -f $SERVER_KEY && -f $CLIENT_CERT ]]; then
        supervisorctl start restapi
    fi
    sleep 5s
done