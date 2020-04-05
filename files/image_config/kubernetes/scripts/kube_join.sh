if [ ! -f /etc/sonic/kubeadm_join.sh ]
then
    echo "Run 'kubeadm token create --print-join-command' in Master."
    echo "please get join command in /etc/sonic/kubeadm_join.sh"
    exit -1
fi

if [ ! -f /etc/sonic/kube_admin.conf ]
then
    echo "please get kube context in /etc/sonic/kube_admin.conf"
    echo "It can be found @ master: /etc/kubernetes/admin.conf"
    exit -1
fi

# Reset
modprobe br_netfilter
# Reset
kubeadm reset -f
rm -rf /etc/cni/net.d
mkdir -p /var/lib/kubelet/

# Copy appropriate service config file 
systemctl enable kubelet.service
systemctl restart kubelet.service

# Give a pause before join
sleep 2

/etc/sonic/kubeadm_join.sh

# if join fails, ensure the following
# a) Ensure both master & node run same or compatible k8s versions
# b) If node already exists, delete it
#       "kubectl drain <node name> --ignore-daemonsets; kubectl delete node <node name>"
# c) If you are using calico, you *may* need to set the following in master.
#    Ensure calico.yaml has the following and apply at master.
#    # Auto-detection method.
#    - name: IP_AUTODETECTION_METHOD
#      value: "interface=<master route dev name>,eth0"
#     e.g. value: "interface=ens192,eth0"
# 
#    kubectl apply -f calico.yaml
# 
