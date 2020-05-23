#! /bin/bash

# Redirect any stdout & stderr into logger
#
exec 1> >(logger -s -t kube_join_stdout) 2>&1

API_SERVER=""
CURL_FLAGS=""
args_str=""

ASYNC_RUN=false
debug=false
force=false
test_only=false

take_lock() {
    # Check is Lock File exists, if not create it and set trap on exit
    if { set -C; 2>/dev/null >/var/lock/kube_join.lock; }; then
        trap "rm -f /var/lock/kube_join.lock" EXIT
    else
        echo "Lock file exists; exiting"
        exit
    fi

}

set_env() {
    # Required when running as CRON job
    export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
}

log_info() {
    logger -p local0.notice -t kube_join ${1}
    if $debug; then
        echo $1
    fi
}

log_err() {
    logger -p local0.error -t kube_join ${1}
    if $debug; then
        echo $1
    fi
}

create_cron() {
    log_info "Creating Cron job /usr/bin/kube_join.sh ${args_str}"
    ( crontab -l | grep -v "kube_join" ; echo "*/10 * * * * /usr/bin/kube_join.sh ${args_str}" ) | crontab -
}

drop_cron() {
    log_info "Dropping Cron job /usr/bin/kube_join.sh ${args_str}"
    ( crontab -l | grep -v "kube_join" ) | crontab -
}

download_file() {
    myfile=$(mktemp "${TMPDIR:-/tmp/}$(basename $0).XXXXXXXXXXXX")
    if ! curl -f -s ${CURL_FLAGS} -o ${myfile} https://${API_SERVER}/admin.conf; then
        log_err "Failed to download https://${API_SERVER}/admin.conf"
        exit -1
    fi
    cp ${myfile} /etc/sonic/kube_admin.conf
    rm -f ${myfile}
    log_info "Downloaded kubeconfig into /etc/sonic/kube_admin.conf"
}

is_connected() {
    pid=""
    if [ -f /etc/sonic/kube_admin.conf ]; then
        master=`kubectl --kubeconfig /etc/sonic/kube_admin.conf get nodes | grep master | cut -f1 -d' '`
        if [ -n ${master} ]; then
            pid=`kubectl --kubeconfig /etc/sonic/kube_admin.conf describe node ${master} | grep InternalIP | cut -f2- -d':' | tr -d '[:space:]'`
        fi
    fi
    if [ "${pid}" == "${API_SERVER}" ]; then
        return 0
    else
        return 1
    fi
}

usage() {
    cat << EOF
Usage: [-i] [-a] [-d] [-s <API Server IP>] [-f]

    -s -- IP address of API server
    -i -- Does insecure curl download of kubeconfig file 
    -a -- Async mode
    -d -- Debug mode
    -f -- Force join
    -t -- Test only 
EOF
}

while getopts ":s:iadft" opt
do
    case ${opt} in
        i ) # Do insecured pull
            CURL_FLAGS="${CURL_FLAGS} --insecure"
            args_str+=" -i"
            ;;
        a ) # Do asynchronous run
            ASYNC_RUN=true
            ;;
        d ) # Run in debug mode
            debug=true
            ;;
        s ) # IP Address of API server
            API_SERVER=${OPTARG}
            args_str+=" -s ${OPTARG}"
            ;;
        f ) # Force the join
            force=true
            ;;
        t ) # Test only
            test_only=true
            ;;
        \? ) # Usage
            usage
            exit -1
            ;;
    esac
done

if [ -z "${API_SERVER}" ]; then
    echo "API SERVER IP address is required"
    exit 1
fi

if [ $EUID -ne 0 ]; then
    echo "This script must be run as root" 
    exit 1
fi

if ! ${force}; then
    # check if already connected to this master
    if is_connected; then
        echo "Already connected to API Server: ${API_SERVER}; skip joining; You may override with -f"
        drop_cron
        exit 0
    fi
fi

if  ${test_only}; then
    echo "About to run reset & join; But skipped as test only"
    exit 0
fi

if $ASYNC_RUN
then
    create_cron
    exit 0
fi

# Take exclusive lock; Exits if fails.
take_lock

set_env

# pre-requisite
modprobe br_netfilter

# Reset
log_info "Resetting kubeadm ..."
/usr/bin/kube_reset.sh -f
mkdir -p /var/lib/kubelet/

# Download kubeconfig file; Exits if fails.
download_file

# Enable kubelet service which is disabled upon install
log_info "enable & start kubelet.service"
systemctl enable kubelet.service
systemctl start kubelet.service

# Coin nodename as "hostname" + "SONiC version", as same host with different versions
# are different instances of the same physical host from kubernetes perspective.
#
hname=`hostname | tr '[:upper:]' '[:lower:]'`
ver=`grep build_version /etc/sonic/sonic_version.yml| cut -f2- -d' '| tr -d "'"`
nodename=${hname}-${ver}

# Call join
log_info "Calling kubeadm join command as suggested by master ..."
kubeadm join --discovery-file /etc/sonic/kube_admin.conf --node-name ${nodename}
ret=$?

tmpf=$(mktemp "${TMPDIR:-/tmp/}$(basename $0).XXXXXXXXXXXX")
tee ${tmpf} > /dev/null <<   EOF
if join fails, check the following
    
a)  Ensure both master & node run same or compatible k8s versions 

b)  Check if this node already exists in master 
    Use 'sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get nodes' to list nodes at master. 
    
    If yes, delete it, as the node is attempting a new join. 
      'kubectl --kubeconfig=/etc/kubernetes/admin.conf drain <node name> --ignore-daemonsets'
      'kubectl --kubeconfig=/etc/kubernetes/admin.conf delete node <node name>' 
          
c) In Master check if all system pods are running good.
   'kubectl get pods --all-namespaces"
   
   If any not running properly, say READY column has 0/1, decribe pod for more detail.
   'kubectl --namespace kube-system describe pod <pod name>'

   For additional details, look into pod's logs.
   @ node: /var/log/pods/<podname>/...
   @ master: "kubectl logs -n kube-system <pod name>"
 
EOF

echo "If you need refer ${tmpf} for some troubleshooting tips"

# Pause for few seconds
log_info "Pause few seconds before adding label; sleep ..."
sleep 10s


log_info "Add label node=${nodename} sonic_version=${ver}"
kubectl --kubeconfig /etc/sonic/kube_admin.conf label nodes ${nodename} sonic_version=${ver}

type=`sudo redis-cli -n 4 hget "DEVICE_METADATA|localhost" type`
log_info "Add label node=${nodename} deployment_type=${type}"
kubectl --kubeconfig /etc/sonic/kube_admin.conf label nodes ${nodename} deployment_type=${type}

sku=`sudo redis-cli -n 4 hget "DEVICE_METADATA|localhost" hwsku`
log_info "Add label node=${nodename} hwsku=${sku}"
kubectl --kubeconfig /etc/sonic/kube_admin.conf label nodes ${nodename} hwsku=${sku}

log_info "Add label node=${nodename} enable_pods=true"
kubectl --kubeconfig /etc/sonic/kube_admin.conf label nodes ${nodename} enable_pods=true

echo "Joined successfully"

