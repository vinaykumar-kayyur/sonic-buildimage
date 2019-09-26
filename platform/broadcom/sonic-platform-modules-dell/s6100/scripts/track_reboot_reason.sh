#!/bin/bash

syslog_found=false
syslog_1_found=false
reboot_dir_found=false
reboot_file_found=false

if [[ -f /var/log/syslog ]]; then
    syslog_found=true
fi

if [[ -f /var/log/syslog.1 ]]; then
    syslog_1_found=true
fi

if [[ -d /host/reboot-cause/platform ]]; then
    reboot_dir_found=true
    if [[ -f /host/reboot-cause/platform/reboot_reason ]]; then
        reboot_file_found=true
    fi
fi

track_thermal() {
    prev_thermal=$(cat /host/reboot-cause/platform/reboot_reason | grep thermal | cut -d ' ' -f2-4)
    curr_poweron_reason=$(cd /sys/devices/platform/SMF.512/hwmon/*; cat smf_poweron_reason)
    if [[ $curr_poweron_reason = "11" ]]; then
       return 0
    fi
    if [[ $prev_thermal = $curr_poweron_reason ]]; then
       return 0
    else
       sed -i "2s/.*/thermal $curr_poweron_reason/" /host/reboot-cause/platform/reboot_reason
       return 1
    fi

    return 0
}

track_watchdog()
{
     if [[ $syslog_found = true ]]; then
             wd_log="$(tac /var/log/syslog | grep -a "watchdog did not stop" | grep -a "CRIT kernel")"
             if [[ $wd_log = "" ]] && [[ $syslog_1_found = true ]]; then
                     wd_log="$(tac /var/log/syslog.1 | grep -a "watchdog did not stop" | grep -a "CRIT kernel")"
             fi
     fi

     if [[ $wd_log = "" ]]; then
         return 0
     fi

     if [[ $reboot_dir_found = true ]]; then
         echo "$wd_log" > /host/reboot-cause/platform/tmp
         wd_log=$(head -n 1 /host/reboot-cause/platform/tmp)
         wd_timestamp=$(echo $wd_log | cut -d ' ' -f1-3)
         wd_date=$(echo $wd_timestamp | cut -d '.' -f1)

         if [[ $reboot_file_found = true ]]; then
             prev_wd=$(cat /host/reboot-cause/platform/reboot_reason | grep watchdog | cut -d ' ' -f2-4)

             if [[ $prev_wd = $wd_date ]]; then
                 rm -rf /host/reboot-cause/platform/tmp
                return 0
             else
                sed -i "1s/.*/watchdog $wd_date/" /host/reboot-cause/platform/reboot_reason
                rm -rf /host/reboot-cause/platform/tmp
                return 1
             fi
         fi
     fi
}

track_reboot_reason() {
    if [[ $reboot_file_found = false ]]; then
        echo "watchdog None" > /host/reboot-cause/platform/reboot_reason
        echo "thermal None" >> /host/reboot-cause/platform/reboot_reason
    fi

    if [[ -d /sys/devices/platform/SMF.512/hwmon/ ]]; then
        track_thermal
        is_thermal_reboot=$(echo $?)

        track_watchdog
        is_wd_reboot=$(echo $?)

        rv=$(cd /sys/devices/platform/SMF.512/hwmon/*; cat mb_poweron_reason)
        reason=$(echo $rv | cut -d 'x' -f2)
        if [[ $reason = "ff" ]]; then
            sed -i "2s/.*/thermal None/" /host/reboot-cause/platform/reboot_reason
            cd /sys/devices/platform/SMF.512/hwmon/*
            if [[ -e /tmp/notify_firstboot_to_platform ]]; then
                echo 0x01 > mb_poweron_reason
            else
                echo 0xbb > mb_poweron_reason
            fi
        elif [[ $is_thermal_reboot = 1 ]]; then
            cd /sys/devices/platform/SMF.512/hwmon/*
            echo 0xee > mb_poweron_reason
        elif [[ $is_wd_reboot = 1 ]]; then
            cd /sys/devices/platform/SMF.512/hwmon/*
            echo 0xdd > mb_poweron_reason
        elif [[ $reason = "cc" ]]; then
            cd /sys/devices/platform/SMF.512/hwmon/*
            echo 0xaa > mb_poweron_reason
        else
            cd /sys/devices/platform/SMF.512/hwmon/*
            echo 0x99 > mb_poweron_reason
        fi
    fi
}
track_reboot_reason
