#!/bin/bash

service rsyslog start
syncd -p profile.ini -N
