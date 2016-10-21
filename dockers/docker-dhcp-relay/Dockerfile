FROM docker-base

## Make apt-get non-interactive
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get -y install \
        isc-dhcp-relay

COPY isc-dhcp-relay /etc/default/isc-dhcp-relay

ENTRYPOINT service isc-dhcp-relay start \
	&& /bin/bash

