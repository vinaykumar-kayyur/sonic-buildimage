#!/bin/bash

/bin/cp -rf /etc/swss/lldp/lldpd.j2 /etc/default/lldpd

sonic-cfggen -m /etc/sonic/minigraph.xml -t /etc/swss/lldp/lldpd.conf.j2 >etc/lldpd.conf

