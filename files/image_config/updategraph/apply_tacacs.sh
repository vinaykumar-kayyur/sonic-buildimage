#! /bin/bash -e

if [ -r /etc/sonic/old_config/${TACACS_JSON_BACKUP} ]; then
    sonic-cfggen -j /etc/sonic/old_config/${TACACS_JSON_BACKUP} --write-to-db
    echo "Applied tacacs config from /etc/sonic/old_config/${TACACS_JSON_BACKUP}"
    config save -y
else
    echo "Missing tacacs json to restore tacacs credentials"
fi
