#!/bin/bash

# from redis official repo https://github.com/redis/redis/
# Generate some test certificates which are used by the regression test suite:
#
#   certs/tls/ca.{crt,key}          Self signed CA certificate.
#   certs/tls/redis.{crt,key}       A certificate with no key usage/policy restrictions.

generate_cert() {
    local name=$1
    local cn="$2"
    local opts="$3"

    local keyfile=certs/tls/${name}.key
    local certfile=certs/tls/${name}.crt

    [ -f $keyfile ] || openssl genrsa -out $keyfile 2048
    openssl req \
        -new -sha256 \
        -subj "/O=Redis Test/CN=$cn" \
        -key $keyfile | \
        openssl x509 \
            -req -sha256 \
            -CA certs/tls/ca.crt \
            -CAkey certs/tls/ca.key \
            -CAserial certs/tls/ca.txt \
            -CAcreateserial \
            -days 365 \
            $opts \
            -out $certfile
}

mkdir -p certs/tls
[ -f certs/tls/ca.key ] || openssl genrsa -out certs/tls/ca.key 4096
openssl req \
    -x509 -new -nodes -sha256 \
    -key certs/tls/ca.key \
    -days 3650 \
    -subj '/O=Redis Test/CN=Certificate Authority' \
    -out certs/tls/ca.crt

cat > certs/tls/openssl.cnf <<_END_
[ server_cert ]
keyUsage = digitalSignature, keyEncipherment
nsCertType = server

[ client_cert ]
keyUsage = digitalSignature, keyEncipherment
nsCertType = client
_END_

generate_cert redis "Generic-cert"
