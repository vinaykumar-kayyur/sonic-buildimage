#!/bin/bash

VRFNAME="mgmt"

vrfenabled=`/usr/bin/redis-cli -n 4 hget "MGMT_VRF_CONFIG|vrf_global" mgmtVrfEnabled`

if [ ! -f /var/run/netns/$VRFNAME ]
then
    logger "interfaces-config: management vrf is not enabled. Bringing down eth0 in default VRF."
	ifdown --force eth0
else
    logger "interfaces-config: management vrf is enabled. Bringing down eth0 in management VRF."
	ip netns exec $VRFNAME ifdown --force eth0

fi

sonic-cfggen -d -t /usr/share/sonic/templates/interfaces.j2 > /etc/network/interfaces

	if [ "$vrfenabled" == "true" ]
	then  
	
	    # Copy the respective netns file to the respective directories
	    logger "interfaces-config: vrfenabled is true. copying the netns scripts & generating interfaces.mgmt file"
	
	    cp /usr/bin/if_pre_up_netns /etc/network/if-pre-up.d/netns
	    cp /usr/bin/if_up_netns /etc/network/if-up.d/netns
	    cp /usr/bin/if_down_netns /etc/network/if-down.d/netns
	    
	    # create management namespace interfaces file which contains the eth0 and 
	    #  other management namespace interfaces.
	
	    sonic-cfggen -d -t /usr/share/sonic/templates/interfaces_mgmt.j2 > /etc/network/interfaces.$VRFNAME
	
	
	 #Following "elif" condition will be exceuted in two conditions. 1. First time fresh boot when vrfenabled variable itself is not there. 2. vrfenabled variable exists, but the value is not true (which is nothing but vrf is disabled.)

    	elif [ -f /var/run/netns/$VRFNAME ]
	then
        		logger "interfaces-config: vrfenabled flag is false. Removing netns files, deleting iptables from management vrf and deleting the management VRF"
	
	    if [ -f /etc/network/if-up.d/netns ]
	    then
		    rm /etc/network/if-up.d/netns
	    fi
	    if [ -f /etc/network/if-pre-up.d/netns ]
	    then
		    rm /etc/network/if-pre-up.d/netns
	    fi
	    if [ -f /etc/network/if-down.d/netns ]
	    then
		    rm /etc/network/if-down.d/netns
	    fi
	    if [ -f /etc/network/interfaces.$VRFNAME ]
	    then
		    rm /etc/network/interfaces.$VRFNAME
	    fi
        logger "interfaces-config: Deleting the management VRF"
	    ip netns del $VRFNAME
	fi

logger "interfaces-config: Adding usb0 interface for bfn platforms."

# Add usb0 interface for bfn platforms
platform=$(sonic-cfggen -H -v 'DEVICE_METADATA["localhost"]["platform"]')
if [[ "$platform" == "x86_64-accton_wedge100bf_32x-r0" || "$platform" == "x86_64-accton_wedge100bf_65x-r0" ]]; then
cat <<'EOF' >> /etc/network/interfaces
# BMC interface
auto usb0
allow-hotplug usb0
iface usb0 inet6 auto
up ifconfig usb0 txqueuelen 64
EOF
fi

logger "interfaces-config: Killing dhcp client."
[ -f /var/run/dhclient.eth0.pid ] && kill `cat /var/run/dhclient.eth0.pid` && rm -f /var/run/dhclient.eth0.pid

logger "interfaces-config: Restarting networking service."
systemctl restart networking

logger "interfaces-config: Bringing down loopback interfaces and bringing it back to up."
ifdown lo && ifup lo
