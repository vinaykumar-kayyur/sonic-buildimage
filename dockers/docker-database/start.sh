#!/usr/bin/env bash

# first, create all redis configuration files
create_all_redis_config

# then, generate all redis server supervisord configuration file
sonic-cfggen -j /etc/sonic/database_config.json -t /usr/share/sonic/templates/supervisord_database.conf.j2 > /etc/supervisor/conf.d/supervisord_database.conf

# finally, reread supervisord config files and start new added redis servers only
supervisorctl reread
supervisorctl update
