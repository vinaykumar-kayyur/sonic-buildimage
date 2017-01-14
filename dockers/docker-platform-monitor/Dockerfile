FROM docker-base

## Pre-install the fundamental packages
## Clean up
RUN apt-get update &&                                                               \
    apt-get -y install                                                              \
        smartmontools                                                               \
        sensord                                                                     \
        debs/python-sonic-config-engine_1.0-1_all.deb                                      \ 
        python-lxml python-jinja2 python-netaddr python-ipaddr python-yaml          \
        &&                                                                          \
    apt-get clean -y && apt-get autoclean -y && apt-get autoremove -y

COPY ["config.sh", "/usr/bin/"]

ENTRYPOINT /usr/bin/config.sh       \
    && service rsyslog start        \
    && service lm-sensors start     \
    && service smartmontools start  \
    && service sensord start        \
    && /bin/bash
