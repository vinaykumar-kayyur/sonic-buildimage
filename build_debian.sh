#!/bin/bash -xe
## This script is to automate the preparation for a debian file system, which will be used for
## an ONIE installer image.
## This is the 2nd part. 1st part in build_rfs.sh
##
## USAGE:
##   USERNAME=username PASSWORD=password ./build_debian
## ENVIRONMENT:
##   USERNAME
##          The name of the default admin user
##   PASSWORD
##          The password, expected by chpasswd command

## Include common functions
. functions.sh

[ -n "$USERNAME" ] || die "[ERROR] USERNAME is not set"
[ -n "$PASSWORD" ] || die "[ERROR] PASSWORD is not set"
[ -n "$RFS_SQUASHFS_NAME" ] || die "[ERROR] RFS_SQUASHFS_NAME is not set"

LINUX_KERNEL_VERSION=$SONIC_LINUX_KERNEL_VERSION

## Working directory to prepare the file system
FILESYSTEM_ROOT=./fsroot
PLATFORM_DIR=platform
DEFAULT_USERINFO="Default admin user,,,"

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

if [ "$IMAGE_TYPE" = "aboot" ]; then
    TARGET_BOOTLOADER="aboot"
fi

## ensure proc is mounted
sudo mount proc /proc -t proc || true

## Prepare the file system directory
sudo rm -rf $FILESYSTEM_ROOT || die "Failed to clean chroot directory"
## Extract 1st stage RFS (build_rfs.sh)
sudo unsquashfs -d $FILESYSTEM_ROOT $TARGET_PATH/$RFS_SQUASHFS_NAME

## make / as a mountpoint in chroot env, needed by dockerd
pushd $FILESYSTEM_ROOT
sudo mount --bind . .
popd

sudo chown root:root $FILESYSTEM_ROOT

## Update /etc/resolv.conf
sudo cat /etc/resolv.conf | sudo tee $FILESYSTEM_ROOT/etc/resolv.conf

## Setup proxy
[ -n "$http_proxy" ] && sudo /bin/bash -c "echo 'Acquire::http::Proxy \"$http_proxy\";' > $FILESYSTEM_ROOT/etc/apt/apt.conf.d/01proxy"

## Mount /proc.
trap_push "sudo LANG=C chroot $FILESYSTEM_ROOT umount /proc || true"
sudo LANG=C chroot $FILESYSTEM_ROOT mount proc /proc -t proc

sudo LANG=C chroot $FILESYSTEM_ROOT apt-get update

