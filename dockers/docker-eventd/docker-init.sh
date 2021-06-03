#!/usr/bin/env bash

sonic-db-cli EVENT_DB config set  notify-keyspace-events AKE
sed -i '/username=/d' /etc/supervisor/supervisord.conf
sed -i '/password=/d' /etc/supervisor/supervisord.conf

cp /var/evprofile/default.json /etc/evprofile/default.json

exec /usr/bin/supervisord

