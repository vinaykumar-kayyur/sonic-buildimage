#!/bin/bash

PREV_REBOOT_CAUSE="/host/reboot-cause/"
DEVICE="/usr/share/sonic/device"
PLATFORM=$(/usr/local/bin/sonic-cfggen -H -v DEVICE_METADATA.localhost.platform)
FILES=$DEVICE/$PLATFORM/api_files
PYTHON2_PACKAGE=$DEVICE/$PLATFORM/sonic_platform-1.0-py3-none-any.whl

install() {
    # Install python2 sonic-platform package
    if [ -e $PYTHON2_PACKAGE ]; then
        pip3 install $PYTHON2_PACKAGE        
    fi
}

init() {
    # mount needed files for sonic-platform package
    mkdir -p $FILES

    mkdir -p $FILES/reboot-cause
    mount -B $PREV_REBOOT_CAUSE $FILES/reboot-cause
}

deinit() {
    # deinit sonic-platform package
    umount -f $PREV_REBOOT_CAUSE $FILES/reboot-cause >/dev/null 2>/dev/null
}

uninstall() {
    # Uninstall sonic-platform package
    pip3 uninstall -y sonic-platform >/dev/null 2>/dev/null
}

case "$1" in
install | uninstall | init | deinit)
    $1
    ;;
*)
    echo "Usage: $0 {install|uninstall|init|deinit}"
    exit 1
    ;;
esac
