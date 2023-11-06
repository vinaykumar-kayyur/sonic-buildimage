#!/bin/bash -xe

## This script is to automate the preparation for a debian file system,
## which will be used for an ONIE installer image.
## This is the 1st part. 2nd part in build_debian.sh
## WARNING: this part can be cached (DPKG cache)

## Include common functions
. functions.sh

FILESYSTEM_ROOT=./fsroot-rfs
PLATFORM_DIR=platform

DOCKER_VERSION=5:24.0.2-1~debian.11~$IMAGE_DISTRO
CONTAINERD_IO_VERSION=1.6.21-1

## Ensure proc is mounted
sudo mount proc /proc -t proc || true

## Prepare the file system directory
sudo rm -rf $FILESYSTEM_ROOT || die "[ERROR] Failed to clean chroot directory"

mkdir -p $FILESYSTEM_ROOT
mkdir -p $FILESYSTEM_ROOT/$PLATFORM_DIR
touch $FILESYSTEM_ROOT/$PLATFORM_DIR/firsttime

bootloader_packages=""
if [ "$IMAGE_TYPE" = "aboot" ]; then
    TARGET_BOOTLOADER="aboot"
fi
if [ "$TARGET_BOOTLOADER" != "aboot" ]; then
    mkdir -p $FILESYSTEM_ROOT/$PLATFORM_DIR/grub
    bootloader_packages="grub2-common"
fi

## Build the host debian base system
echo '[INFO] Build host debian base system...'
TARGET_PATH=$TARGET_PATH scripts/build_debian_base_system.sh $CONFIGURED_ARCH $IMAGE_DISTRO $FILESYSTEM_ROOT

## Prepare buildinfo
echo "[INFO] Prepare buildinfo"
sudo DBGOPT="${DBGOPT}" \
    scripts/prepare_debian_image_buildinfo.sh $CONFIGURED_ARCH $IMAGE_DISTRO $FILESYSTEM_ROOT

## https://unix.stackexchange.com/questions/593529/can-not-configure-systemd-inside-a-chrooted-environment
sudo chown root:root $FILESYSTEM_ROOT

## Config hostname and hosts, otherwise 'sudo ...' will complain 'sudo: unable to resolve host ...'
run_in_chroot $FILESYSTEM_ROOT /bin/bash -c "echo '$SONIC_DEFAULT_HOSTNAME' > /etc/hostname"
run_in_chroot $FILESYSTEM_ROOT /bin/bash -c "echo '127.0.0.1 $SONIC_DEFAULT_HOSTNAME' >> /etc/hosts"
run_in_chroot $FILESYSTEM_ROOT /bin/bash -c "echo '127.0.0.1 localhost' >> /etc/hosts"

## Config basic fstab
run_in_chroot $FILESYSTEM_ROOT /bin/bash -c 'echo "proc /proc proc defaults 0 0" >> /etc/fstab'
run_in_chroot $FILESYSTEM_ROOT /bin/bash -c 'echo "sysfs /sys sysfs defaults 0 0" >> /etc/fstab'

## Mount /proc.
trap_push "sudo chroot $FILESYSTEM_ROOT umount /proc || true"
run_in_chroot $FILESYSTEM_ROOT mount proc /proc -t proc

## Pointing apt to public apt mirrors and getting latest packages, needed for latest security updates
scripts/build_mirror_config.sh files/apt $CONFIGURED_ARCH $IMAGE_DISTRO
sudo cp files/apt/sources.list.$CONFIGURED_ARCH $FILESYSTEM_ROOT/etc/apt/sources.list
sudo cp files/apt/apt-retries-count $FILESYSTEM_ROOT/etc/apt/apt.conf.d/
sudo cp files/apt/apt.conf.d/{81norecommends,apt-{clean,gzip-indexes,no-languages},no-check-valid-until} $FILESYSTEM_ROOT/etc/apt/apt.conf.d/

## Setup apt proxy
[ -n "$http_proxy" ] && sudo /bin/bash -c "echo 'Acquire::http::Proxy \"$http_proxy\";' > $FILESYSTEM_ROOT/etc/apt/apt.conf.d/01proxy"

