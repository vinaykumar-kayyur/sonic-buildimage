#! /bin/bash

# Redirect any stdout & stderr into logger
#
exec 1> >(logger -s -t kube_join_stdout) 2>&1

API_SERVER=""
CURL_FLAGS=""
args_str=""

ASYNC_RUN=false
debug=false
oneshot=false
force=false
test_only=false

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
    if ! ${oneshot}; then
        log_info "Creating Cron job /usr/bin/kube_join.sh ${args_str}"
        ( crontab -l | grep -v "kube_join" ; echo "*/10 * * * * /usr/bin/kube_join.sh ${args_str}" ) | crontab -
    fi
}

drop_cron() {
    log_info "Dropping Cron job /usr/bin/kube_join.sh ${args_str}"
    ( crontab -l | grep -v "kube_join" ) | crontab -
}

download_file() {

    myfile=$(mktemp "${TMPDIR:-/tmp/}$(basename $0).XXXXXXXXXXXX")
    if ! curl -f -s ${CURL_FLAGS} -o ${myfile} https://${API_SERVER}/admin.conf; then
        log_err "Failed to download https://${API_SERVER}/admin.conf"
        create_cron
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

while getopts ":s:iadoft" opt
do
    case ${opt} in
        i ) # Do insecured pull
            CURL_FLAGS="${CURL_FLAGS} --insecure"
            args_str+=" -i"
            ;;
        o ) # Do one shot attempt
            oneshot=true
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
        f ) # Do one shot attempt
            force=true
            ;;
        t ) # Test only
            test_only=true
            ;;
        \? ) cat << EOF
Usage: [-i] [-a] [-d] [-s <API Server IP>] [-f]

    -s -- IP address of API server"
    -i -- Does insecure curl download of kubeconfig file 
    -a -- Async mode
    -d -- Debug mode
    -o -- Single shot
    -f -- Force join
    -t -- test only 
EOF
            exit -1
            ;;
    esac
done

if [ -z "${API_SERVER}" ]; then
    log_err "API SERVER IP address is required"
    exit 1
fi

if [ $EUID -ne 0 ]; then
    log_err "This script must be run as root" 
    exit 1
fi

if ! ${force}; then
    # check if already connected to this master
    if is_connected; then
        echo "Already connected to API Server: ${API_SERVER}; skip joining; You may override with -f"
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

set_env

# pre-requisite
modprobe br_netfilter

# Reset
log_info "Resetting kubeadm ..."
/usr/bin/kube_reset.sh -f
mkdir -p /var/lib/kubelet/

# Download kubeconfig file
download_file

# The server is reachable. drop cron.
echo "Drop cron, if any"
drop_cron


# Enable kubelet service which is disabled upon install
log_info "enable & start kubelet.service"
systemctl enable kubelet.service
systemctl start kubelet.service

# Call join
log_info "Calling kubeadm join command as suggested by master ..."
kubeadm join --discovery-file /etc/sonic/kube_admin.conf
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

node=`hostname`

ver=`grep build_version /etc/sonic/sonic_version.yml| cut -f2- -d' '`
log_info "Add label node=${node} sonic_version=${ver}"
kubectl --kubeconfig /etc/sonic/kube_admin.conf label nodes ${node} sonic_version=${ver}

type=`sudo redis-cli -n 4 hget "DEVICE_METADATA|localhost" type`
log_info "Add label node=${node} deployment_type=${type}"
kubectl --kubeconfig /etc/sonic/kube_admin.conf label nodes ${node} deployment_type=${type}

sku=`sudo redis-cli -n 4 hget "DEVICE_METADATA|localhost" hwsku`
log_info "Add label node=${node} hwsku=${sku}"
kubectl --kubeconfig /etc/sonic/kube_admin.conf label nodes ${node} hwsku=${sku}

echo "Joined successfully"

