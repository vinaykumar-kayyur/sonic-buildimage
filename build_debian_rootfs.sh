#!/bin/bash
## This script is to automate the preparation for a debian file system, which will be used for
## an ONIE installer image.
## Build a common part of sonic rootfs image.
##
## USAGE:
##   USERNAME=username PASSWORD=password ./build_debian
## ENVIRONMENT:
##   BUILD_TARGET
##          The name of the installer that is currently being created
##   USERNAME
##          The name of the default admin user
##   PASSWORD
##          The password, expected by chpasswd command
##   NUMPROCS
##          Limit the number of processes to use with mksquashfs

## Default user
[ -n "$USERNAME" ] || {
    echo "Error: no or empty USERNAME"
    exit 1
}

## Password for the default user
[ -n "$PASSWORD" ] || {
    echo "Error: no or empty PASSWORD"
    exit 1
}

## Number of CPU processes to use for mksquashfs
[ -n "$NUMPROCS" ] || {
    NUMPROCS=$(nproc)
}

## Include common functions
. functions.sh

## Enable debug output for script
set -x -e

CONFIGURED_ARCH=$([ -f .arch ] && cat .arch || echo amd64)

## docker engine version (with platform)
DOCKER_VERSION=5:20.10.7~3-0~debian-$IMAGE_DISTRO
LINUX_KERNEL_VERSION=5.10.0-8-2

## Hostname for the linux image
HOSTNAME=sonic
DEFAULT_USERINFO="Default admin user,,,"
BUILD_TOOL_PATH=src/sonic-build-hooks/buildinfo
TRUSTED_GPG_DIR=$BUILD_TOOL_PATH/trusted.gpg.d

## Read ONIE image related config file
. ./onie-image.conf
[ -n "$ONIE_IMAGE_PART_SIZE" ] || {
    echo "Error: Invalid ONIE_IMAGE_PART_SIZE in onie image config file"
    exit 1
}
[ -n "$ONIE_INSTALLER_PAYLOAD" ] || {
    echo "Error: Invalid ONIE_INSTALLER_PAYLOAD in onie image config file"
    exit 1
}
[ -n "$FILESYSTEM_SQUASHFS" ] || {
    echo "Error: Invalid FILESYSTEM_SQUASHFS in onie image config file"
    exit 1
}


## Working directory to prepare the file system
FILESYSTEM_BASE=/sonic/build/${BASE_IMAGE_NAME}
FILESYSTEM_ROOT=${FILESYSTEM_BASE}
PLATFORM_DIR=platform
BUILD_PATH=target/fs/${TARGET_MACHINE}


BASE_IMAGE_NAME=${BASE_IMAGE_NAME} scripts/fsutil.sh imagefs create 
trap_push "sudo LANG=C BASE_IMAGE_NAME=${BASE_IMAGE_NAME} scripts/fsutil.sh rootfs umount || true"
BASE_IMAGE_NAME=${BASE_IMAGE_NAME} scripts/fsutil.sh rootfs mount  


mkdir -p ${BUILD_PATH}
sudo chmod -R 777 ${BUILD_PATH}
mkdir -p ${FILESYSTEM_ROOT}
mkdir -p $FILESYSTEM_ROOT/$PLATFORM_DIR
mkdir -p $FILESYSTEM_ROOT/$PLATFORM_DIR/x86_64-grub
touch $FILESYSTEM_ROOT/$PLATFORM_DIR/firsttime

## ensure proc is mounted
sudo mountpoint -q /proc || sudo mount -t proc proc /proc || true


## make / as a mountpoint in chroot env, needed by dockerd
pushd $FILESYSTEM_ROOT
sudo mount --bind . .
popd

## Build the host debian base system
echo '[INFO] Build host debian base system...'
TARGET_PATH=$TARGET_PATH scripts/build_debian_base_system.sh $CONFIGURED_ARCH $IMAGE_DISTRO $FILESYSTEM_ROOT

## ensure proc is mounted
## BUG: https://www.mail-archive.com/debian-boot@lists.debian.org/msg172722.html
sudo mountpoint -q /proc || sudo mount -t proc proc /proc || true

# Prepare buildinfo
sudo DBGOPT="${DBGOPT}" SONIC_VERSION_CACHE=${SONIC_VERSION_CACHE} \
	scripts/prepare_debian_image_buildinfo.sh $CONFIGURED_ARCH $IMAGE_DISTRO $FILESYSTEM_ROOT $http_proxy


