#!/usr/bin/env bash

supervisorctl start redis-server

# If there is a config db dump file, load it
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

