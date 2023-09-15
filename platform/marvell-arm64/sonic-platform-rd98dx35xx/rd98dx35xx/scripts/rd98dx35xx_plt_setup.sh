#!/bin/bash

PLATFORM_AC5X="arm64-marvell_rd98DX35xx-r0"
MACH_FILE="/host/machine.conf"

fw_uboot_env_cfg()
{
    echo "Setting up U-Boot environment..."

    FW_ENV_DEFAULT='/dev/mtd0 0x400000 0x10000 0x10000'
    echo $FW_ENV_DEFAULT > /etc/fw_env.config
}

rd98DX35xx_profile()
{
    MAC_ADDR=$(fw_printenv -n ethaddr)
    find /usr/share/sonic/device/*rd98DX35xx* -name profile.ini | xargs sed -i "s/switchMacAddress=.*/switchMacAddress=$MAC_ADDR/g"
    echo "rd98DX35xx: Updating switch mac address ${MAC_ADDR}"
}

update_modulelist()
{
    MODULE_FILE="/etc/modules-load.d/marvell.conf"

    if grep -Fxq "mvMbusDrv" $MODULE_FILE
    then
        echo "Module list up to date"
    else
        echo "mvMbusDrv" >> $MODULE_FILE
        modprobe mvMbusDrv
    fi
}

main()
{
    if [ -f "$MACH_FILE" ]; then
        PLATFORM=`sed -n 's/^onie_platform=\(.*\)/\1/p' $MACH_FILE`
        if [ "$PLATFORM" = "$PLATFORM_AC5X" ]; then
            fw_uboot_env_cfg
            rd98DX35xx_profile
            update_modulelist
        fi
    fi
}

main $@
