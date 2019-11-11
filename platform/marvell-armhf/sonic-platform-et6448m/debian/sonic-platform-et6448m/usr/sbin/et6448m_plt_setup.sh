#!/bin/bash


et6448m_profile()
{
    MAC_ADDR=$(fw_printenv -n ethaddr)
    sed -i "s/switchMacAddress=.*/switchMacAddress=$MAC_ADDR/g" /usr/share/sonic/device/armhf-marvell_et6448m_52x-r0/et6448m/profile.ini
    echo "ET6448M: Updating switch mac address ${MAC_ADDR}"
}

main()
{
    et6448m_profile
}

main $@
