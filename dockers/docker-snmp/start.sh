#!/usr/bin/env bash


if [ "${RUNTIME_OWNER}" == "" ]; then
    RUNTIME_OWNER="kube"
fi

CTR_SCRIPT="/usr/share/sonic/scripts/container_startup.py"
if test -f ${CTR_SCRIPT}
then
    ${CTR_SCRIPT} -f snmp -o ${RUNTIME_OWNER} -v ${IMAGE_VERSION}
fi

mkdir -p /etc/ssw /etc/snmp

# Parse snmp.yml and insert the data in Config DB
/usr/bin/snmp_yml_to_configdb.py

DOCKER0_V4=$(ip -4 addr show docker0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
DOCKER0_V6=$(ip -6 addr show docker0 scope global | grep -oP '(?<=inet6\s)[0-9a-fA-F:]+')
# Loopback0 interface will not exist on multi-asic device
if ip link show Loopback0 >/dev/null 2>&1; then
   LOOPBACK0_EXITS=true
fi

ADD_PARAM=$(printf '%s {"docker0_v4":"%s","docker0_v6":"%s","loopback0_exists":"%s"}' \
           "-a" "$DOCKER0_V4" "$DOCKER0_V6" "$LOOPBACK0_EXITS")

SONIC_CFGGEN_ARGS=" \
    -d \
    -y /etc/sonic/sonic_version.yml \
    -t /usr/share/sonic/templates/sysDescription.j2,/etc/ssw/sysDescription \
    -t /usr/share/sonic/templates/snmpd.conf.j2,/etc/snmp/snmpd.conf \
    $ADD_PARAM \
"

sonic-cfggen $SONIC_CFGGEN_ARGS

mkdir -p /var/sonic
echo "# Config files managed by sonic-config-engine" > /var/sonic/config_status
