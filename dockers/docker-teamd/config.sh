#!/bin/bash

mkdir -p /etc/teamd

for pc in `sonic-cfggen -m /etc/sonic/minigraph.xml --var-keys minigraph_portchannel_interfaces`; do
  sonic-cfggen -m /etc/sonic/minigraph.xml -a '{"pc":"'$pc'"}' -t teamd.j2 >/etc/teamd/$pc.conf
done

