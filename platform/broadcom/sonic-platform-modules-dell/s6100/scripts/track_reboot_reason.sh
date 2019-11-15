#!/bin/bash

reboot_dir_found=false
reboot_file_found=false

if [[ -d /host/reboot-cause/platform ]]; then
    reboot_dir_found=true
    if [[ -f /host/reboot-cause/platform/reboot_reason ]]; then
        reboot_file_found=true
    fi
fi

is_thermal_reset() {
    prev_thermal=$(cat /host/reboot-cause/platform/reboot_reason)
    curr_poweron_reason=$(cat /sys/devices/platform/SMF.512/hwmon/*/smf_poweron_reason)
    if [[ $curr_poweron_reason = "11" ]]; then
       echo 0
       return 0
    fi
    if [[ $prev_thermal = $curr_poweron_reason ]]; then
        echo 0
        return 0
    else
        echo "$curr_poweron_reason" > /host/reboot-cause/platform/reboot_reason
        echo 1
        return 1
    fi

    echo 0
    return 0
}

is_watchdog_reset(){
    curr_reset_reason=$(cat /sys/devices/platform/SMF.512/hwmon/*/smf_reset_reason)
    if [[ $curr_reset_reason = "33" ]]; then
        echo 1
        return 1
    fi

    echo 0
    return 0
}

_track_reboot_reason(){
    if [[ $reboot_file_found = false ]]; then
        echo "None" > /host/reboot-cause/platform/reboot_reason
    fi

    if [[ -d /sys/devices/platform/SMF.512/hwmon/ ]]; then
        is_thermal_reboot=$(is_thermal_reset)

        is_wd_reboot=$(is_watchdog_reset)

        rv=$(cat /sys/devices/platform/SMF.512/hwmon/*/mb_poweron_reason)
        reason=$(echo $rv | cut -d 'x' -f2)
        if [[ $reason = "ff" ]]; then
            echo "None" > /host/reboot-cause/platform/reboot_reason
            if [[ -e /tmp/notify_firstboot_to_platform ]]; then
                echo 0x01 > /sys/devices/platform/SMF.512/hwmon/*/mb_poweron_reason
            else
                echo 0xbb > /sys/devices/platform/SMF.512/hwmon/*/mb_poweron_reason
            fi
        elif [[ $is_thermal_reboot = 1 ]]; then
            echo 0xee > /sys/devices/platform/SMF.512/hwmon/*/mb_poweron_reason
        elif [[ $is_wd_reboot = 1 ]] && [[ $reason != "cc" ]]; then
            echo 0xdd > /sys/devices/platform/SMF.512/hwmon/*/mb_poweron_reason
        elif [[ $reason = "cc" ]]; then
            echo 0xaa > /sys/devices/platform/SMF.512/hwmon/*/mb_poweron_reason
        else
            echo 0x99 > /sys/devices/platform/SMF.512/hwmon/*/mb_poweron_reason
        fi
    fi
}

_track_reboot_reason
