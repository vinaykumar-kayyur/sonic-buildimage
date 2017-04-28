#!/bin/bash

ifdown -a -X eth0
sonic-cfggen -m /etc/sonic/minigraph.xml -t /usr/share/sonic/templates/interfaces.j2 >/etc/network/interfaces
ifup -a -X eth0

NEW_MGMT_IP=`sonic-cfggen -m /etc/sonic/minigraph.xml  -v 'minigraph_mgmt_interface["addr"]'`
NEW_MGMT_MASK=`sonic-cfggen -m /etc/sonic/minigraph.xml  -v 'minigraph_mgmt_interface["mask"]'`

ifconfig eth0 $NEW_MGMT_IP netmask $NEW_MGMT_MASK

