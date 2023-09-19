#!/usr/bin/env bash

EXIT_TELEMETRY_VARS_FILE_NOT_FOUND=1
EXIT_TELEMETRY_SERVER_CERT_FILE_NOT_FOUND=2
EXIT_TELEMETRY_SERVER_KEY_FILE_NOT_FOUND=3
EXIT_TELEMETRY_CA_CERT_FILE_NOT_FOUND=4
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

if [ -n "$CERTS" ]; then
    SERVER_CRT=$(echo $CERTS | jq -r '.server_crt')
    SERVER_KEY=$(echo $CERTS | jq -r '.server_key')
    if [ -z $SERVER_CRT ] || [ $SERVER_CRT == "null" ] || [ -z $SERVER_KEY ] || [ $SERVER_KEY == "null" ]; then
        TELEMETRY_ARGS+=" --insecure"
    else
        TELEMETRY_ARGS+=" --server_crt $SERVER_CRT --server_key $SERVER_KEY "
    fi

    CA_CRT=$(echo $CERTS | jq -r '.ca_crt')
    if [ ! -z $CA_CRT ] && [ $CA_CRT != "null" ]; then
        TELEMETRY_ARGS+=" --ca_crt $CA_CRT"
    fi

elif [ -n "$X509" ]; then
    SERVER_CRT=$(echo $X509 | jq -r '.server_crt')
    SERVER_KEY=$(echo $X509 | jq -r '.server_key')
    if [ -z $SERVER_CRT ] || [ $SERVER_CRT == "null" ] || [ -z $SERVER_KEY ] || [ $SERVER_KEY == "null" ]; then
        TELEMETRY_ARGS+=" --insecure"
    else
        TELEMETRY_ARGS+=" --server_crt $SERVER_CRT --server_key $SERVER_KEY "
    fi

    CA_CRT=$(echo $X509 | jq -r '.ca_crt')
    if [ ! -z $CA_CRT ] && [ $CA_CRT != "null" ]; then
        TELEMETRY_ARGS+=" --ca_crt $CA_CRT"
    fi

else
    TELEMETRY_ARGS+=" --insecure"
fi

# Check whether server certificate file exists or not
if [[ $TELEMETRY_ARGS == *"server_crt"* ]] && [ ! -f "$SERVER_CRT" ]; then
    echo "Telemetry server certificate file not found"
    exit $EXIT_TELEMETRY_SERVER_CERT_FILE_NOT_FOUND
fi

# Check whether server key file exists or not
if [[ $TELEMETRY_ARGS == *"server_key"* ]] && [ ! -f "$SERVER_KEY" ]; then
    echo "Telemetry server key file not found"
    exit $EXIT_TELEMETRY_SERVER_KEY_FILE_NOT_FOUND
fi

# Check whether CA certificate file exists or not
if [[ $TELEMETRY_ARGS == *"ca_crt"* ]] && [ ! -f "$CA_CRT" ]; then
    echo "Telemetry CA certificate file not found"
    exit $EXIT_TELEMETRY_CA_CERT_FILE_NOT_FOUND
fi

# If no configuration entry exists for TELEMETRY, create one default port
PORT=$(echo $GNMI | jq -r '.port')
if [ -z $PORT ] || [ $PORT == "null" ]; then
    TELEMETRY_ARGS+=" --port 8080"
else
    TELEMETRY_ARGS+=" --port $PORT"
fi

CLIENT_AUTH=$(echo $GNMI | jq -r '.client_auth')
if [ -z $CLIENT_AUTH ] || [ $CLIENT_AUTH == "null" ] || [ $CLIENT_AUTH == "false" ]; then
    TELEMETRY_ARGS+=" --allow_no_client_auth"
else
    TELEMETRY_ARGS+=" --client_auth $CLIENT_AUTH"
fi

LOG_LEVEL=$(echo $GNMI | jq -r '.log_level')
if [ ! -z $LOG_LEVEL ] && [ $LOG_LEVEL != "null" ] && [[ $LOG_LEVEL =~ ^[0-9]+$ ]]; then
    TELEMETRY_ARGS+=" -v=$LOG_LEVEL"
else
    TELEMETRY_ARGS+=" -v=2"
fi

exec /usr/sbin/telemetry ${TELEMETRY_ARGS}
