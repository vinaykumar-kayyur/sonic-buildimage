#!/usr/bin/env bash

# Generate redis.conf files for each instance
create_all_redis_config

# Generate supervisord config file
conf_file="/etc/sonic/database_config.json"
sonic-cfggen -j $conf_file -t /usr/share/sonic/templates/docker-database.supervisord.conf.j2 > /etc/supervisor/conf.d/supervisord.conf

# The docker container should start this script as PID 1, so now that supervisord is
# properly configured, we exec supervisord so that it runs as PID 1 for the
# duration of the container's lifetime
exec /usr/bin/supervisord
