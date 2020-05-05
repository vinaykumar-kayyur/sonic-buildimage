#!/usr/bin/env bash

REDIS_DIR=/var/run/redis$NAMESPACE_ID
mkdir -p $REDIS_DIR/sonic-db

if [ -f /etc/sonic/database_config$NAMESPACE_ID.json ]; then
    cp /etc/sonic/database_config$NAMESPACE_ID.json $REDIS_DIR/sonic-db/database_config.json
else
    j2 /usr/share/sonic/templates/database_config.json.j2 > $REDIS_DIR/sonic-db/database_config.json
fi

mkdir -p /etc/supervisor/conf.d/

# copy/generate the database_global.json file if this is global database service in multi asic platform.
if [[ $NAMESPACE_ID == "" ]] && [[ $NAMESPACE_COUNT -gt 1 ]]
then
    if [ -f /etc/sonic/database_global.json ]; then
        cp /etc/sonic/database_global.json $REDIS_DIR/sonic-db/database_global.json
    else
        j2 /usr/share/sonic/templates/database_global.json.j2 > $REDIS_DIR/sonic-db/database_global.json
    fi
fi

# Touch a file "db_config_generated" once the database_config.json is created, used for synchronization.
if [ -f $REDIS_DIR/sonic-db/database_config.json ]; then
    touch $REDIS_DIR/db_config_generated
fi

# generate all redis server supervisord configuration file
sonic-cfggen -j /var/run/redis/sonic-db/database_config.json -t /usr/share/sonic/templates/supervisord.conf.j2 > /etc/supervisor/conf.d/supervisord.conf

exec /usr/bin/supervisord
