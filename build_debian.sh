#!/bin/bash
## This script is to automate the preparation for a debian file system, which will be used for
## an ONIE installer image.
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
DOCKER_VERSION=5:20.10.14~3-0~debian-$IMAGE_DISTRO
CONTAINERD_IO_VERSION=1.5.11-1
LINUX_KERNEL_VERSION=5.10.0-12-2

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

mkdir -p ${BUILD_PATH}
sudo chmod -R 777 ${BUILD_PATH}
mkdir -p ${FILESYSTEM_ROOT}

## ensure proc is mounted
sudo mountpoint -q /proc || sudo mount -t proc proc /proc || true

## make / as a mountpoint in chroot env, needed by dockerd
pushd $FILESYSTEM_ROOT
sudo mount --bind . .
popd


trap_push "sudo LANG=C BASE_IMAGE_NAME=${BASE_IMAGE_NAME} scripts/fsutil.sh rootfs umount || true"
BASE_IMAGE_NAME=${BASE_IMAGE_NAME} scripts/fsutil.sh rootfs mount  


trap_push 'sudo LANG=C chroot $FILESYSTEM_ROOT umount /proc || true'
sudo LANG=C chroot $FILESYSTEM_ROOT mount proc /proc -t proc
## Note: mounting is necessary to makedev and install linux image
echo '[INFO] Mount all'
## Output all the mounted device for troubleshooting
sudo LANG=C chroot $FILESYSTEM_ROOT mount



# mount the docker tmpfs
BASE_IMAGE_NAME=${BASE_IMAGE_NAME} scripts/fsutil.sh dockerfs mount


echo '[INFO] Install SONiC linux kernel image'
## Note: duplicate apt-get command to ensure every line return zero
sudo dpkg --root=$FILESYSTEM_ROOT -i $debs_path/initramfs-tools-core_*.deb || \
    sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y install -f
sudo dpkg --root=$FILESYSTEM_ROOT -i $debs_path/initramfs-tools_*.deb || \
    sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y install -f
sudo dpkg --root=$FILESYSTEM_ROOT -i $debs_path/linux-image-${LINUX_KERNEL_VERSION}-*_${CONFIGURED_ARCH}.deb || \
    sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y install -f
sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y install acl
if [[ $CONFIGURED_ARCH == amd64 ]]; then
    sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y install dmidecode hdparm
fi

## Sign the Linux kernel
if [ "$SONIC_ENABLE_SECUREBOOT_SIGNATURE" = "y" ]; then
    if [ ! -f $SIGNING_KEY ]; then
       echo "Error: SONiC linux kernel signing key missing"
       exit 1
    fi
    if [ ! -f $SIGNING_CERT ]; then
       echo "Error: SONiC linux kernel signing certificate missing"
       exit 1
    fi

    echo '[INFO] Signing SONiC linux kernel image'
    K=$FILESYSTEM_ROOT/boot/vmlinuz-${LINUX_KERNEL_VERSION}-amd64
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
j2 files/build_templates/sonic_version.yml.j2 | sudo tee $FILESYSTEM_ROOT/etc/sonic/sonic_version.yml

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

if [ -f sonic_debian_extension.sh ]; then
    ./sonic_debian_extension.sh $FILESYSTEM_ROOT $PLATFORM_DIR $IMAGE_DISTRO
fi

## Organization specific extensions such as Configuration & Scripts for features like AAA, ZTP...
if [ "${enable_organization_extensions}" = "y" ]; then
   if [ -f files/build_templates/organization_extensions.sh ]; then
      sudo chmod 755 files/build_templates/organization_extensions.sh
      ./files/build_templates/organization_extensions.sh -f $FILESYSTEM_ROOT -h $HOSTNAME
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

## Update initramfs
sudo chroot $FILESYSTEM_ROOT update-initramfs -u
## Convert initrd image to u-boot format
if [[ $CONFIGURED_ARCH == armhf || $CONFIGURED_ARCH == arm64 ]]; then
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
scripts/collect_host_image_version_files.sh $TARGET_PATH $FILESYSTEM_ROOT

# Remove GCC
sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y remove gcc

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
sleep 15
sudo LANG=C chroot $FILESYSTEM_ROOT umount /proc || true

## Prepare empty directory to trigger mount move in initramfs-tools/mount_loop_root, implemented by patching
sudo mkdir $FILESYSTEM_ROOT/host

