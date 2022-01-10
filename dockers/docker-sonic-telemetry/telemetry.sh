#!/usr/bin/env bash

EXIT_TELEMETRY_VARS_FILE_NOT_FOUND=1
TELEMETRY_VARS_FILE=/usr/share/sonic/templates/telemetry_vars.j2

if [ ! -f "$TELEMETRY_VARS_FILE" ]; then
    echo "Telemetry vars template file not found"
    exit $EXIT_TELEMETRY_VARS_FILE_NOT_FOUND
fi

# Try to read telemetry and certs config from ConfigDB.
# Use default value if no valid config exists
TELEMETRY_VARS=$(sonic-cfggen -d -t $TELEMETRY_VARS_FILE)
TELEMETRY_VARS=${TELEMETRY_VARS//[\']/\"}
X509=$(echo $TELEMETRY_VARS | jq -r '.x509')
GNMI=$(echo $TELEMETRY_VARS | jq -r '.gnmi')
CERTS=$(echo $TELEMETRY_VARS | jq -r '.certs')

TELEMETRY_ARGS=" -logtostderr"
export CVL_SCHEMA_PATH=/usr/sbin/schema

while true
do
    if [ -n "$CERTS" ]; then
        SERVER_CRT=$(echo $CERTS | jq -r '.server_crt')
        SERVER_KEY=$(echo $CERTS | jq -r '.server_key')
        CA_CRT=$(echo $CERTS | jq -r '.ca_crt')

        logger "Trying to retrieve server certificate, key and Root CA certificate ..."
        logger "The file path of server certificate in CONFIG_DB is: $SERVER_CRT"
        logger "The file path of server provate key in CONFIG_DB is: $SERVER_KEY"
        logger "The file path of Root CA certificate in CONFIG_DB is: $CA_CRT"

        if [[ -f $SERVER_CRT && -f $SERVER_KEY && -f $CA_CRT ]]; then
            logger "Succeeded in retrieving server certificate, key and Root CA certificate."
            TELEMETRY_ARGS+=" --server_crt $SERVER_CRT --server_key $SERVER_KEY --ca_crt $CA_CRT"
            break
        else
            logger "Failed to retrieve server certificate, key or Root CA certificate!"
        fi
    elif [ -n "$X509" ]; then
        SERVER_CRT=$(echo $X509 | jq -r '.server_crt')
        SERVER_KEY=$(echo $X509 | jq -r '.server_key')
        if [ -z $SERVER_CRT  ] || [ -z $SERVER_KEY  ]; then
            TELEMETRY_ARGS+=" --insecure"
        else
            TELEMETRY_ARGS+=" --server_crt $SERVER_CRT --server_key $SERVER_KEY "
        fi

        CA_CRT=$(echo $X509 | jq -r '.ca_crt')
        if [ ! -z $CA_CRT ]; then
            TELEMETRY_ARGS+=" --ca_crt $CA_CRT"
        fi
        break
    else
        TELEMETRY_ARGS+=" --noTLS"
        break
    fi

    logger "Sleeping 3600 seconds and checks the existence of secrets again ..."
    sleep 3600
done

# If no configuration entry exists for TELEMETRY, create one default port
if [ -z "$GNMI" ]; then
    PORT=8080
else
    PORT=$(echo $GNMI | jq -r '.port')
fi
TELEMETRY_ARGS+=" --port $PORT"

CLIENT_AUTH=$(echo $GNMI | jq -r '.client_auth')
if [ -z $CLIENT_AUTH ] || [ $CLIENT_AUTH == "false" ]; then
    TELEMETRY_ARGS+=" --allow_no_client_auth"
fi

LOG_LEVEL=$(echo $GNMI | jq -r '.log_level')
if [ ! -z $LOG_LEVEL ]; then
    TELEMETRY_ARGS+=" -v=$LOG_LEVEL"
else
    TELEMETRY_ARGS+=" -v=2"
fi

exec /usr/sbin/telemetry ${TELEMETRY_ARGS}
