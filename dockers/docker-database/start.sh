#!/usr/bin/env bash

supervisorctl start redis-server

# If this platform has an initialization file for the Broadcom LED microprocessor, load it
if [ -r /etc/sonic/config_db.json ]; then
    # Wait until redis starts
    while true; do
        if [ -e /var/run/redis/redis.sock ]; then
            break
        fi
        sleep 1
    done

    sonic-cfggen -j /etc/sonic/config_db.json -D
fi