## Upgrade installed deb packages
run_in_chroot $FILESYSTEM_ROOT apt-get update
run_in_chroot $FILESYSTEM_ROOT apt-get -y upgrade

## Install eatmydata to speedup deb package installation
echo '[INFO] Install and setup eatmydata'
run_in_chroot $FILESYSTEM_ROOT apt-get -y install eatmydata
run_in_chroot $FILESYSTEM_ROOT ln -s /usr/bin/eatmydata /usr/local/bin/dpkg
echo 'Dir::Bin::dpkg "/usr/local/bin/dpkg";' | sudo tee $FILESYSTEM_ROOT/etc/apt/apt.conf.d/00image-install-eatmydata > /dev/null
## Note: dpkg hook conflict with eatmydata
run_in_chroot $FILESYSTEM_ROOT rm /usr/local/sbin/dpkg -f

echo '[INFO] Install packages for building image'
run_in_chroot $FILESYSTEM_ROOT apt-get -y install makedev psmisc

if [[ $CROSS_BUILD_ENVIRON == y ]]; then
    run_in_chroot $FILESYSTEM_ROOT dpkg --add-architecture $CONFIGURED_ARCH
fi

## Create device files
echo '[INFO] MAKEDEV'
if [[ $CONFIGURED_ARCH == armhf || $CONFIGURED_ARCH == arm64 ]]; then
    run_in_chroot $FILESYSTEM_ROOT /bin/bash -c 'cd /dev && MAKEDEV generic-arm'
else
    run_in_chroot $FILESYSTEM_ROOT /bin/bash -c 'cd /dev && MAKEDEV generic'
fi

## Install initramfs-tools and linux kernel
## Note: initramfs-tools recommends depending on busybox, and we really want busybox for
## 1. commands such as touch
## 2. mount supports squashfs
## However, 'dpkg -i' plus 'apt-get install -f' will ignore the recommended dependency. So
## we install busybox explicitly
run_in_chroot $FILESYSTEM_ROOT apt-get -y install busybox linux-base pigz
echo '[INFO] Install SONiC linux kernel image'
## Note: duplicate apt-get command to ensure every line return zero
sudo dpkg --root=$FILESYSTEM_ROOT -i $debs_path/initramfs-tools-core_*.deb || \
    run_in_chroot $FILESYSTEM_ROOT apt-get -y install -f
sudo dpkg --root=$FILESYSTEM_ROOT -i $debs_path/initramfs-tools_*.deb || \
    run_in_chroot $FILESYSTEM_ROOT apt-get -y install -f
sudo dpkg --root=$FILESYSTEM_ROOT -i $debs_path/linux-image-$SONIC_LINUX_KERNEL_VERSION-*_$CONFIGURED_ARCH.deb || \
    run_in_chroot $FILESYSTEM_ROOT apt-get -y install -f

## Install docker
echo '[INFO] Install docker'
## Install apparmor utils since they're missing and apparmor is enabled in the kernel
## Otherwise Docker will fail to start
run_in_chroot $FILESYSTEM_ROOT apt-get -y install \
    apt-transport-https \
    ca-certificates \
    curl

if [[ $CONFIGURED_ARCH == armhf ]]; then
    # update ssl ca certificates for secure pem
    run_in_chroot $FILESYSTEM_ROOT c_rehash
fi
run_in_chroot $FILESYSTEM_ROOT curl -o /tmp/docker.asc -fsSL https://download.docker.com/linux/debian/gpg
run_in_chroot $FILESYSTEM_ROOT mv /tmp/docker.asc /etc/apt/trusted.gpg.d/
sudo tee $FILESYSTEM_ROOT/etc/apt/sources.list.d/docker.list >/dev/null <<EOF
deb [arch=$CONFIGURED_ARCH] https://download.docker.com/linux/debian $IMAGE_DISTRO stable
EOF
run_in_chroot $FILESYSTEM_ROOT apt-get update
run_in_chroot $FILESYSTEM_ROOT apt-get -y install \
    docker-ce=${DOCKER_VERSION} \
    docker-ce-cli=${DOCKER_VERSION} \
    containerd.io=${CONTAINERD_IO_VERSION}

