#!/bin/bash

mkdir -p /etc/sensors.d

hwsku=`sonic-cfggen -m /etc/sonic/minigraph.xml -v minigraph_hwsku`

if [ -e /usr/share/sonic/$hwsku/sensors.conf ]
then
  /bin/cp -rf /usr/share/sonic/$hwsku/sensors.conf /etc/sensors.d/
fi

