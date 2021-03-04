#!/bin/bash
iSMART="/usr/local/bin/iSMART_64"
iSMART_OPTIONS="-d /dev/sda"

iSMART_CMD=`$iSMART $iSMART_OPTIONS`

GPIO_STATUS=$(echo "$iSMART_CMD" | grep GPIO | rev | cut -d' ' -f 2 | rev)

if [ $GPIO_STATUS != "0x01" ];then
    logger -p user.crit -t DELL_S6100_SSD_MON "The SSD on this unit is faulty and does not support cold reboot."
    logger -p user.crit -t DELL_S6100_SSD_MON "If a reboot is required, please perform a soft-/fast-/warm-reboot"
fi
