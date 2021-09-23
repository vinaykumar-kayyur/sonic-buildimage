#!/bin/bash -x

old_lags=`ip link show type team | awk -F ':' '{print $2}' | grep PortChannel`
new_lag=`redis-cli -n 4 keys "PORTCHANNEL|*"`
for lag in ${old_lags[*]}; do
    if [[ !($new_lag =~ $lag) ]]
    then
        `ip link del $lag`
    fi
done
