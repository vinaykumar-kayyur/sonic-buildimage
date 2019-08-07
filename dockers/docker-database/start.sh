#!/usr/bin/env bash

mkdir -p /var/run/redis/
if [ -f /etc/sonic/database_config.json ]; then
    cp /etc/sonic/database_config.json /var/run/redis/
else
    cp /usr/share/sonic/config/database_config.json /var/run/redis/
fi

# first, create all redis configuration files
create_all_redis_config

# then, generate all redis server supervisord configuration file
sonic-cfggen -j /var/run/redis/database_config.json -t /usr/share/sonic/templates/supervisord_database.conf.j2 > /etc/supervisor/conf.d/supervisord_database.conf

# finally, reread supervisord config files and start new added redis servers only
supervisorctl reread
supervisorctl update
