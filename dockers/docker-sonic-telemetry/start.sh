#!/usr/bin/env bash

# Container image version
# Acquires build image version as its version during build
#
IMAGE_VERSION="0.0.0"

if [ "${RUNTIME_OWNER}" == "" ]; then
    RUNTIME_OWNER="kube"
fi

/usr/share/sonic/scripts/container_state.py up -f telemetry -o ${RUNTIME_OWNER} -v ${IMAGE_VERSION}

mkdir -p /var/sonic
echo "# Config files managed by sonic-config-engine" > /var/sonic/config_status
