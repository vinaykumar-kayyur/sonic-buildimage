#!/usr/bin/env bash

RESTAPI_ARGS=""
while true
do
    client_auth=`sonic-cfggen -d -v "RESTAPI['config']['client_auth']"`
    if [[ $client_auth == 'true' ]]; then
        certs=`sonic-cfggen -d -v "RESTAPI['certs']"`
        if [[ -n "$certs" ]]; then
                SERVER_CRT=`sonic-cfggen -d -v "RESTAPI['certs']['server_crt']"`
                SERVER_KEY=`sonic-cfggen -d -v "RESTAPI['certs']['server_key']"`
                CLIENT_CA_CRT=`sonic-cfggen -d -v "RESTAPI['certs']['client_ca_crt']"`
                CLIENT_CRT_CNAME=`sonic-cfggen -d -v "RESTAPI['certs']['client_crt_cname']"`
                if [[ -f $SERVER_CRT && -f $SERVER_KEY && -f $CLIENT_CA_CRT ]]; then
                    RESTAPI_ARGS+=" -enablehttps=true -enablehttp=false -servercert=$SERVER_CRT -serverkey=$SERVER_KEY -clientcert=$CLIENT_CA_CRT -clientcertcommonname=$CLIENT_CRT_CNAME"
                    break
                fi
        fi
    fi
    logger "Waiting for certificates..."
    sleep 60
done

LOG_LEVEL=`sonic-cfggen -d -v "RESTAPI['config']['log_level']"`
if [ ! -z $LOG_LEVEL ]; then
    RESTAPI_ARGS+=" -loglevel=$LOG_LEVEL"
else
    RESTAPI_ARGS+=" -loglevel=trace"
fi 

logger "RESTAPI_ARGS: $RESTAPI_ARGS"
exec /usr/sbin/go-server-server ${RESTAPI_ARGS}
