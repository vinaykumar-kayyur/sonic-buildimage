#!/usr/bin/env bash

PLATFORM=$(sonic-cfggen -v "platform")

# If this is an Arista platform newer than the 7050, do not start caclmgrd.
# Newer Arista devices will use their own service ACL manager instead.
if [ "$(echo $PLATFORM | grep -v "7050" | grep -c "arista")" -gt 0 ]; then
    echo "Not starting caclmgrd - unsupported platform"
    exit 0
fi

exec /usr/bin/caclmgrd
