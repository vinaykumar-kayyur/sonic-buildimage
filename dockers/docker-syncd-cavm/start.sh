#!/bin/bash

service rsyslog start
syncd -p /usr/bin/profile.ini -N
