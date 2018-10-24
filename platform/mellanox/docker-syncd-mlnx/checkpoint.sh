#!/usr/bin/env bash

SYNCD_DUMP_DIR=/var/warmboot/syncd
SYNCD_PID=`pidof syncd`
SYNCD_EXTERNAL_ARGS=`ls -la /proc/$SYNCD_PID/fd | grep -ho "socket:\[[0-9]*\]" | sed "s/socket:/--external unix/g" | xargs`

SDK_DUMP_DIR=/var/warmboot/sdk
SDK_PID=`pidof sx_sdk`
SDK_EXTERNAL_ARGS=`ls -la /proc/$SDK_PID/fd | grep -ho "socket:\[[0-9]*\]" | sed "s/socket:/--external unix/g" | xargs`

SHM_DUMP_DIR=/var/warmboot/shm
SHM_DIR=/dev/shm

if [ -d $SYNCD_DUMP_DIR ]; then
    rm -rf $SYNCD_DUMP_DIR
fi

if [ -d $SDK_DUMP_DIR ]; then
    rm -rf $SDK_DUMP_DIR
fi

if [ -d $SHM_DUMP_DIR ]; then
    rm -rf $SHM_DUMP_DIR
fi

mkdir $SYNCD_DUMP_DIR
mkdir $SDK_DUMP_DIR
mkdir $SHM_DUMP_DIR

criu dump -D $SYNCD_DUMP_DIR -t $SYNCD_PID --shell-job $SYNCD_EXTERNAL_ARGS

criu dump -D $SDK_DUMP_DIR -t $SDK_PID --shell-job $SDK_EXTERNAL_ARGS

cp -rf $SHM_DIR/* $SHM_DUMP_DIR/
