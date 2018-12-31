#!/bin//bash

set -e

VRFNAME="mgmt"

ip netns exec $VRFNAME iptables -t nat -A PREROUTING -i eth0 -j $IF_MGMT_VRF_CHAIN

ip netns exec $VRFNAME iptables -t nat -A POSTROUTING -p tcp -o $IF_PEER_IFACE -j SNAT --to-source $IF_IF1_IP:62000-65000
ip netns exec $VRFNAME iptables -t nat -A POSTROUTING -p udp -o $IF_PEER_IFACE -j SNAT --to-source $IF_IF1_IP:62000-65000

ip netns exec $VRFNAME iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

ip netns exec $VRFNAME iptables -t nat -A $IF_MGMT_VRF_CHAIN -p tcp --dport 22 -j DNAT --to-destination $IF_IF2_IP

ip netns exec $VRFNAME iptables -t nat -A $IF_MGMT_VRF_CHAIN -p tcp --dport 20 -j DNAT --to-destination $IF_IF2_IP

ip netns exec $VRFNAME iptables -t nat -A $IF_MGMT_VRF_CHAIN -p tcp --dport 21 -j DNAT --to-destination $IF_IF2_IP

ip netns exec $VRFNAME iptables -t nat -A $IF_MGMT_VRF_CHAIN -p udp --dport 161 -j DNAT --to-destination $IF_IF2_IP

ip netns exec $VRFNAME iptables -t nat -A $IF_MGMT_VRF_CHAIN -p udp --dport 69 -j DNAT --to-destination ${IF_IF2_IP}

ip netns exec $VRFNAME iptables -t nat -A $IF_MGMT_VRF_CHAIN -p tcp --dport 80 -j DNAT --to-destination $IF_IF2_IP

ip netns exec $VRFNAME iptables -t nat -A $IF_MGMT_VRF_CHAIN -p tcp --dport 443 -j DNAT --to-destination $IF_IF2_IP

