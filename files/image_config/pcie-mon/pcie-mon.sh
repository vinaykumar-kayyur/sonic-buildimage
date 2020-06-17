#! /bin/bash
## Check the platform PCIe device presence and status

VERBOSE=no
RESULTS="PCIe Device Checking All Test"
PASS="PASSED"
TEMP_PCIE_MON_F="/tmp/pcie-mon.txt"
STATUS=1
MAX_RESCAN=15

function debug()
{
    /usr/bin/logger "$0 : $1"
    if [[ x"${VERBOSE}" == x"yes" ]]; then
        echo "$(date) $0: $1"
    fi
}

function check_pcie_devices()
{
    show platform pcieinfo -c > $TEMP_PCIE_MON_F
    while read -r line;
    do
       debug "$line"
       if [[ $line =~ $RESULTS ]]; then
           if [[ $line =~ $PASS ]]; then
               STATUS=0 
           fi
        fi
    done < $TEMP_PCIE_MON_F
    rm $TEMP_PCIE_MON_F
    if [ $STATUS = 0 ]; then
        debug "PCIe check passed"
        return 0
    fi
    debug "PCIe check failed"
    return 1
}

function check_and_rescan_pcie_devices()
{
    i=0
    while [ $i -lt $MAX_RESCAN ];
    do
        ret=check_pcie_devices
        if [ $ret -eq 0]
            exit 0
        fi
        debug "PCIe RESCAN"
        echo 1 > /sys/bus/pci/rescan
        let "i+=1"
        sleep 1
    done
    exit 1
}

check_and_rescan_pcie_devices
