#! /bin/bash

if [ "${RUNTIME_OWNER}" == "" ]; then
    RUNTIME_OWNER="kube"
fi

/usr/share/sonic/scripts/container_state.py up -f radv -o ${RUNTIME_OWNER} -v ${IMAGE_VERSION}