## Compress most file system into squashfs file
sudo rm -f $ONIE_INSTALLER_PAYLOAD $FILESYSTEM_SQUASHFS
## Output the file system total size for diag purpose
## Note: -x to skip directories on different file systems, such as /proc
sudo du -hsx $FILESYSTEM_ROOT
sudo mkdir -p $FILESYSTEM_ROOT/var/lib/docker

# mount the installer fs and it gets unmounted in slave.mk file (allfs umount)
BASE_IMAGE_NAME=${BASE_IMAGE_NAME} scripts/fsutil.sh installerfs mount

sudo mksquashfs $FILESYSTEM_ROOT ${BUILD_PATH}/$FILESYSTEM_SQUASHFS -noappend -comp zstd -b 1M -e boot -e var/lib/docker -e $PLATFORM_DIR

# Ensure admin gid is 1000
gid_user=$(sudo LANG=C chroot $FILESYSTEM_ROOT id -g $USERNAME) || gid_user="none"
if [ "${gid_user}" != "1000" ]; then
    die "expect gid 1000. current:${gid_user}"
fi

# ALERT: This bit of logic tears down the qemu based build environment used to
# perform builds for the ARM architecture. This must be the last step in this
# script before creating the Sonic installer payload zip file.
if [ $MULTIARCH_QEMU_ENVIRON == y ]; then
    # Remove qemu arm bin executable used for cross-building
    sudo rm -f $FILESYSTEM_ROOT/usr/bin/qemu*static || true
    DOCKERFS_PATH=../dockerfs/
fi


SONIC_FS_IMAGE_COMPRESSION_TYPE="${SONIC_FS_IMAGE_COMPRESSION_TYPE:-zip}"
if [[ "${SONIC_FS_IMAGE_COMPRESSION_TYPE}" == "pigz" ]]; then

	## Compress docker files
	pushd $FILESYSTEM_ROOT && sudo tar --use-compress-program=pigz -cf $OLDPWD/${BUILD_PATH}/$FILESYSTEM_DOCKERFS -C ${DOCKERFS_PATH}var/lib/docker .; popd

	ln -s /sonic/${BUILD_PATH}/$FILESYSTEM_SQUASHFS $FILESYSTEM_ROOT/$FILESYSTEM_SQUASHFS
	ln -s /sonic/${BUILD_PATH}/$FILESYSTEM_DOCKERFS $FILESYSTEM_ROOT/$FILESYSTEM_DOCKERFS
	pushd $FILESYSTEM_ROOT && sudo tar --use-compress-program=pigz -chf $OLDPWD/${BUILD_PATH}/$ONIE_INSTALLER_PAYLOAD boot/ $PLATFORM_DIR/ $FILESYSTEM_SQUASHFS $FILESYSTEM_DOCKERFS ; popd
else
	## Compress docker files
	pushd $FILESYSTEM_ROOT && sudo tar czf $OLDPWD/${BUILD_PATH}/$FILESYSTEM_DOCKERFS -C ${DOCKERFS_PATH}var/lib/docker .; popd
	## Compress together with /boot, /var/lib/docker and $PLATFORM_DIR as an installer payload zip file
	pushd $FILESYSTEM_ROOT && sudo zip $OLDPWD/${BUILD_PATH}/$ONIE_INSTALLER_PAYLOAD -r boot/ $PLATFORM_DIR/; popd
	pushd ${BUILD_PATH} && sudo zip -g -n .squashfs:.gz $ONIE_INSTALLER_PAYLOAD $FILESYSTEM_SQUASHFS $FILESYSTEM_DOCKERFS; popd
fi

sudo chmod -R 777 ${BUILD_PATH}

# umount dockerfs when it is done
BASE_IMAGE_NAME=${BASE_IMAGE_NAME} scripts/fsutil.sh dockerfs umount || true

## Output all the mounted device for troubleshooting
echo '[INFO] Show Mount all'
sudo LANG=C chroot $FILESYSTEM_ROOT mount proc /proc -t proc
sudo LANG=C chroot $FILESYSTEM_ROOT mount
sync; sync; sync;

#Exit trap handles the umount
#sudo LANG=C chroot $FILESYSTEM_ROOT umount /proc || true
#BASE_IMAGE_NAME=${BASE_IMAGE_NAME} scripts/fsutil.sh rootfs umount  

## ensure proc is mounted
sudo mountpoint -q /proc || sudo mount -t proc proc /proc || true
echo "Done"
