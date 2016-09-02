#!/bin/bash

export XP_ROOT=usr/bin/cli/

service rsyslog start
syncd -p /usr/bin/profile.ini -N
