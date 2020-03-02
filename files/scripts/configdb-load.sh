#!/usr/bin/env bash

# Wait until redis starts
until [[ $(redis-cli ping | grep -c PONG) -gt 0 ]]; do
  sleep 1;
done

# If there are init_cfg.json and config_db.json dump files, load them. Otherwise,
# loading one of them if it exists.
if [[ -r /etc/sonic/init_cfg.json ]] && [[ -r /etc/sonic/config_db.json ]]; then
    sonic-cfggen -j /etc/sonic/init_cfg.json -j /etc/sonic/config_db.json --write-to-db
elif [ -r /etc/sonic/init_cfg.json ]; then
    sonic-cfggen -j /etc/sonic/init_cfg.json --write-to-db
elif [ -r /etc/sonic/config_db.json ]; then
    sonic-cfggen -j /etc/sonic/config_db.json --write-to-db
fi

sonic-db-cli CONFIG_DB SET "CONFIG_DB_INITIALIZED" "1"
