#!/usr/bin/env bash

run_cmd () {
    echo "$1"
    eval $1
}

echo "Restart bgpd"

run_cmd "sonic-cfggen -d -y /etc/sonic/deployment_id_asn_map.yml -t /usr/share/sonic/templates/bgpd.conf.j2 > /etc/quagga/bgpd.conf"
run_cmd "supervisorctl stop bgpd"
run_cmd "sleep 1"
run_cmd "supervisorctl start bgpd"