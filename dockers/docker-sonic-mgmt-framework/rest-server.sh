#!/usr/bin/env bash

REST_SERVER_ARGS=" -ui /rest_ui -port=80 -logtostderr"

exec /usr/sbin/rest_server ${REST_SERVER_ARGS}


