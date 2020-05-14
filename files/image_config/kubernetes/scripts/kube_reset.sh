#! /bin/bash

# Redirect any stdout & stderr into logger
#
exec 1> >(logger -s -t kube_reset_stdout) 2>&1


is_connected() {
    if [ -f /etc/sonic/kube_admin.conf ]; then
        master=`kubectl --request-timeout 5s --kubeconfig /etc/sonic/kube_admin.conf get nodes | grep master | cut -f1 -d' '`
        if [ -n "${master}" ]; then
            return 0
        fi
    fi
    return 1
}

drop_cron() {
    echo "Dropping Cron job /usr/bin/kube_join.sh"
    ( crontab -l | grep -v "kube_join" ) | crontab -
}

do_reset=false
test_only=false
do_drop_cron=false

while getopts ":fct" opt
do
    case ${opt} in
        f ) # Force a reset
            do_reset=true
            ;;
        c ) # Drop the CRON job
            do_drop_cron=true
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

# If there is a pending CRON job to join, drop it.
if ${do_drop_cron}; then
    drop_cron
fi

if ${do_reset}; then
    if is_connected; then
        hname=`hostname | tr '[:upper:]' '[:lower:]'`
        ver=`grep build_version /etc/sonic/sonic_version.yml| cut -f2- -d' '| tr -d "'"`
        nodename=${hname}-${ver}

        echo "Remove labels, drain & delete node ${nodename}"
        kubectl --request-timeout 15s --kubeconfig /etc/sonic/kube_admin.conf label nodes ${nodename} enable_pods-
        kubectl --request-timeout 25s --kubeconfig /etc/sonic/kube_admin.conf drain ${nodename} --ignore-daemonsets
        kubectl --request-timeout 25s --kubeconfig /etc/sonic/kube_admin.conf delete node ${nodename}
    fi


    echo "Resetting kubeadm ..."
    kubeadm reset -f
    rm -rf /etc/cni/net.d
    sudo systemctl stop kubelet
    sudo systemctl disable kubelet
    rm -f /etc/sonic/kube_admin.conf
    echo "Give a pause ..."
    sleep 10s
fi
