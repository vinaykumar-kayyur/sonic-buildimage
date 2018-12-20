#!/usr/bin/env bash

port=$1
until [[ $(/usr/bin/docker exec database redis-cli -p $port ping | grep -c PONG) -gt 0 ]]; do
    sleep 1;
done
