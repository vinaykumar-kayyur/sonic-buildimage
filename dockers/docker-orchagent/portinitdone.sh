#!/usr/bin/env bash

PORT_INIT_DONE=""

while [ "$PORT_INIT_DONE" == "PORT_TABLE:PortInitDone" ]
do
    PORT_INIT_DONE=`sonic-db-cli APPL_DB keys "PORT_TABLE:PortInitDone"`
    sleep 1
done
