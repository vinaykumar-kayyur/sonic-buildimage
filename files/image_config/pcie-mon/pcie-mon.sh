#! /bin/bash
## Check the platform PCIe device presence and status

VERBOSE=no
RESULTS="PCIe Device Checking All Test"
PASS="PASSED"
TEMP_PCIE_MON_F="/tmp/pcie-mon.txt"
STATUS=1

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
	exit 0
    fi
    debug "PCIe check failed"
    exit 1
}

check_pcie_devices
