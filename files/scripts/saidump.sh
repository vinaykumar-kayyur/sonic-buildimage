#!/bin/bash
set -e

function debug()
{
  /usr/bin/logger "$1"
}

save_saidump_by_rdb() {
  debug "saidump.sh: [1] sonic-db-cli -n asic$1 SAVE."
  sudo sonic-db-cli -n asic$1 SAVE > /dev/null
  debug "saidump.sh: [2] Move dump.rdb to /var/run/redis$1/ in container database$1."
  docker exec database$1 sh -c "mv /var/lib/redis/dump.rdb /var/run/redis$1/"
  debug "saidump.sh: [3] Run rdb command to convert the dump files into JSON files."
  sudo python /usr/local/bin/rdb --command json  /var/run/redis$1/dump.rdb | sudo tee /var/run/redis$1/dump.json > /dev/null
  debug "saidump.sh: [4] Run saidump -r to update the JSON files' format as same as the saidump before. Then we can get the saidump's result in standard output."
  docker exec syncd$1 sh -c "saidump -r /var/run/redis$1/dump.json"
  debug "saidump.sh: [5] Clear temporary files."
  sudo rm -f /var/run/redis$1/dump.rdb
  sudo rm -f /var/run/redis$1/dump.json
}

NUM_ASICS=`python -c 'from sonic_py_common.multi_asic import get_num_asics; print(get_num_asics())'`


if (( $# == 0 &&  $NUM_ASICS == 1 )); then
  save_saidump_by_rdb
#validate if the argument is an integer  
elif [[ "$1" =~ [0-9]+ ]] && (( $# == 1 && $1 >= 0  && $1 < $NUM_ASICS )) ; then
    save_saidump_by_rdb $1
else
  echo "The number of ASICS is $NUM_ASICS."
  echo "Usage:"
  echo "saidump.sh <ASIC Index> or NULL"
  echo "           <ASIC Index> should be 0 ~ NUM_ASICS."
  echo "           E.g. \"saidump.sh 1\" is OK when NUMASICS is 2."
  echo "           NULL"
  echo "           E.g. \"saidump.sh\" is OK when NUMASICS is 1."
fi