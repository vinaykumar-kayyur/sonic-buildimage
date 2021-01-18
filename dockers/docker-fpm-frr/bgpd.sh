#!/usr/bin/env bash

addr="127.0.0.1"
port=2601

while getopts ":A:P:" opt; do
    case "${opt}" in
        A) addr=${OPTARG}
            ;;
        P) port=${OPTARG}
            ;;
    esac
done

timeout 5s bash -c -- "until </dev/tcp/${addr}/${port}; do sleep 0.1;done"

exec /usr/lib/frr/bgpd "$@"
