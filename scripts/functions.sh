run_with_retry(){
    [ $SONIC_BUILD_RETRY_COUNT -lt 0 ] && SONIC_BUILD_RETRY_COUNT=0
    [[ "$*" == "" ]] && { echo "run_with_retry: input command can't be empty." 1>&2;exit 1; }
    for ((i=0; i<=$SONIC_BUILD_RETRY_COUNT; i++))
    do
        [[ $i != 0 ]] && { echo "================================================================================================" 1>&2; echo "Waiting $SONIC_BUILD_RETRY_INTERVAL to run again, $i/$SONIC_BUILD_RETRY_COUNT" 1>&2; echo "================================================================================================" 1>&2; sleep $SONIC_BUILD_RETRY_INTERVAL; }
        "$@" && break
    done
}

