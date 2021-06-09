#!/usr/bin/env bash

sonic-db-cli EVENT_DB config set  notify-keyspace-events AKE

cp /var/evprofile/default.json /etc/evprofile/default.json

exec /usr/local/bin/supervisord

