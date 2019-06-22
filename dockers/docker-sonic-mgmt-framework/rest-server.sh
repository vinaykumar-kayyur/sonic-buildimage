#!/usr/bin/env bash

REST_SERVER_ARGS=" -ui /rest_ui -port=80 -logtostderr"

#export LIBYANG_EXTENSIONS_PLUGINS_DIR 
export CVL_SCHEMA_PATH=/usr/sbin/schema
export LIBYANG_EXTENSIONS_PLUGINS_DIR=/usr/sbin/lib
export LIBYANG_USER_TYPES_PLUGINS_DIR=/usr/sbin/lib
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$PATH:/usr/sbin/lib

exec /usr/sbin/rest_server ${REST_SERVER_ARGS}
#while [ true ]; do sleep 1; done
