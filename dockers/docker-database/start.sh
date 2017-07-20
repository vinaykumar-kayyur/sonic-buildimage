#!/usr/bin/env bash

supervisorctl start redis-server

# If there is a config db dump file, load it
if [ -r /etc/sonic/config_db.json ]; then
    # Wait until redis starts
    while true; do
        if [ `redis-cli ping` == $'PONG\r' ]; then
            break
        fi
        sleep 1
    done

    sonic-cfggen -j /etc/sonic/config_db.json -D
    echo $'select 4\nset CONFIG_DB_INITIALIZED true' | redis-cli

    echo 
fi

