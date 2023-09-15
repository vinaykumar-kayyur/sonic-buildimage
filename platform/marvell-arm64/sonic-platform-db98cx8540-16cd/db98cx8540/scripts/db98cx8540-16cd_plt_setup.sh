#!/bin/bash

PLATFORM_FALCON="arm64-marvell_db98cx8540_16cd-r0"
MACH_FILE="/host/machine.conf"

db98cx8540_profile()
{
    MAC_ADDR=$(fw_printenv -n ethaddr)
    find /usr/share/sonic/device/*db98cx* -name profile.ini | xargs sed -i "s/switchMacAddress=.*/switchMacAddress=$MAC_ADDR/g"
    echo "db98cx8540: Updating switch mac address ${MAC_ADDR}"
}

main()
{
    if [ -f "$MACH_FILE" ]; then
        PLATFORM=`sed -n 's/onie_platform=\(.*\)/\1/p' $MACH_FILE`
        if [ "$PLATFORM" = "$PLATFORM_FALCON" ]; then
            db98cx8540_profile
        fi
    fi
}

main $@
