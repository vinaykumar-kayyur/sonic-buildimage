#!/usr/bin/env bash

# Check and load SDE profile
P4_PROFILE=$(sonic-cfggen -d -v 'DEVICE_METADATA["localhost"]["p4_profile"]')
if [[ -n "$P4_PROFILE" ]]; then
    if [[ ( -d /opt/bfn/install_${P4_PROFILE} ) && ( -L /opt/bfn/install || ! -e /opt/bfn/install ) ]]; then
        ln -srfn /opt/bfn/install_${P4_PROFILE} /opt/bfn/install
    fi
fi
export PYTHONHOME=/opt/bfn/install/
export PYTHONPATH=/opt/bfn/install/
export ONIE_PLATFORM=`grep onie_platform /etc/machine.conf | awk 'BEGIN { FS = "=" } ; { print $2 }'`
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/bfn/install/lib:/opt/bfn/install/lib/platform/$ONIE_PLATFORM:/opt/bfn/install/lib:/opt/bfn/install/lib/tofinopd/switch
./opt/bfn/install/bin/dma_setup.sh
/usr/sbin/saiserver -p /etc/sai/profile.ini -f /etc/sai/portmap.ini