## Pre-install the fundamental packages
##
## apparmor is enabled in the kernel, otherwise Docker will fail to start
## ca-certificates is needed for easy_install
## python3-cryptography for azure-storage
## efitools to support secure upgrade
## fdisk and gpg are needed by fwutil
## gdisk is needed for sgdisk in install.sh
## libffi-dev to match utilities' dependency
## libpam-cracklib for supporting password hardening
## parted is needed for partprobe in install.sh
run_in_chroot $FILESYSTEM_ROOT apt-get -y install \
    $bootloader_packages    \
    acl                     \
    apparmor                \
    arping                  \
    auditd                  \
    bash-completion         \
    bridge-utils            \
    bsdmainutils            \
    ca-certificates         \
    cgroup-tools            \
    conntrack               \
    cron                    \
    curl                    \
    dbus                    \
    device-tree-compiler    \
    ebtables                \
    efibootmgr              \
    efitools                \
    fdisk                   \
    file                    \
    gdisk                   \
    gpg                     \
    haveged                 \
    hping3                  \
    i2c-tools               \
    ifmetric                \
    ipmitool                \
    iproute2                \
    iptables-persistent     \
    iputils-ping            \
    isc-dhcp-client         \
    jq                      \
    kexec-tools             \
    less                    \
    libffi-dev              \
    libgrpc++1              \
    libgrpc10               \
    libpam-cracklib         \
    libprotobuf23           \
    libubootenv-tool        \
    linux-perf              \
    locales                 \
    logrotate               \
    lsof                    \
    makedumpfile            \
    mokutil                 \
    mtd-utils               \
    mtr-tiny                \
    ndisc6                  \
    net-tools               \
    ntp                     \
    ntpstat                 \
    openssh-server          \
    openssl                 \
    pciutils                \
    picocom                 \
    python3                 \
    python3-apt             \
    python3-cryptography    \
    python3-distutils       \
    python3-pip             \
    python-is-python3       \
    resolvconf              \
    screen                  \
    squashfs-tools          \
    sudo                    \
    sysfsutils              \
    sysstat                 \
    systemd                 \
    systemd-sysv            \
    tcpdump                 \
    tcptraceroute           \
    traceroute              \
    u-boot-tools            \
    unzip                   \
    usbutils                \
    vim

# default rsyslog version is 8.2110.0 which has a bug on log rate limit,
# use backport version
run_in_chroot $FILESYSTEM_ROOT apt-get -t bullseye-backports -y install rsyslog

# Installed smartmontools version should match installed smartmontools in docker-platform-monitor Dockerfile
run_in_chroot $FILESYSTEM_ROOT apt-get -y install smartmontools=7.2-1

if [[ $CONFIGURED_ARCH == amd64 ]]; then
    ## Pre-install packages for amd64 (x86)
    run_in_chroot $FILESYSTEM_ROOT apt-get -y install \
        firmware-linux-nonfree \
        rasdaemon \
        dmidecode \
        hdparm
fi

if [[ $CONFIGURED_ARCH == armhf || $CONFIGURED_ARCH == arm64 ]]; then
    ## Install dependency pkgs for SONiC config engine Python 2 package
    run_in_chroot $FILESYSTEM_ROOT apt-get -y install libxslt-dev libz-dev
fi

## Install dev packages, needed for building/installing some Python packages, remove them later
run_in_chroot $FILESYSTEM_ROOT apt-get -y install \
    build-essential \
    gcc \
    libcairo2-dev \
    libdbus-1-dev \
    libgirepository1.0-dev \
    libssl-dev \
    libsystemd-dev \
    pkg-config \
    python3-dev \
    swig

## Mark runtime dependencies as manually installed to avoid them being auto-removed while uninstalling build dependencies
run_in_chroot $FILESYSTEM_ROOT apt-mark manual \
    gir1.2-glib-2.0 \
    libdbus-1-3 \
    libgirepository-1.0-1 \
    libsystemd0 \
    python3-dbus

