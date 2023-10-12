#!/usr/bin/env bash

cp /usr/share/sonic/templates/telemetry_vars.j2.${CONTAINER_NAME} /usr/share/sonic/templates/telemetry_vars.j2
cp /etc/supervisor/conf.d/supervisord.conf.${CONTAINER_NAME} /etc/supervisor/conf.d/supervisord.conf
cp /etc/supervisor/critical_processes.${CONTAINER_NAME} /etc/supervisor/critical_processes

exec /usr/local/bin/supervisord
