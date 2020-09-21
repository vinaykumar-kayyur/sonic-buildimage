#! /bin/bash

# This version is per docker. To be updated upon updates.
# Hence this could be different from version of other features
IMAGE_VERSION = "1.0.0"

if [ "${RUNTIME_OWNER}" == "" ]; then
    RUNTIME_OWNER="local"
fi

/usr/bin/container_state.py up -f snmp -o ${RUNTIME_OWNER} -v ${IMAGE_VERSION}
