#!/usr/bin/env bash

set -e

function fast_reboot {
  case "$(cat /proc/cmdline)" in
    *fast-reboot*)
      if [[ -f /fdb.json ]];
      then
        swssconfig /fdb.json
        mv -f /fdb.json /fdb.json.1
      fi

      if [[ -f /arp.json ]];
      then
        swssconfig /arp.json
        mv -f /arp.json /arp.json.1
      fi

      if [[ -f /default_routes.json ]];
      then
        swssconfig /default_routes.json
        mv -f /default_routes.json /default_routes.json.1
      fi

      ;;
    *)
      ;;
  esac
}

function config_reload {
    if [[ -f /config-reload-restore ]];
    then
      if [[ -f /fdb.json ]];
      then
        swssconfig /fdb.json
        mv -f /fdb.json /fdb.json.1
      fi

      if [[ -f /arp.json ]];
      then
        mv -f /arp.json /arp.json.1
        # Tell kernel_arp_restore.sh that it needs to act
        touch /restore-kernel
      fi
      rm -f /config-reload-restore
    fi
}

# Wait until swss.sh in the host system create file swss:/ready
until [[ -e /ready ]]; do
    sleep 0.1;
done

rm -f /ready

# Restore FDB and ARP table ASAP
fast_reboot
config_reload

# read SONiC immutable variables
[ -f /etc/sonic/sonic-environment ] && . /etc/sonic/sonic-environment

HWSKU=${HWSKU:-`sonic-cfggen -d -v "DEVICE_METADATA['localhost']['hwsku']"`}

# Don't load json config if system warm start or
# swss docker warm start is enabled, the data already exists in appDB.
SYSTEM_WARM_START=`sonic-db-cli STATE_DB hget "WARM_RESTART_ENABLE_TABLE|system" enable`
SWSS_WARM_START=`sonic-db-cli STATE_DB hget "WARM_RESTART_ENABLE_TABLE|swss" enable`
if [[ "$SYSTEM_WARM_START" == "true" ]] || [[ "$SWSS_WARM_START" == "true" ]]; then
  exit 0
fi

SWSSCONFIG_ARGS="ipinip.json ports.json switch.json "

for file in $SWSSCONFIG_ARGS; do
    swssconfig /etc/swss/config.d/$file
    sleep 1
done
