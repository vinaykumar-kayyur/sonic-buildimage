#!/bin/bash
# This script is used to check the readiness of containers
# Check if the container is ready or not

#### exit code
# 0: ready
# 1: python script crach exit code
# 2: supervisor start service doesn't exit normally
#### other: return code of post_check_script, define in the script, should not include 1,2

# supervisorctl exit code
# 0: Running
# 3: Exited
# 4: ERROR (no such process)
pre_check_service_name="start"
supervisorctl status |awk '{print $1}' |grep -w $pre_check_service_name > /dev/null
start_check_result=$?
if [ $start_check_result = 0 ] && [ $(supervisorctl status $pre_check_service_name |awk '{print $2}') != 'EXITED' ]; then
    exit 2
fi

# feature owner can add their own readiness check script
post_check_script="/usr/bin/readiness_probe.py"
if [ -f $post_check_script ]; then
    python3 $post_check_script
    post_check_result=$?
    if [ $post_check_result != 0 ]; then
        exit $post_check_result
    fi
fi

exit 0
