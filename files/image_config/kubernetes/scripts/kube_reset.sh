#! /bin/bash

# Redirect any stdout & stderr into logger
#
exec 1> >(logger -s -t kube_reset_stdout) 2>&1

do_reset=false
test_only=false

while getopts ":ft" opt
do
    case ${opt} in
        f ) # Force a reset
            do_reset=true
            ;;
        t ) # Force a reset
            test_only=true
            ;;
        \? ) cat << EOF
Usage: [-f]

    -f -- Force a reset
    -t -- test only. Reset action would be skipped
EOF
            exit -1
            ;;
    esac
done

if ! ${do_reset}; then
    # Force if the master's conf file is still present
    if [ -f /etc/sonic/kube_admin.conf ]; then
        do_reset=true
    fi
fi

if ! ${do_reset}; then
    #  Force if service is still enabled or running
    if [ -f /etc/systemd/system/multi-user.target.wants/kubelet.service ]; then
        do_reset=true
    else
        pid=`pidof kubelet`
        if [ -n "${pid}" ]; then
            do_reset=true
        fi
    fi
fi

if [ $EUID -ne 0 ]; then
    echo "This script must be run as root" 
    exit 1
fi

if ${test_only}; then
    if ${do_reset}; then
        echo "About to reset; But skipping as test only"
    else
        echo "reset is not required and not forced either"
    fi
    exit 0
fi

if ${do_reset}; then
    echo "Resetting kubeadm ..."
    kubeadm reset -f
    rm -rf /etc/cni/net.d
    sudo systemctl stop kubelet
    sudo systemctl disable kubelet
    rm -f /etc/sonic/kube_admin.conf
    echo "Give a pause ..."
    sleep 10s
fi
