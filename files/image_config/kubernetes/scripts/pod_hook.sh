#! /bin/bash

start() {
    # create /etc/sonic/pods/<container name>.pod with container id
    cat /proc/self/cgroup   | head -n1 | rev | cut -f1 -d'/' | rev > /etc/sonic/pods/$1.pod
}

stop() {
    rm -f /etc/sonic/pods/$1.pod
    mkdir -p /etc/sonic/pods/stopped
    rm -f /etc/sonic/pods/stopped/$1
    date -u > /etc/sonic/pods/stopped/$1
    date -u +%s >> /etc/sonic/pods/stopped/$1
    logger -p local0.notice -t "pod_stopped_$1" "pod $1 stopped"
}

case "$1" in
    start|stop)
        $1 $2
        if test -f ./$2.sh
        then
            ./$2_hook.sh $1
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop}"
        exit 1
        ;;
esac
