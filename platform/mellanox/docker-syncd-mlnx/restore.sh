#!/usr/bin/env bash

SYNCD_DUMP_DIR=/var/warmboot/syncd
SDK_DUMP_DIR=/var/warmboot/sdk
SHM_DUMP_DIR=/var/warmboot/shm
SHM_DIR=/dev/shm

if [ -d $SHM_DUMP_DIR ]; then
    cp -rf $SHM_DUMP_DIR/* $SHM_DIR/
    rm -rf $SHM_DUMP_DIR
fi

if [ -d $SDK_DUMP_DIR ]; then
    criu restore -d -D $SDK_DUMP_DIR --shell-job --ext-unix-sk
    rm -rf $SDK_DUMP_DIR
fi

if [ -d $SYNCD_DUMP_DIR ]; then
    criu restore -d -D $SYNCD_DUMP_DIR --shell-job --ext-unix-sk
    rm -rf $SYNCD_DUMP_DIR
fi
