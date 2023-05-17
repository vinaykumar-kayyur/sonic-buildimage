#!/bin/bash

# This script is for kubernetes master image usage
# Will mount kubernetes master disk and execute kubernetes entrance script

set -x

# mount disk from host
mount_point="/from_host"
disk="/dev/sdb1"
mkdir -p $mount_point
mount $disk $mount_point
# check whether it is the first time to boot
first_boot_flag_file="/from_host/first_boot_flag"
if [ -f $first_boot_flag_file ]; then
    exit 0
fi
touch $first_boot_flag_file
# execute entrance script
init_file_name="entrance.sh"
init_file=${mount_point}/${init_file_name}
chmod +x $init_file
source $init_file
