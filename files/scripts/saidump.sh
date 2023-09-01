#!/bin/bash

save_saidump_by_rdb() {
  #1. Save the Redis data.
  sudo sonic-db-cli -n asic$1 SAVE > /dev/null
  #2. Move dump files to /var/run/redisX/
  docker exec database$1 sh -c "mv /var/lib/redis/dump.rdb /var/run/redis$1/"
  #3. Run rdb command to convert the dump files into JSON files
  sudo python /usr/local/bin/rdb --command json  /var/run/redis$1/dump.rdb | sudo tee /var/run/redis$1/dump.json > /dev/null
  #4. Run saidump -r to update the JSON files' format as same as the saidump before. Then we can get the saidump result in standard output.
  docker exec syncd$1 sh -c "saidump -r /var/run/redis$1/dump.json"
  #5. clear
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