#!/usr/bin/env bash

name=$1
{ [[ -s /var/lib/$name/dump.rdb ]] || rm -f /var/lib/$name/dump.rdb; }
/usr/bin/redis-server /etc/$name/$name.conf&
