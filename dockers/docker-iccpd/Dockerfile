FROM docker-config-engine

## Make apt-get non-interactive
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update

RUN apt-get install -f -y libdbus-1-3 libdaemon0 libjansson4

## Install redis-tools dependencies
## TODO: implicitly install dependencies
RUN apt-get -y install libjemalloc1
RUN apt-get -y install libpython2.7
RUN apt-get -y install ebtables
RUN apt-get install -f kmod

COPY \
debs/libnl-3-200_3.2.27-2_amd64.deb debs/libnl-route-3-200_3.2.27-2_amd64.deb debs/libnl-genl-3-200_3.2.27-2_amd64.deb debs/libnl-nf-3-200_3.2.27-2_amd64.deb debs/libhiredis0.13_0.13.3-2_amd64.deb debs/libnl-cli-3-200_3.2.27-2_amd64.deb debs/libswsscommon_1.0.0_amd64.deb debs/libsairedis_1.0.0_amd64.deb debs/libsaimetadata_1.0.0_amd64.deb debs/libteam5_1.26-1_amd64.deb debs/python-swsscommon_1.0.0_amd64.deb debs/swss_1.0.0_amd64.deb debs/redis-tools_3.2.4-1~bpo8+1_amd64.deb debs/iccpd_0.0.5_amd64.deb debs/

RUN dpkg -i \
debs/libnl-3-200_3.2.27-2_amd64.deb debs/libnl-route-3-200_3.2.27-2_amd64.deb debs/libnl-genl-3-200_3.2.27-2_amd64.deb debs/libnl-nf-3-200_3.2.27-2_amd64.deb debs/libhiredis0.13_0.13.3-2_amd64.deb debs/libnl-cli-3-200_3.2.27-2_amd64.deb debs/libswsscommon_1.0.0_amd64.deb debs/libsairedis_1.0.0_amd64.deb debs/libsaimetadata_1.0.0_amd64.deb debs/libteam5_1.26-1_amd64.deb debs/python-swsscommon_1.0.0_amd64.deb debs/swss_1.0.0_amd64.deb debs/redis-tools_3.2.4-1~bpo8+1_amd64.deb debs/iccpd_0.0.5_amd64.deb 

COPY ["start.sh", "iccpd.sh", "/usr/bin/"]
COPY ["supervisord.conf", "/etc/supervisor/conf.d/"]
COPY ["iccpd.j2", "/usr/share/sonic/templates/"]

RUN apt-get clean -y; apt-get autoclean -y; apt-get autoremove -y
RUN rm -rf /debs

ENTRYPOINT ["/usr/bin/supervisord"]