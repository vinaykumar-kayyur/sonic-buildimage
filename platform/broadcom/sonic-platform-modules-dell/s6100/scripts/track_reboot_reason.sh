#!/bin/bash

reboot_dir_found=false
reboot_file_found=false

REBOOT_CAUSE_FILE=/host/reboot-cause/reboot-cause.txt
REBOOT_REASON=/host/reboot-cause/platform/reboot_reason
SMF_POWERON_REASON=/sys/devices/platform/SMF.512/hwmon/*/smf_poweron_reason
SMF_RESET_REASON=/sys/devices/platform/SMF.512/hwmon/*/smf_reset_reason
MAILBOX_POWERON_REASON=/sys/devices/platform/SMF.512/hwmon/*/mb_poweron_reason

if [[ -d /host/reboot-cause/platform ]]; then
    reboot_dir_found=true
    if [[ -f $REBOOT_REASON ]]; then
        reboot_file_found=true
    fi
fi

_is_thermal_reset() {
    prev_thermal=$(cat $REBOOT_REASON)
    curr_poweron_reason=$(cat $SMF_POWERON_REASON)
    if [[ $curr_poweron_reason = "11" ]]; then
       echo 0
       return 0
    fi
    if [[ $prev_thermal = $curr_poweron_reason ]]; then
        echo 2
        return 2
    else
        echo "$curr_poweron_reason" > $REBOOT_REASON
        echo 1
        return 1
    fi

    echo 0
    return 0
}

_is_watchdog_reset(){
    curr_reset_reason=$(cat $SMF_RESET_REASON)
    if [[ $curr_reset_reason = "33" ]]; then
        echo 1
        return 1
    fi

    echo 0
    return 0
}

_is_unknown_reset(){
    if [[ -f $REBOOT_CAUSE_FILE ]]; then
	if [[ $1 = 0 ]]; then
	    echo "Unknown software reboot" > $REBOOT_CAUSE_FILE
	    return
	fi
        curr_poweron_reason=$(cat $SMF_POWERON_REASON)
	curr_reset_reason=$(cat $SMF_RESET_REASON)
	mb_poweron_reason=$(cat $MAILBOX_POWERON_REASON)
	echo "Unknown POR: $curr_poweron_reason RST: $curr_reset_reason MBR: $mb_poweron_reason" > $REBOOT_CAUSE_FILE
    fi
    
}

update_mailbox_register(){
    if [[ $reboot_file_found = false ]]; then
        echo "None" > $REBOOT_REASON
    fi

    if [[ -d /sys/devices/platform/SMF.512/hwmon/ ]]; then
        is_thermal_reboot=$(_is_thermal_reset)

        is_wd_reboot=$(_is_watchdog_reset)

        rv=$(cat $MAILBOX_POWERON_REASON)
        reason=$(echo $rv | cut -d 'x' -f2)
        if [[ $reason = "ff" ]]; then
            echo "None" > $REBOOT_REASON
            if [[ -e /tmp/notify_firstboot_to_platform ]]; then
                echo 0x01 > $MAILBOX_POWERON_REASON
            else
                echo 0xbb > $MAILBOX_POWERON_REASON
            fi
        elif [[ $is_thermal_reboot = 1 ]]; then
            echo 0xee > $MAILBOX_POWERON_REASON
        elif [[ $is_wd_reboot = 1 ]] && [[ $reason != "cc" ]]; then
            echo 0xdd > $MAILBOX_POWERON_REASON
        elif [[ $reason = "cc" ]]; then
            echo 0xaa > $MAILBOX_POWERON_REASON
        else
	    _is_unknown_reset $is_thermal_reboot
            echo 0x99 > $MAILBOX_POWERON_REASON
        fi
    fi
}

update_mailbox_register