sudo chown root:root $FILESYSTEM_ROOT

## Config hostname and hosts, otherwise 'sudo ...' will complain 'sudo: unable to resolve host ...'
sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo '$HOSTNAME' > /etc/hostname"
sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo '127.0.0.1       $HOSTNAME' >> /etc/hosts"
sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo '127.0.0.1       localhost' >> /etc/hosts"

## Config basic fstab
sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c 'echo "proc /proc proc defaults 0 0" >> /etc/fstab'
sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c 'echo "sysfs /sys sysfs defaults 0 0" >> /etc/fstab'

## Setup proxy
[ -n "$http_proxy" ] && sudo /bin/bash -c "echo 'Acquire::http::Proxy \"$http_proxy\";' > $FILESYSTEM_ROOT/etc/apt/apt.conf.d/01proxy"

## make / as a mountpoint in chroot env, needed by dockerd
#pushd $FILESYSTEM_ROOT
#sudo mount --bind . .
#trap_push 'sudo umount $FILESYSTEM_ROOT || true'
#popd

trap_push 'sudo LANG=C chroot $FILESYSTEM_ROOT umount /proc || true'
sudo LANG=C chroot $FILESYSTEM_ROOT mount proc /proc -t proc
## Note: mounting is necessary to makedev and install linux image
echo '[INFO] Mount all'
## Output all the mounted device for troubleshooting
sudo LANG=C chroot $FILESYSTEM_ROOT mount