#Adds a locale to a debian system in non-interactive mode
sudo sed -i '/^#.* en_US.* /s/^#//' $FILESYSTEM_ROOT/etc/locale.gen && \
    run_in_chroot $FILESYSTEM_ROOT locale-gen "en_US.UTF-8"
sudo LANG=en_US.UTF-8 DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT update-locale "LANG=en_US.UTF-8"
run_in_chroot $FILESYSTEM_ROOT bash -c "find /usr/share/i18n/locales/ ! -name 'en_US' -type f -exec rm -f {} +"

if [[ $TARGET_BOOTLOADER == grub ]]; then
    if [[ $CONFIGURED_ARCH == amd64 ]]; then
        GRUB_PKG=grub-pc-bin
    elif [[ $CONFIGURED_ARCH == arm64 ]]; then
        GRUB_PKG=grub-efi-arm64-bin
    fi

    run_in_chroot $FILESYSTEM_ROOT apt-get install -d -o dir::cache=/var/cache/apt $GRUB_PKG
    sudo cp $FILESYSTEM_ROOT/var/cache/apt/archives/grub*.deb $FILESYSTEM_ROOT/$PLATFORM_DIR/grub
fi

## Upgrade pip via PyPI and uninstall the Debian version
## Note: keep pip installed for maintainance purpose
run_in_chroot $FILESYSTEM_ROOT pip3 install --upgrade pip
run_in_chroot $FILESYSTEM_ROOT apt-get purge -y python3-pip

## For building Python packages
run_in_chroot $FILESYSTEM_ROOT pip3 install 'setuptools==49.6.00'
run_in_chroot $FILESYSTEM_ROOT pip3 install 'wheel==0.35.1'

## docker Python API package is needed by Ansible docker module as well as some SONiC applications
run_in_chroot $FILESYSTEM_ROOT pip3 install 'docker==6.1.1'

## Install scapy
run_in_chroot $FILESYSTEM_ROOT pip3 install 'scapy==2.4.4'

## The option --no-build-isolation can be removed when upgrading PyYAML to 6.0.1
run_in_chroot $FILESYSTEM_ROOT pip3 install 'PyYAML==5.4.1' --no-build-isolation

## Install j2cli for handling jinja template
run_in_chroot $FILESYSTEM_ROOT pip3 install "j2cli==0.3.10"

## Install Python client for Redis
run_in_chroot $FILESYSTEM_ROOT pip3 install "redis==3.5.3"

## Install Python module for psutil
run_in_chroot $FILESYSTEM_ROOT pip3 install psutil

## Install Python module for ipaddr
run_in_chroot $FILESYSTEM_ROOT pip3 install ipaddr

## Install Python module for grpcio and grpcio-tools
if [[ $CONFIGURED_ARCH == amd64 ]]; then
    run_in_chroot $FILESYSTEM_ROOT pip3 install "grpcio==1.39.0"
    run_in_chroot $FILESYSTEM_ROOT pip3 install "grpcio-tools==1.39.0"
fi

## Install systemd-python for SONiC host services
sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT pip3 install systemd-python

sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT pip3 install azure-storage==0.36.0
sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT pip3 install watchdog==0.10.3

## Remove apt proxy
sudo rm -f $FILESYSTEM_ROOT/etc/apt/apt.conf.d/01proxy

## Remove resolv.conf
sudo rm -f $FILESYSTEM_ROOT/etc/resolv.conf

echo '[INFO] Umount all'
## Display all process details access /proc
run_in_chroot $FILESYSTEM_ROOT fuser -vm /proc
## Kill the processes
run_in_chroot $FILESYSTEM_ROOT fuser -km /proc || true
## Wait fuser fully kill the processes
sudo timeout 15s bash -c 'until chroot $0 umount /proc; do sleep 1; done' $FILESYSTEM_ROOT

sudo rm -f $TARGET_PATH/$RFS_SQUASHFS_NAME
sudo mksquashfs $FILESYSTEM_ROOT $TARGET_PATH/$RFS_SQUASHFS_NAME -Xcompression-level 1
sudo rm -rf $FILESYSTEM_ROOT
