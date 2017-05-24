#!/usr/bin/env bash

export XP_ROOT=/usr/bin/

while true; do
    # Check if redis-server starts
    RESULT=$(redis-cli ping)

    if [ "$RESULT" == "PONG" ]; then
        break
    fi

    sleep 1
done


redis-cli FLUSHALL

exec syncd -p /etc/ssw/AS7512/profile.ini -N

