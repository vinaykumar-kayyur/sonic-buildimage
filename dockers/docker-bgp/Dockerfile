FROM docker-base

## Make apt-get non-interactive
ENV DEBIAN_FRONTEND=noninteractive

COPY deps/quagga_*.deb /deps/
RUN dpkg_apt() { [ -f $1 ] && { dpkg -i $1 || apt-get -y install -f; } || return 1; } &&        \
    dpkg_apt /deps/quagga_*.deb &&                                                              \
    apt-get update &&                                                                           \
    apt-get -y install -f python-jinja2 python-netaddr python-ipaddr python-lxml &&             \
    apt-get clean -y && apt-get autoclean -y && apt-get autoremove -y &&                        \
    rm -rf /deps

COPY daemons /etc/quagga/
COPY ["*.j2", "config.sh", "template_list", "*.py", "/etc/swss/"]

ENTRYPOINT service rsyslog start    \
    && /etc/swss/config.sh          \
    && service quagga start         \
    && /bin/bash
