#!/usr/bin/env bash

set -x

start_bcm()
{
    [ -e /dev/linux-bcm-knet ] || mknod /dev/linux-bcm-knet c 122 0
    [ -e /dev/linux-user-bde ] || mknod /dev/linux-user-bde c 126 0
    [ -e /dev/linux-kernel-bde ] || mknod /dev/linux-kernel-bde c 127 0
}

PLATFORM_DIR=/usr/share/sonic/platform
HWSKU_DIR=/usr/share/sonic/hwsku

mkdir -p /etc/sai.d/

if [ -f $HWSKU_DIR/sai.profile ]; then
	cp $HWSKU_DIR/sai.profile /etc/sai.d/sai.profile

	SAI_CONFIG=`cat /etc/sai.d/sai.profile | rev | cut -d "/" -f1 | rev`

	ln -s $HWSKU_DIR/$SAI_CONFIG /tmp/brcm_sai_config.bcm
	ln -s $HWSKU_DIR/port_config.ini /tmp/port_config.ini

	parse_port_config.py > /tmp/test_config.ini
fi

start_bcm

exec /usr/bin/supervisord

