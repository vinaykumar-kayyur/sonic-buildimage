#!/usr/bin/env bash

mkdir -p /var/sonic
echo "# Config files managed by sonic-config-engine" > /var/sonic/config_status

## TODO: symbolic links will be removed when AAA improvements get merged
ln -sf /host_etc/passwd /etc/passwd	
ln -sf /host_etc/group /etc/group
