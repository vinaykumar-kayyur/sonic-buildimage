#!/bin/bash -e

sonic-cfggen -m /etc/sonic/minigraph.xml -t /usr/share/sonic/templates/ipinip.conf.j2 > /etc/swss/config.d/ipinip.conf
sonic-cfggen -m /etc/sonic/minigraph.xml -t /usr/share/sonic/templates/mirror.conf.j2 > /etc/swss/config.d/mirror.conf