## Install the trusted gpg public keys
[ -d $TRUSTED_GPG_DIR ] && [ ! -z "$(ls $TRUSTED_GPG_DIR)" ] && sudo cp $TRUSTED_GPG_DIR/* ${FILESYSTEM_ROOT}/etc/apt/trusted.gpg.d/

## Pointing apt to public apt mirrors and getting latest packages, needed for latest security updates
sudo cp files/apt/sources.list.$CONFIGURED_ARCH $FILESYSTEM_ROOT/etc/apt/sources.list
sudo cp files/apt/apt.conf.d/{81norecommends,apt-{clean,gzip-indexes,no-languages},no-check-valid-until} $FILESYSTEM_ROOT/etc/apt/apt.conf.d/

## Note: set lang to prevent locale warnings in your chroot
sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y update
sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y upgrade


# Pre-install the list of deian packages which are required at the later part of the installation.
# These packages are installed either directly or required as a dependency for the main package.
# Pre-installation of these packages will skip the installation of the same package at the later stage
# and will speed up the build process.
# These packages are not removed from the original place to avoid the merge issues during branch merge. 
DEB_PKG_LIST_FILE=files/build/versions/host-image/versions-deb-${IMAGE_DISTRO}-${CONFIGURED_ARCH}
if [[ ! -z ${SONIC_VERSION_CACHE} && ${SONIC_VERSION_CACHE} != "none" && -e ${DEB_PKG_LIST_FILE} ]]; then
	sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y install \
		$(cat ${DEB_PKG_LIST_FILE} | sed 's/==/=/g'| tr "\n" " ")
fi


echo '[INFO] Install and setup eatmydata'
sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install eatmydata
sudo LANG=C chroot $FILESYSTEM_ROOT ln -s /usr/bin/eatmydata /usr/local/bin/dpkg
echo 'Dir::Bin::dpkg "/usr/local/bin/dpkg";' | sudo tee $FILESYSTEM_ROOT/etc/apt/apt.conf.d/00image-install-eatmydata > /dev/null

echo '[INFO] Install packages for building image'
sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install makedev psmisc

## Create device files
echo '[INFO] MAKEDEV'
if [[ $CONFIGURED_ARCH == armhf || $CONFIGURED_ARCH == arm64 ]]; then
    sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c 'cd /dev && MAKEDEV generic-arm'
else
    sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c 'cd /dev && MAKEDEV generic'
fi
## Install initramfs-tools and linux kernel
## Note: initramfs-tools recommends depending on busybox, and we really want busybox for
## 1. commands such as touch
## 2. mount supports squashfs
## However, 'dpkg -i' plus 'apt-get install -f' will ignore the recommended dependency. So
## we install busybox explicitly
sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install busybox linux-base


## Install docker
echo '[INFO] Install docker'
## Install apparmor utils since they're missing and apparmor is enabled in the kernel
## Otherwise Docker will fail to start
sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install apparmor
sudo cp files/image_config/ntp/ntp-apparmor $FILESYSTEM_ROOT/etc/apparmor.d/local/usr.sbin.ntpd
sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install apt-transport-https \
                                                       ca-certificates \
                                                       curl \
                                                       gnupg2 \
                                                       software-properties-common
if [[ $CONFIGURED_ARCH == armhf ]]; then
    # update ssl ca certificates for secure pem
    sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT c_rehash
fi
sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT curl -o /tmp/docker.gpg -fsSL https://download.docker.com/linux/debian/gpg
sudo LANG=C chroot $FILESYSTEM_ROOT apt-key add /tmp/docker.gpg
sudo LANG=C chroot $FILESYSTEM_ROOT rm /tmp/docker.gpg
sudo LANG=C chroot $FILESYSTEM_ROOT add-apt-repository \
                                    "deb [arch=$CONFIGURED_ARCH] https://download.docker.com/linux/debian $IMAGE_DISTRO stable"
sudo LANG=C FORCE_UPDATE=Y chroot $FILESYSTEM_ROOT apt-get update
if dpkg --compare-versions ${DOCKER_VERSION} ge "18.09"; then
    sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install docker-ce=${DOCKER_VERSION} docker-ce-cli=${DOCKER_VERSION}
else
    sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install docker-ce=${DOCKER_VERSION}
fi

# Uninstall 'python3-gi' installed as part of 'software-properties-common' to remove debian version of 'PyGObject'
# pip version of 'PyGObject' will be installed during installation of 'sonic-host-services'
sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y remove software-properties-common gnupg2 python3-gi

if [ "$INCLUDE_KUBERNETES" == "y" ]
then
    ## Install Kubernetes
    echo '[INFO] Install kubernetes'
    sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT curl -fsSL \
        https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
        sudo LANG=C chroot $FILESYSTEM_ROOT apt-key add -
    ## Check out the sources list update matches current Debian version
    sudo cp files/image_config/kubernetes/kubernetes.list $FILESYSTEM_ROOT/etc/apt/sources.list.d/
    sudo LANG=C chroot $FILESYSTEM_ROOT apt-get update
    sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install kubernetes-cni=${KUBERNETES_CNI_VERSION}-00
    sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install kubelet=${KUBERNETES_VERSION}-00
    sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install kubectl=${KUBERNETES_VERSION}-00
    sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install kubeadm=${KUBERNETES_VERSION}-00
else
    echo '[INFO] Skipping Install kubernetes'
fi

## Add docker config drop-in to specify dockerd command line
sudo mkdir -p $FILESYSTEM_ROOT/etc/systemd/system/docker.service.d/
## Note: $_ means last argument of last command
sudo cp files/docker/docker.service.conf $_
## Fix systemd race between docker and containerd
sudo sed -i '/After=/s/$/ containerd.service/' $FILESYSTEM_ROOT/lib/systemd/system/docker.service

## Create default user
## Note: user should be in the group with the same name, and also in sudo/docker/redis groups
sudo LANG=C chroot $FILESYSTEM_ROOT useradd -G sudo,docker $USERNAME -c "$DEFAULT_USERINFO" -m -s /bin/bash
## Create password for the default user
echo "$USERNAME:$PASSWORD" | sudo LANG=C chroot $FILESYSTEM_ROOT chpasswd

## Create redis group
sudo LANG=C chroot $FILESYSTEM_ROOT groupadd -f redis
sudo LANG=C chroot $FILESYSTEM_ROOT usermod -aG redis $USERNAME

if [[ $CONFIGURED_ARCH == amd64 ]]; then
    ## Pre-install hardware drivers
    sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install      \
        firmware-linux-nonfree
fi

## Pre-install the fundamental packages
## Note: gdisk is needed for sgdisk in install.sh
## Note: parted is needed for partprobe in install.sh
## Note: ca-certificates is needed for easy_install
## Note: don't install python-apt by pip, older than Debian repo one
## Note: fdisk and gpg are needed by fwutil
sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y install      \
    file                    \
    ifmetric                \
    iproute2                \
    bridge-utils            \
    isc-dhcp-client         \
    sudo                    \
    vim                     \
    tcpdump                 \
    dbus                    \
    ntpstat                 \
    openssh-server          \
    python3-apt             \
    traceroute              \
    iputils-ping            \
    net-tools               \
    bsdmainutils            \
    ca-certificates         \
    i2c-tools               \
    efibootmgr              \
    usbutils                \
    pciutils                \
    iptables-persistent     \
    ebtables                \
    logrotate               \
    curl                    \
    kexec-tools             \
    less                    \
    unzip                   \
    gdisk                   \
    sysfsutils              \
    squashfs-tools          \
    grub2-common            \
    rsyslog                 \
    screen                  \
    hping3                  \
    tcptraceroute           \
    mtr-tiny                \
    locales                 \
    cgroup-tools            \
    ipmitool                \
    ndisc6                  \
    makedumpfile            \
    conntrack               \
    python3                 \
    python3-distutils       \
    python3-pip             \
    python-is-python3       \
    cron                    \
    libprotobuf23           \
    libgrpc++1              \
    libgrpc10               \
    haveged                 \
    fdisk                   \
    gpg                     \
    jq                      \
    auditd



# Have systemd create the auditd log directory
sudo mkdir -p ${FILESYSTEM_ROOT}/etc/systemd/system/auditd.service.d
sudo tee ${FILESYSTEM_ROOT}/etc/systemd/system/auditd.service.d/log-directory.conf >/dev/null <<EOF
[Service]
LogsDirectory=audit
LogsDirectoryMode=0750
EOF

if [[ $CONFIGURED_ARCH == amd64 ]]; then
## Pre-install the fundamental packages for amd64 (x86)
sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y install      \
    rasdaemon
fi

## Set /etc/shadow permissions to -rw-------.
sudo LANG=c chroot $FILESYSTEM_ROOT chmod 600 /etc/shadow

## Set /etc/passwd, /etc/group permissions to -rw-r--r--.
sudo LANG=c chroot $FILESYSTEM_ROOT chmod 644 /etc/passwd
sudo LANG=c chroot $FILESYSTEM_ROOT chmod 644 /etc/group

# Needed to install kdump-tools
sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "mkdir -p /etc/initramfs-tools/conf.d"
sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo 'MODULES=most' >> /etc/initramfs-tools/conf.d/driver-policy"

# Copy vmcore-sysctl.conf to add more vmcore dump flags to kernel
sudo cp files/image_config/kdump/vmcore-sysctl.conf $FILESYSTEM_ROOT/etc/sysctl.d/

#Adds a locale to a debian system in non-interactive mode
sudo sed -i '/^#.* en_US.* /s/^#//' $FILESYSTEM_ROOT/etc/locale.gen && \
    sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT locale-gen "en_US.UTF-8"
sudo LANG=en_US.UTF-8 DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT update-locale "LANG=en_US.UTF-8"
sudo LANG=C chroot $FILESYSTEM_ROOT bash -c "find /usr/share/i18n/locales/ ! -name 'en_US' -type f -exec rm -f {} +"

sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y install \
    picocom \
    systemd \
    systemd-sysv \
    ntp

if [[ $CONFIGURED_ARCH == amd64 ]]; then
    sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y download \
        grub-pc-bin

    sudo mv $FILESYSTEM_ROOT/grub-pc-bin*.deb $FILESYSTEM_ROOT/$PLATFORM_DIR/x86_64-grub
fi

# Pre-install the list of deian packages which are required at the later part of the installation.
# These packages are installed either directly or required as a dependency for the main package.
# Pre-installation of these packages will skip the installation of the same package at the later stage
# and will speed up the build process.
# These packages are not removed from the original place to avoid the merge issues during branch merge. 
PIP_PKG_LIST_FILE=files/build/versions/host-image/versions-pip3-${IMAGE_DISTRO}-${CONFIGURED_ARCH}
if [[ ! -z ${SONIC_VERSION_CACHE} && ${SONIC_VERSION_CACHE} != "none" && -e ${PIP_PKG_LIST_FILE} ]]; then
	sudo https_proxy=$https_proxy LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT pip3 install \
		$(cat ${PIP_PKG_LIST_FILE} | tr "\n" " ")
fi


# Install dependencies for SONiC config engine
sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y install \
    python3-dev

# Install j2cli for handling jinja template
sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT pip3 install "j2cli==0.3.10"

# Install Python client for Redis
sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT pip3 install "redis==3.5.3"


## Add mtd and uboot firmware tools package
sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install u-boot-tools libubootenv-tool mtd-utils device-tree-compiler


# Upgrade pip via PyPI and uninstall the Debian version
sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT pip3 install --upgrade pip
sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get purge -y python3-pip

# For building Python packages
sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT pip3 install 'setuptools==49.6.00'
sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT pip3 install 'wheel==0.35.1'

# docker Python API package is needed by Ansible docker module as well as some SONiC applications
sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT pip3 install 'docker==5.0.3'

# Install scapy
sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT pip3 install 'scapy==2.4.4'

## Note: keep pip installed for maintainance purpose

# Install GCC, needed for building/installing some Python packages
sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y install gcc

## Create /var/run/redis folder for docker-database to mount
sudo mkdir -p $FILESYSTEM_ROOT/var/run/redis

## Config DHCP for eth0
sudo tee -a $FILESYSTEM_ROOT/etc/network/interfaces > /dev/null <<EOF

auto eth0
allow-hotplug eth0
iface eth0 inet dhcp
EOF



# Install Python module for psutil
sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT pip3 install psutil

# Install Python module for ipaddr
sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT pip3 install ipaddr

# Install Python module for grpcio and grpcio-toole
if [[ $CONFIGURED_ARCH == amd64 ]]; then
    sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT pip3 install "grpcio==1.39.0"
    sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT pip3 install "grpcio-tools==1.39.0"
fi



# Install dependency pkgs for SONiC config engine Python 2 package
if [[ $CONFIGURED_ARCH == armhf || $CONFIGURED_ARCH == arm64 ]]; then
    sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y install libxslt-dev libz-dev
fi



# Install prerequisites needed for installing the Python m2crypto package, used by sonic-utilities
# These packages can be uninstalled after intallation
sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y install build-essential libssl-dev swig

# Install prerequisites needed for using the Python m2crypto package, used by sonic-utilities
sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y install openssl


# Install prerequisites needed for installing the dependent Python packages of sonic-host-services
# These packages can be uninstalled after installation
sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y install libcairo2-dev libdbus-1-dev libgirepository1.0-dev libsystemd-dev pkg-config

# Mark runtime dependencies as manually installed to avoid them being auto-removed while uninstalling build dependencies
sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-mark manual gir1.2-glib-2.0 libdbus-1-3 libgirepository-1.0-1 libsystemd0 python3-dbus

# Install systemd-python for SONiC host services
sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT pip3 install systemd-python



# Install custom-built smartmontools
sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y install smartmontools=7.2-1

sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y install libffi-dev libssl-dev

if [[ $CONFIGURED_ARCH == armhf ]]; then
    # The azure-storage package depends on the cryptography package. Newer
    # versions of cryptography require the rust compiler, the correct version
    # for which is not readily available in buster. Hence we pre-install an
    # older version here to satisfy the azure-storage dependency.
    # Note: This is not a problem for other architectures as pre-built versions
    # of cryptography are available for those. This sequence can be removed
    # after upgrading to debian bullseye.
    sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT pip3 install cryptography==3.3.1
fi
sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT pip3 install azure-storage==0.36.0
sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT pip3 install watchdog==0.10.3


# For sonic-config-engine Python 3 package
# Install pyangbind here, outside sonic-config-engine dependencies, as pyangbind causes enum34 to be installed.
# Then immediately uninstall enum34, as enum34 should not be installed for Python >= 3.4, as it causes a
# conflict with the new 'enum' module in the standard library
# https://github.com/robshakir/pyangbind/issues/232
sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT pip3 install pyangbind==0.8.1
sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT pip3 uninstall -y enum34


sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT pip3 install PyYAML==5.3.1

sync; sync; sync;
## Output all the mounted device for troubleshooting
echo '[INFO] Show Mount all'
sudo LANG=C chroot $FILESYSTEM_ROOT mount
sync; sync; sync;

#Exit trap handles the umount
#sudo LANG=C chroot $FILESYSTEM_ROOT umount /proc || true
#BASE_IMAGE_NAME=${BASE_IMAGE_NAME} scripts/fsutil.sh rootfs umount  

## ensure proc is mounted
sudo mountpoint -q /proc || sudo mount -t proc proc /proc || true
echo "Rootfs Done"
