#!/usr/bin/env bash

REDIS_DIR=/var/run/redis$NAMESPACE_ID
mkdir -p $REDIS_DIR/sonic-db

if [ -f /etc/sonic/database_config$NAMESPACE_ID.json ]; then
    cp /etc/sonic/database_config$NAMESPACE_ID.json $REDIS_DIR/sonic-db/database_config.json
else
    python -c "import sys;import jinja2;loader = jinja2.FileSystemLoader('/usr/share/sonic/templates/');\
               env = jinja2.Environment(loader=loader, trim_blocks=True);template = env.get_template('database_config.json.j2');\
               print(template.render(NAMESPACE=sys.argv[1]))" "$NAMESPACE_ID" > $REDIS_DIR/sonic-db/database_config.json
fi

mkdir -p /etc/supervisor/conf.d/

# copy/generate the database_global.json file if this is global database service in multi asic platform.
if [[ $NAMESPACE_ID == "" ]] && [[ $NAMESPACE_COUNT -gt 1 ]]
then
    if [ -f /etc/sonic/database_global.json ]; then
        cp /etc/sonic/database_global.json $REDIS_DIR/sonic-db/database_global.json
    else
        python -c "import sys;import jinja2;loader = jinja2.FileSystemLoader('/usr/share/sonic/templates/');\
                   env = jinja2.Environment(loader=loader, trim_blocks=True);template = env.get_template('database_global.json.j2');\
                   print(template.render(PREFIX=sys.argv[1], NAMESPACE_CNT=sys.argv[2]))" "$NAMESPACE_PREFIX" \
                   "$NAMESPACE_COUNT" > $REDIS_DIR/sonic-db/database_global.json
    fi
fi

# generate all redis server supervisord configuration file
sonic-cfggen -j /var/run/redis/sonic-db/database_config.json -t /usr/share/sonic/templates/supervisord.conf.j2 > /etc/supervisor/conf.d/supervisord.conf

exec /usr/bin/supervisord
