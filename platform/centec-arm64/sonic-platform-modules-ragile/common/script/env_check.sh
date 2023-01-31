#!/bin/bash
<<!
 **********************************************************
 * Author        : linxingqiang
 * Email         : support@ragilenetworks.com
 * Last modified : 2019-03-15
 * Filename      : env_check.sh
 * Description   : check sonic environment
 * *******************************************************
!

CONFIG_DB_JSON=/etc/sonic/config_db.json
MACHINE_CONF=/host/machine.conf
ENV_CHECK_SH=env_check.sh

echo "Sonic environmental monitoring begin"
echo "==============================================="
if [ ! -f $CONFIG_DB_JSON ];then
    echo "$CONFIG_DB_JSON:No such file"
    logger -t $ENV_CHECK_SH "$CONFIG_DB_JSON:No such file"
else
    size=`ls -al $CONFIG_DB_JSON | awk '{print $5}'`
    if [ "$size" -eq 0 ];then
        echo "$CONFIG_DB_JSON is empty"
        logger -t $ENV_CHECK_SH "$CONFIG_DB_JSON is empty"
    else
        echo "$CONFIG_DB_JSON is Available"
    fi
fi

if [  -f $MACHINE_CONF ];then
    machine_platform_name=`cat $MACHINE_CONF | grep onie_build_platform | awk -F= '{print $2}'`
    sys_platform_name=`show plat sys | grep Platform | awk '{print $5}'`
    if [ -z $machine_platform_name ];then
        echo "$MACHINE_CONF can't find onie_build_platform's keyword"
        logger -t $ENV_CHECK_SH "$MACHINE_CONF can't find onie_build_platform"
    else
        if [ $machine_platform_name != $sys_platform_name ];then
            echo "platform name in $MACHINE_CONF is not equal to platform name in 'show plat sys'"
            logger -t $ENV_CHECK_SH "platform name in $MACHINE_CONF is not equal to platform name in 'show plat sys'"
        fi
    fi
else
    echo "$MACHINE_CONF:No such file"
    logger -t $ENV_CHECK_SH "$MACHINE_CONF:No such file"
fi

status_pmon_log="systemctl status pmon"
status_pmon=`$status_pmon_log | grep "Active:" | grep "running"`
if [ -z "$status_pmon" ];then
    echo "pmon service started fail"
    logger -t $ENV_CHECK_SH "`$status_pmon_log`"
else
    echo "pmon service is running"
fi

status_device_i2c_log="systemctl status device_i2c.service"
status_device_i2c=`$status_device_i2c_log | grep "Active:" | grep "active (exited)"`
if [ -z "$status_device_i2c" ];then
    echo "device_i2c service started fail"
    logger -t $ENV_CHECK_SH "`$status_device_i2c_log`"
else
    echo "device_i2c service exited normally"
fi

status_device_init_log="systemctl status device_init.service"
status_device_init=`$status_device_init_log | grep "Active:" | grep "active (exited)"`
if [ -z "$status_device_init" ];then
    echo "device_init service started fail"
    logger -t $ENV_CHECK_SH "`$status_device_init_log`"
else
    echo "device_init service exited normally"
fi

syncd_count=`ps aux | grep syncd | grep "/usr/bin/syncd --diag -u -p /etc/sai.d/sai.profile" | grep -v grep | wc -l`
if [ $syncd_count -lt 3 ];then
    echo "syncd count is less than 3"
    logger -t $ENV_CHECK_SH "syncd count is less than 3"
fi

echo "==============================================="
echo "Sonic environmental monitoring end"
