#! /bin/bash
## Check the platform PCIe device presence and status

VERBOSE="no"
RESULTS="PCIe Device Checking All Test"
PCIE_CHK_CMD=`sudo pcieutil pcie-check |grep "$RESULTS"`
EXPECTED="PCIe Device Checking All Test ----------->>> PASSED"
MAX_RESCAN=15

function debug()
{
    /usr/bin/logger "$0 : $1"
    if [[ x"${VERBOSE}" == x"yes" ]]; then
        echo "$(date) $0: $1"
    fi
}

function check_and_rescan_pcie_devices()
{
    PLATFORM=`sonic-cfggen -H -v DEVICE_METADATA.localhost.platform`
    if [ ! -f /usr/share/sonic/device/$PLATFORM/plugins/pcie.yaml ]; then
        debug "pcie.yaml does not exist! can't check pcie status!"
        exit
    fi

    for i in $(seq 1 1 $MAX_RESCAN)
    do
        if [ "$PCIE_CHK_CMD" = "$EXPECTED" ]; then
            redis-cli -n 6 SET "PCIE_STATUS|PCIE_DEVICES" "PASSED"
            debug "PCIe check passed"
            exit
        else
            debug "PCIe check failed, try pci bus rescan"
            echo 1 > /sys/bus/pci/rescan
         fi
         sleep 1
     done
     redis-cli -n 6 SET "PCIE_STATUS|PCIE_DEVICES" "FAILED"
}

check_and_rescan_pcie_devices
