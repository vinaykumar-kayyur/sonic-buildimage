#!/usr/bin/env bash

name=$1
port=$2
mkdir -p /etc/$name
mkdir -p /var/lib/$name
cp /etc/redis/redis.conf /etc/$name/$name.conf
r1="s/port 6379/port $port/;"
r2="s%^unixsocket .*%unixsocket /var/run/redis/$name.sock%;"
r3="s%dir .*%dir /var/lib/$name%;"
r4="s%pidfile .*%pidfile /var/run/redis/$name.pid%;"
sed -ri "$r1$r2$r3$r4" /etc/$name/$name.conf
cp /etc/init.d/redis-server /etc/init.d/$name
