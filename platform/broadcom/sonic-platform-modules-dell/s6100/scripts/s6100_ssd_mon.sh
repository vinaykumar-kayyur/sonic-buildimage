#!/bin/bash
iSMART="/usr/local/bin/iSMART_64"
iSMART_OPTIONS="-d /dev/sda"

iSMART_CMD=`$iSMART $iSMART_OPTIONS`

GPIO_STATUS=$(echo "$iSMART_CMD" | grep GPIO | rev | cut -d' ' -f 2 | rev)

if [ $GPIO_STATUS != "0x01" ];then
    logger -p user.crit -t DELL_S6100_SSD_MON "The SSD on this unit does not support reboot.\
        Please perform a warm/fast-reboot instead."
fi
