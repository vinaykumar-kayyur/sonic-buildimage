
FROM docker-config-engine-stretch

ARG docker_container_name
ENV PYTHONPATH=/usr/share/sonic/platform

RUN [ -f /etc/rsyslog.conf ] && sed -ri "s/%syslogtag%/$docker_container_name#%syslogtag%/;" /etc/rsyslog.conf

# Make apt-get non-interactive
ENV DEBIAN_FRONTEND=noninteractive

# Update apt's cache of available packages
RUN apt-get update && apt-get install -y ipmitool telnet busybox kmod

RUN pip install pytest pexpect

# Copy locally-built Debian package dependencies
COPY \
debs/libsaibcm_3.5.3.1m-25_amd64.deb debs/sonic-platform-pde_1.0_amd64.deb /debs/

# Install locally-built Debian packages and implicitly install their dependencies
RUN dpkg_apt() { [ -f $1 ] && { dpkg -i $1 || apt-get -y install -f; } || return 1; }; \
dpkg_apt /debs/libsaibcm_3.5.3.1m-25_amd64.deb; \
dpkg_apt /debs/sonic-platform-pde_1.0_amd64.deb

# Copy locally-built Debian package dependencies
COPY \
python-debs/python-sonic-utilities_1.2-1_all.deb /debs/

# Install locally-built Debian packages and implicitly install their dependencies
RUN dpkg_apt() { [ -f $1 ] && { dpkg -i $1 || apt-get -y install -f; } || return 1; }; dpkg_apt /debs/python-sonic-utilities_1.2-1_all.deb

# Copy locally-built Python wheel dependencies
COPY \
python-wheels/sonic_platform_common-1.0-py2-none-any.whl /python-wheels/

# Install locally-built Python wheel dependencies
RUN pip install \
/python-wheels/sonic_platform_common-1.0-py2-none-any.whl 



# Clean up
RUN apt-get clean -y; \
    apt-get autoclean -y; \
    apt-get autoremove -y
RUN rm -rf /debs ~/.cache

RUN mkdir -p /home/pde

COPY ["base_image_files/port_breakout.py", "/usr/local/bin/"]
COPY ["supervisord.conf", "/etc/supervisor/conf.d/"]
COPY ["docker_init.sh", "/usr/bin/"]
ENTRYPOINT ["/usr/bin/docker_init.sh"]
