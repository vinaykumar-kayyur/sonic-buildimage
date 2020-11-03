#!/usr/bin/env bash

# Container image version
# Acquires build image version as its version during build
#
IMAGE_VERSION="0.0.0"

if [ "${RUNTIME_OWNER}" == "" ]; then
    RUNTIME_OWNER="kube"
fi

/usr/share/sonic/scripts/container_state.py up -f lldp -o ${RUNTIME_OWNER} -v ${IMAGE_VERSION}

sonic-cfggen -d -t /usr/share/sonic/templates/lldpd.conf.j2 > /etc/lldpd.conf

mkdir -p /var/sonic
echo "# Config files managed by sonic-config-engine" > /var/sonic/config_status

rm -f /var/run/lldpd.socket
