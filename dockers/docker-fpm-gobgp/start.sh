#!/bin/bash

service rsyslog start
service quagga start
service gobgp start
fpmsyncd &