## Sign the Linux kernel
# note: when flag SONIC_ENABLE_SECUREBOOT_SIGNATURE is enabled the Secure Upgrade flags should be disabled (no_sign) to avoid conflict between the features.
if [ "$SONIC_ENABLE_SECUREBOOT_SIGNATURE" = "y" ] && [ "$SECURE_UPGRADE_MODE" != 'dev' ] && [ "$SECURE_UPGRADE_MODE" != "prod" ]; then
    if [ ! -f $SIGNING_KEY ]; then
       echo "Error: SONiC linux kernel signing key missing"
       exit 1
    fi
    if [ ! -f $SIGNING_CERT ]; then
       echo "Error: SONiC linux kernel signing certificate missing"
       exit 1
    fi

    echo '[INFO] Signing SONiC linux kernel image'
    K=$FILESYSTEM_ROOT/boot/vmlinuz-${LINUX_KERNEL_VERSION}-${CONFIGURED_ARCH}
    sbsign --key $SIGNING_KEY --cert $SIGNING_CERT --output /tmp/${K##*/} ${K}
    sudo cp -f /tmp/${K##*/} ${K}
fi

## Update initramfs for booting with squashfs+overlay
cat files/initramfs-tools/modules | sudo tee -a $FILESYSTEM_ROOT/etc/initramfs-tools/modules > /dev/null

## Hook into initramfs: change fs type from vfat to ext4 on arista switches
sudo mkdir -p $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-premount/
sudo cp files/initramfs-tools/arista-convertfs $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-premount/arista-convertfs
sudo chmod +x $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-premount/arista-convertfs
sudo cp files/initramfs-tools/arista-hook $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-premount/arista-hook
sudo chmod +x $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-premount/arista-hook
sudo cp files/initramfs-tools/mke2fs $FILESYSTEM_ROOT/etc/initramfs-tools/hooks/mke2fs
sudo chmod +x $FILESYSTEM_ROOT/etc/initramfs-tools/hooks/mke2fs
sudo cp files/initramfs-tools/setfacl $FILESYSTEM_ROOT/etc/initramfs-tools/hooks/setfacl
sudo chmod +x $FILESYSTEM_ROOT/etc/initramfs-tools/hooks/setfacl

# Hook into initramfs: rename the management interfaces on arista switches
sudo cp files/initramfs-tools/arista-net $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-premount/arista-net
sudo chmod +x $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-premount/arista-net

# Hook into initramfs: resize root partition after migration from another NOS to SONiC on Dell switches
sudo cp files/initramfs-tools/resize-rootfs $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-premount/resize-rootfs
sudo chmod +x $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-premount/resize-rootfs

# Hook into initramfs: upgrade SSD from initramfs
sudo cp files/initramfs-tools/ssd-upgrade $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-premount/ssd-upgrade
sudo chmod +x $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-premount/ssd-upgrade

# Hook into initramfs: run fsck to repair a non-clean filesystem prior to be mounted
sudo cp files/initramfs-tools/fsck-rootfs $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-premount/fsck-rootfs
sudo chmod +x $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-premount/fsck-rootfs

## Hook into initramfs: after partition mount and loop file mount
## 1. Prepare layered file system
## 2. Bind-mount docker working directory (docker overlay storage cannot work over overlay rootfs)
sudo cp files/initramfs-tools/union-mount $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-bottom/union-mount
sudo chmod +x $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-bottom/union-mount
sudo cp files/initramfs-tools/varlog $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-bottom/varlog
sudo chmod +x $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-bottom/varlog
# Management interface (eth0) dhcp can be optionally turned off (during a migration from another NOS to SONiC)
#sudo cp files/initramfs-tools/mgmt-intf-dhcp $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-bottom/mgmt-intf-dhcp
#sudo chmod +x $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-bottom/mgmt-intf-dhcp
sudo cp files/initramfs-tools/union-fsck $FILESYSTEM_ROOT/etc/initramfs-tools/hooks/union-fsck
sudo chmod +x $FILESYSTEM_ROOT/etc/initramfs-tools/hooks/union-fsck
pushd $FILESYSTEM_ROOT/usr/share/initramfs-tools/scripts/init-bottom && sudo patch -p1 < $OLDPWD/files/initramfs-tools/udev.patch; popd
if [[ $CONFIGURED_ARCH == armhf || $CONFIGURED_ARCH == arm64 ]]; then
    sudo cp files/initramfs-tools/uboot-utils $FILESYSTEM_ROOT/etc/initramfs-tools/hooks/uboot-utils
    sudo chmod +x $FILESYSTEM_ROOT/etc/initramfs-tools/hooks/uboot-utils
    cat files/initramfs-tools/modules.arm | sudo tee -a $FILESYSTEM_ROOT/etc/initramfs-tools/modules > /dev/null
fi
# Update initramfs for load platform specific modules
if [ -f platform/$CONFIGURED_PLATFORM/modules ]; then
    cat platform/$CONFIGURED_PLATFORM/modules | sudo tee -a $FILESYSTEM_ROOT/etc/initramfs-tools/modules > /dev/null
fi

sudo cp files/image_config/ntp/ntp-apparmor $FILESYSTEM_ROOT/etc/apparmor.d/local/usr.sbin.ntpd

install_kubernetes () {
    local ver="$1"
    sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install gnupg
    sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y remove gnupg
    sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT curl -fsSL \
        https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
        sudo LANG=C chroot $FILESYSTEM_ROOT apt-key add -
    ## Check out the sources list update matches current Debian version
    sudo cp files/image_config/kubernetes/kubernetes.list $FILESYSTEM_ROOT/etc/apt/sources.list.d/
    sudo LANG=C chroot $FILESYSTEM_ROOT apt-get update
    sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install kubernetes-cni=${KUBERNETES_CNI_VERSION}
    sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install kubelet=${ver}
    sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install kubectl=${ver}
    sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install kubeadm=${ver}
}

if [ "$INCLUDE_KUBERNETES" == "y" ]
then
    ## Install Kubernetes
    echo '[INFO] Install kubernetes'
    install_kubernetes ${KUBERNETES_VERSION}
else
    echo '[INFO] Skipping Install kubernetes'
fi

if [ "$INCLUDE_KUBERNETES_MASTER" == "y" ]
then
    ## Install Kubernetes master
    echo '[INFO] Install kubernetes master'
    install_kubernetes ${MASTER_KUBERNETES_VERSION}

    sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install hyperv-daemons xmlstarlet parted netcat
    sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT curl -o /tmp/cri-dockerd.deb -fsSL \
        https://github.com/Mirantis/cri-dockerd/releases/download/v${MASTER_CRI_DOCKERD}/cri-dockerd_${MASTER_CRI_DOCKERD}.3-0.debian-${IMAGE_DISTRO}_amd64.deb
    sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install -f /tmp/cri-dockerd.deb
    sudo LANG=C chroot $FILESYSTEM_ROOT rm -f /tmp/cri-dockerd.deb
else
    echo '[INFO] Skipping Install kubernetes master'
fi

## Add docker config drop-in to specify dockerd command line
sudo mkdir -p $FILESYSTEM_ROOT/etc/systemd/system/docker.service.d/
## Note: $_ means last argument of last command
sudo cp files/docker/docker.service.conf $_

## Create default user
## Note: user should be in the group with the same name, and also in sudo/docker/redis groups
sudo LANG=C chroot $FILESYSTEM_ROOT useradd -G sudo,docker $USERNAME -c "$DEFAULT_USERINFO" -m -s /bin/bash
## Create password for the default user
echo "$USERNAME:$PASSWORD" | sudo LANG=C chroot $FILESYSTEM_ROOT chpasswd

## Create redis group
sudo LANG=C chroot $FILESYSTEM_ROOT groupadd -f redis
sudo LANG=C chroot $FILESYSTEM_ROOT usermod -aG redis $USERNAME

# Have systemd create the auditd log directory
sudo mkdir -p ${FILESYSTEM_ROOT}/etc/systemd/system/auditd.service.d
sudo tee ${FILESYSTEM_ROOT}/etc/systemd/system/auditd.service.d/log-directory.conf >/dev/null <<EOF
[Service]
LogsDirectory=audit
LogsDirectoryMode=0750
EOF

# latest tcpdump control resource access with AppArmor.
# override tcpdump profile to allow tcpdump access TACACS config file.
sudo cp files/apparmor/usr.bin.tcpdump $FILESYSTEM_ROOT/etc/apparmor.d/local/usr.bin.tcpdump

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

# Workaround for issue: The udev rule may fail to be executed because the
#                       daemon-reload command is executed in parallel
# Github issue: https://github.com/systemd/systemd/issues/24668
# Github PR: https://github.com/systemd/systemd/pull/24673
# This workaround should be removed after a upstream already contains the fixes
sudo patch $FILESYSTEM_ROOT/lib/systemd/system/systemd-udevd.service \
    files/image_config/systemd/systemd-udevd/fix-udev-rule-may-fail-if-daemon-reload-command-runs.patch

## Disable kexec supported reboot which was installed by default
sudo sed -i 's/LOAD_KEXEC=true/LOAD_KEXEC=false/' $FILESYSTEM_ROOT/etc/default/kexec

## Remove sshd host keys, and will regenerate on first sshd start
sudo rm -f $FILESYSTEM_ROOT/etc/ssh/ssh_host_*_key*
sudo cp files/sshd/host-ssh-keygen.sh $FILESYSTEM_ROOT/usr/local/bin/
sudo mkdir $FILESYSTEM_ROOT/etc/systemd/system/ssh.service.d
sudo cp files/sshd/override.conf $FILESYSTEM_ROOT/etc/systemd/system/ssh.service.d/override.conf
# Config sshd
# 1. Set 'UseDNS' to 'no'
# 2. Configure sshd to close all SSH connetions after 15 minutes of inactivity
sudo augtool -r $FILESYSTEM_ROOT <<'EOF'
touch /files/etc/ssh/sshd_config/EmptyLineHack
rename /files/etc/ssh/sshd_config/EmptyLineHack ""
set /files/etc/ssh/sshd_config/UseDNS no
ins #comment before /files/etc/ssh/sshd_config/UseDNS
set /files/etc/ssh/sshd_config/#comment[following-sibling::*[1][self::UseDNS]] "Disable hostname lookups"

rm /files/etc/ssh/sshd_config/ClientAliveInterval
rm /files/etc/ssh/sshd_config/ClientAliveCountMax
touch /files/etc/ssh/sshd_config/EmptyLineHack
rename /files/etc/ssh/sshd_config/EmptyLineHack ""
set /files/etc/ssh/sshd_config/ClientAliveInterval 900
set /files/etc/ssh/sshd_config/ClientAliveCountMax 0
ins #comment before /files/etc/ssh/sshd_config/ClientAliveInterval
set /files/etc/ssh/sshd_config/#comment[following-sibling::*[1][self::ClientAliveInterval]] "Close inactive client sessions after 15 minutes"
rm /files/etc/ssh/sshd_config/LogLevel
set /files/etc/ssh/sshd_config/LogLevel VERBOSE
save
quit
EOF
# Configure sshd to listen for v4 and v6 connections
sudo sed -i 's/^#ListenAddress 0.0.0.0/ListenAddress 0.0.0.0/' $FILESYSTEM_ROOT/etc/ssh/sshd_config
sudo sed -i 's/^#ListenAddress ::/ListenAddress ::/' $FILESYSTEM_ROOT/etc/ssh/sshd_config

## Config rsyslog
sudo augtool -r $FILESYSTEM_ROOT --autosave "
rm /files/lib/systemd/system/rsyslog.service/Service/ExecStart/arguments
set /files/lib/systemd/system/rsyslog.service/Service/ExecStart/arguments/1 -n
"
sudo mkdir -p $FILESYSTEM_ROOT/var/core

# Config sysctl
sudo augtool --autosave "
set /files/etc/sysctl.conf/kernel.core_pattern '|/usr/local/bin/coredump-compress %e %t %p %P'
set /files/etc/sysctl.conf/kernel.softlockup_panic 1
set /files/etc/sysctl.conf/kernel.panic 10
set /files/etc/sysctl.conf/kernel.hung_task_timeout_secs 300
set /files/etc/sysctl.conf/vm.panic_on_oom 2
set /files/etc/sysctl.conf/fs.suid_dumpable 2
" -r $FILESYSTEM_ROOT

sysctl_net_cmd_string=""
while read line; do
  [[ "$line" =~ ^#.*$ ]] && continue
  sysctl_net_conf_key=`echo $line | awk -F '=' '{print $1}'`
  sysctl_net_conf_value=`echo $line | awk -F '=' '{print $2}'`
  sysctl_net_cmd_string=$sysctl_net_cmd_string"set /files/etc/sysctl.conf/$sysctl_net_conf_key $sysctl_net_conf_value"$'\n'
done < files/image_config/sysctl/sysctl-net.conf

sudo augtool --autosave "$sysctl_net_cmd_string" -r $FILESYSTEM_ROOT

## Create /var/run/redis folder for docker-database to mount
sudo mkdir -p $FILESYSTEM_ROOT/var/run/redis

## Config DHCP for eth0
sudo tee -a $FILESYSTEM_ROOT/etc/network/interfaces > /dev/null <<EOF

auto eth0
allow-hotplug eth0
iface eth0 inet dhcp
EOF

sudo cp files/dhcp/rfc3442-classless-routes $FILESYSTEM_ROOT/etc/dhcp/dhclient-exit-hooks.d
sudo cp files/dhcp/sethostname $FILESYSTEM_ROOT/etc/dhcp/dhclient-exit-hooks.d/
sudo cp files/dhcp/sethostname6 $FILESYSTEM_ROOT/etc/dhcp/dhclient-exit-hooks.d/
sudo cp files/dhcp/graphserviceurl $FILESYSTEM_ROOT/etc/dhcp/dhclient-exit-hooks.d/
sudo cp files/dhcp/snmpcommunity $FILESYSTEM_ROOT/etc/dhcp/dhclient-exit-hooks.d/
sudo cp files/dhcp/vrf $FILESYSTEM_ROOT/etc/dhcp/dhclient-exit-hooks.d/
if [ -f files/image_config/ntp/ntp ]; then
    sudo cp ./files/image_config/ntp/ntp $FILESYSTEM_ROOT/etc/init.d/
fi

if [ -f files/image_config/ntp/ntp-systemd-wrapper ]; then
    sudo mkdir -p $FILESYSTEM_ROOT/usr/lib/ntp/
    sudo cp ./files/image_config/ntp/ntp-systemd-wrapper $FILESYSTEM_ROOT/usr/lib/ntp/
fi

## Version file
sudo mkdir -p $FILESYSTEM_ROOT/etc/sonic
if [ -f files/image_config/sonic_release ]; then
    sudo cp files/image_config/sonic_release $FILESYSTEM_ROOT/etc/sonic/
fi
export build_version="${SONIC_IMAGE_VERSION}"
export debian_version="$(cat $FILESYSTEM_ROOT/etc/debian_version)"
export kernel_version="${kversion}"
export asic_type="${sonic_asic_platform}"
export asic_subtype="${TARGET_MACHINE}"
export commit_id="$(git rev-parse --short HEAD)"
export branch="$(git rev-parse --abbrev-ref HEAD)"
export release="$(if [ -f $FILESYSTEM_ROOT/etc/sonic/sonic_release ]; then cat $FILESYSTEM_ROOT/etc/sonic/sonic_release; fi)"
export build_date="$(date -u)"
export build_number="${BUILD_NUMBER:-0}"
export built_by="$USER@$BUILD_HOSTNAME"
export sonic_os_version="${SONIC_OS_VERSION}"
j2 files/build_templates/sonic_version.yml.j2 | sudo tee $FILESYSTEM_ROOT/etc/sonic/sonic_version.yml

if [ -f sonic_debian_extension.sh ]; then
    ./sonic_debian_extension.sh $FILESYSTEM_ROOT $PLATFORM_DIR $IMAGE_DISTRO
fi

# Default users info
export password_expire="$( [[ "$CHANGE_DEFAULT_PASSWORD" == "y" ]] && echo true || echo false )"
export username="${USERNAME}"
export password="$(sudo grep ^${USERNAME} $FILESYSTEM_ROOT/etc/shadow | cut -d: -f2)"
j2 files/build_templates/default_users.json.j2 | sudo tee $FILESYSTEM_ROOT/etc/sonic/default_users.json
sudo LANG=c chroot $FILESYSTEM_ROOT chmod 600 /etc/sonic/default_users.json
sudo LANG=c chroot $FILESYSTEM_ROOT chown root:shadow /etc/sonic/default_users.json

## Copy over clean-up script
sudo cp ./files/scripts/core_cleanup.py $FILESYSTEM_ROOT/usr/bin/core_cleanup.py

## Copy ASIC config checksum
sudo chmod 755 files/build_scripts/generate_asic_config_checksum.py
./files/build_scripts/generate_asic_config_checksum.py
if [[ ! -f './asic_config_checksum' ]]; then
    echo 'asic_config_checksum not found'
    exit 1
fi
sudo cp ./asic_config_checksum $FILESYSTEM_ROOT/etc/sonic/asic_config_checksum

## Organization specific extensions such as Configuration & Scripts for features like AAA, ZTP...
if [ "${enable_organization_extensions}" = "y" ]; then
   if [ -f files/build_templates/organization_extensions.sh ]; then
      sudo chmod 755 files/build_templates/organization_extensions.sh
      ./files/build_templates/organization_extensions.sh -f $FILESYSTEM_ROOT -h $SONIC_DEFAULT_HOSTNAME
   fi
fi

## Setup ebtable rules (rule file in text format)
sudo cp files/image_config/ebtables/ebtables.filter.cfg ${FILESYSTEM_ROOT}/etc

## Debug Image specific changes
## Update motd for debug image
if [ "$DEBUG_IMG" == "y" ]
then
    sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo '**************' >> /etc/motd"
    sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo 'Running DEBUG image' >> /etc/motd"
    sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo '**************' >> /etc/motd"
    sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo '/src has the sources' >> /etc/motd"
    sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo '/src is mounted in each docker' >> /etc/motd"
    sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo '/debug is created for core files or temp files' >> /etc/motd"
    sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo 'Create a subdir under /debug to upload your files' >> /etc/motd"
    sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo '/debug is mounted in each docker' >> /etc/motd"

    sudo mkdir -p $FILESYSTEM_ROOT/src
    sudo cp $DEBUG_SRC_ARCHIVE_FILE $FILESYSTEM_ROOT/src/
    sudo mkdir -p $FILESYSTEM_ROOT/debug

fi

## Set FIPS runtime default option
sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "mkdir -p /etc/fips"
sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo 0 > /etc/fips/fips_enable"

# #################
#   secure boot
# #################
if [[ $SECURE_UPGRADE_MODE == 'dev' || $SECURE_UPGRADE_MODE == "prod" && $SONIC_ENABLE_SECUREBOOT_SIGNATURE != 'y' ]]; then
    # note: SONIC_ENABLE_SECUREBOOT_SIGNATURE is a feature that signing just kernel,
    # SECURE_UPGRADE_MODE is signing all the boot component including kernel.
    # its required to do not enable both features together to avoid conflicts.
    echo "Secure Boot support build stage: Starting .."

    # debian secure boot dependecies
    sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y install      \
        shim-unsigned \
        grub-efi

    if [ ! -f $SECURE_UPGRADE_SIGNING_CERT ]; then
        echo "Error: SONiC SECURE_UPGRADE_SIGNING_CERT=$SECURE_UPGRADE_SIGNING_CERT key missing"
        exit 1
    fi

    if [[ $SECURE_UPGRADE_MODE == 'dev' ]]; then
        # development signing & verification

        if [ ! -f $SECURE_UPGRADE_DEV_SIGNING_KEY ]; then
            echo "Error: SONiC SECURE_UPGRADE_DEV_SIGNING_KEY=$SECURE_UPGRADE_DEV_SIGNING_KEY key missing"
            exit 1
        fi

        sudo ./scripts/signing_secure_boot_dev.sh -a $CONFIGURED_ARCH \
                                                  -r $FILESYSTEM_ROOT \
                                                  -l $LINUX_KERNEL_VERSION \
                                                  -c $SECURE_UPGRADE_SIGNING_CERT \
                                                  -p $SECURE_UPGRADE_DEV_SIGNING_KEY
    elif [[ $SECURE_UPGRADE_MODE == "prod" ]]; then
        #  Here Vendor signing should be implemented
        OUTPUT_SEC_BOOT_DIR=$FILESYSTEM_ROOT/boot

        if [ ! -f $sonic_su_prod_signing_tool ]; then
            echo "Error: SONiC sonic_su_prod_signing_tool=$sonic_su_prod_signing_tool script missing"
            exit 1
        fi

        sudo $sonic_su_prod_signing_tool -a $CONFIGURED_ARCH \
                                         -r $FILESYSTEM_ROOT \
                                         -l $LINUX_KERNEL_VERSION \
                                         -o $OUTPUT_SEC_BOOT_DIR \
                                         $SECURE_UPGRADE_PROD_TOOL_ARGS

        # verifying all EFI files and kernel modules in $OUTPUT_SEC_BOOT_DIR
        sudo ./scripts/secure_boot_signature_verification.sh -e $OUTPUT_SEC_BOOT_DIR \
                                                             -c $SECURE_UPGRADE_SIGNING_CERT \
                                                             -k $FILESYSTEM_ROOT

        # verifying vmlinuz file.
        sudo ./scripts/secure_boot_signature_verification.sh -e $FILESYSTEM_ROOT/boot/vmlinuz-${LINUX_KERNEL_VERSION}-${CONFIGURED_ARCH} \
                                                             -c $SECURE_UPGRADE_SIGNING_CERT \
                                                             -k $FILESYSTEM_ROOT
    fi
    echo "Secure Boot support build stage: END."
fi

## Update initramfs
sudo chroot $FILESYSTEM_ROOT update-initramfs -u
## Convert initrd image to u-boot format
if [[ $TARGET_BOOTLOADER == uboot ]]; then
    INITRD_FILE=initrd.img-${LINUX_KERNEL_VERSION}-${CONFIGURED_ARCH}
    if [[ $CONFIGURED_ARCH == armhf ]]; then
        INITRD_FILE=initrd.img-${LINUX_KERNEL_VERSION}-armmp
        sudo LANG=C chroot $FILESYSTEM_ROOT mkimage -A arm -O linux -T ramdisk -C gzip -d /boot/$INITRD_FILE /boot/u${INITRD_FILE}
        ## Overwriting the initrd image with uInitrd
        sudo LANG=C chroot $FILESYSTEM_ROOT mv /boot/u${INITRD_FILE} /boot/$INITRD_FILE
    elif [[ $CONFIGURED_ARCH == arm64 ]]; then
        sudo cp -v $PLATFORM_DIR/${sonic_asic_platform}-${CONFIGURED_ARCH}/sonic_fit.its $FILESYSTEM_ROOT/boot/
        sudo LANG=C chroot $FILESYSTEM_ROOT mkimage -f /boot/sonic_fit.its /boot/sonic_${CONFIGURED_ARCH}.fit
    fi
fi

# Collect host image version files before cleanup
SONIC_VERSION_CACHE=${SONIC_VERSION_CACHE}  \
	DBGOPT="${DBGOPT}" \
	scripts/collect_host_image_version_files.sh $CONFIGURED_ARCH $IMAGE_DISTRO $TARGET_PATH $FILESYSTEM_ROOT

# Remove dev packages
sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y remove \
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

# Remove eatmydata
sudo rm $FILESYSTEM_ROOT/etc/apt/apt.conf.d/00image-install-eatmydata $FILESYSTEM_ROOT/usr/local/bin/dpkg
sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y remove eatmydata

## Clean up apt
sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y autoremove
sudo LANG=C chroot $FILESYSTEM_ROOT apt-get autoclean
sudo LANG=C chroot $FILESYSTEM_ROOT apt-get clean
sudo LANG=C chroot $FILESYSTEM_ROOT bash -c 'rm -rf /usr/share/doc/* /usr/share/locale/* /var/lib/apt/lists/* /tmp/*'

## Clean up proxy
[ -n "$http_proxy" ] && sudo rm -f $FILESYSTEM_ROOT/etc/apt/apt.conf.d/01proxy

## Clean up pip cache
sudo LANG=C chroot $FILESYSTEM_ROOT pip3 cache purge

## Umount all
echo '[INFO] Umount all'
## Display all process details access /proc
sudo LANG=C chroot $FILESYSTEM_ROOT fuser -vm /proc
## Kill the processes
sudo LANG=C chroot $FILESYSTEM_ROOT fuser -km /proc || true
## Wait fuser fully kill the processes
sudo timeout 15s bash -c 'until LANG=C chroot $0 umount /proc; do sleep 1; done' $FILESYSTEM_ROOT || true

## Prepare empty directory to trigger mount move in initramfs-tools/mount_loop_root, implemented by patching
sudo mkdir $FILESYSTEM_ROOT/host


if [[ "$CHANGE_DEFAULT_PASSWORD" == "y" ]]; then
    ## Expire default password for exitsing users that can do login
    default_users=$(cat $FILESYSTEM_ROOT/etc/passwd | grep "/home"|  grep ":/bin/bash\|:/bin/sh" | awk -F ":" '{print $1}' 2> /dev/null)
    for user in $default_users
    do
        sudo LANG=C chroot $FILESYSTEM_ROOT passwd -e ${user}
    done
fi

## Compress most file system into squashfs file
sudo rm -f $ONIE_INSTALLER_PAYLOAD $FILESYSTEM_SQUASHFS
## Output the file system total size for diag purpose
## Note: -x to skip directories on different file systems, such as /proc
sudo du -hsx $FILESYSTEM_ROOT
sudo mkdir -p $FILESYSTEM_ROOT/var/lib/docker

## Clear DNS configuration inherited from the build server
sudo rm -f $FILESYSTEM_ROOT/etc/resolvconf/resolv.conf.d/original
sudo cp files/image_config/resolv-config/resolv.conf.head $FILESYSTEM_ROOT/etc/resolvconf/resolv.conf.d/head

## Optimize filesystem size
if [ "$BUILD_REDUCE_IMAGE_SIZE" = "y" ]; then
   sudo scripts/build-optimize-fs-size.py "$FILESYSTEM_ROOT" \
      --image-type "$IMAGE_TYPE" \
      --hardlinks var/lib/docker \
      --hardlinks usr/share/sonic/device \
      --remove-docs \
      --remove-mans \
      --remove-licenses
fi

sudo mksquashfs $FILESYSTEM_ROOT $FILESYSTEM_SQUASHFS -comp zstd -b 1M -e boot -e var/lib/docker -e $PLATFORM_DIR

## Reduce /boot permission
sudo chmod -R go-wx $FILESYSTEM_ROOT/boot

# Ensure admin gid is 1000
gid_user=$(sudo LANG=C chroot $FILESYSTEM_ROOT id -g $USERNAME) || gid_user="none"
if [ "${gid_user}" != "1000" ]; then
    die "expect gid 1000. current:${gid_user}"
fi

# ALERT: This bit of logic tears down the qemu based build environment used to
# perform builds for the ARM architecture. This must be the last step in this
# script before creating the Sonic installer payload zip file.
if [[ $MULTIARCH_QEMU_ENVIRON == y || $CROSS_BUILD_ENVIRON == y ]]; then
    # Remove qemu arm bin executable used for cross-building
    sudo rm -f $FILESYSTEM_ROOT/usr/bin/qemu*static || true
    DOCKERFS_PATH=../dockerfs/
fi

## Compress docker files
pushd $FILESYSTEM_ROOT && sudo tar -I pigz -cf $OLDPWD/$FILESYSTEM_DOCKERFS -C ${DOCKERFS_PATH}var/lib/docker .; popd

## Compress together with /boot, /var/lib/docker and $PLATFORM_DIR as an installer payload zip file
pushd $FILESYSTEM_ROOT && sudo tar -I pigz -cf platform.tar.gz -C $PLATFORM_DIR . && sudo zip -n .gz $OLDPWD/$ONIE_INSTALLER_PAYLOAD -r boot/ platform.tar.gz; popd
sudo zip -g -n .squashfs:.gz $ONIE_INSTALLER_PAYLOAD $FILESYSTEM_SQUASHFS $FILESYSTEM_DOCKERFS
