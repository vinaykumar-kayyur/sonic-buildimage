#!/bin/bash
## This script is to create the tmpfs for different mount point during 
## the ONIE installer image generation to speed up the processing.
##
## USAGE:
##   ./tmpfs <storage> <operation>
## ENVIRONMENT:
##   storage  => Can be imagefs, rootfs, overlayfs, dockerfs, installerfs or allfs
##   type     => It can be one of the operation: allocate, deallocate, create, delete, mount or umount

## Include common functions
. functions.sh

## Enable debug output for script
set -x 


## Use tmpfs
if [[ "${SONIC_USE_TMPFS_BUILD}" == "y" ]]; then
	BUILD_TMP_ROOTFS_SIZE=6G
	BUILD_ROOTFS_FILE_SIZE=4 #4G
	BUILD_TMP_DOCKERFS_SIZE=16G
	BUILD_TMP_FS_SIZE=8G
else
	BUILD_ROOTFS_FILE_SIZE=10 #10G
fi

## Read ONIE image related config file
. ./onie-image.conf

## Working directory to prepare the file system
FILESYSTEM_BASE=/sonic/build/${BASE_IMAGE_NAME}
FILESYSTEM_ROOT=${FILESYSTEM_BASE}/
mkdir -p ${FILESYSTEM_ROOT}


FSROOT_IMAGE_BASE_DIR=target/image/
FSROOT_IMAGE_DIR=${FSROOT_IMAGE_BASE_DIR}/${BASE_IMAGE_NAME}
mkdir -p ${FSROOT_IMAGE_DIR}
FSROOT_IMAGE_FILENAME=fsroot.img
FSROOT_IMAGE_FILE=${FSROOT_IMAGE_DIR}/${FSROOT_IMAGE_FILENAME}
BUILD_PATH=target/fs/${TARGET_MACHINE}


mount_imagefs()
{
	umount_allfs
	delete_rootfs_image
    if [[  -e ${FSROOT_IMAGE_FILE} ]]; then
        return 
    fi

    if [[ "${SONIC_USE_TMPFS_BUILD}" == "y" ]] ; then
        sudo mount -t tmpfs -o size=${BUILD_TMP_ROOTFS_SIZE} tmpfs ${FSROOT_IMAGE_DIR}
    fi
}

create_rootfs_image()
{
    # Create special tmpfs mount point for fsroot
    if [[ ! -e ${FSROOT_IMAGE_FILE} ]]; then
        dd if=/dev/zero of=${FSROOT_IMAGE_FILE} bs=1G  count=${BUILD_ROOTFS_FILE_SIZE} 
        mkfs.ext4 -F ${FSROOT_IMAGE_FILE}
    fi
}
delete_rootfs_image()
{
    sudo rm -f ${FSROOT_IMAGE_FILE} || true

}

umount_imagefs()
{
    if [[  "${SONIC_USE_TMPFS_BUILD}" != "y" ]] ; then
        return
    fi
    if $(mountpoint -q ${FSROOT_IMAGE_DIR}); then
        # save the log file
        cp ${FSROOT_IMAGE_FILE}.log ${FSROOT_IMAGE_BASE_DIR}/${BASE_IMAGE_NAME}-${FSROOT_IMAGE_FILENAME}.log
        sudo umount ${FSROOT_IMAGE_DIR}  || true
    fi

}
imagefs_fun()
{
    case $2 in
        mount)
            mount_imagefs
            ;;
        umount)
            umount_imagefs
            ;;
        create)
            create_rootfs_image
            ;;
        delete)
            delete_rootfs_image
            ;;
        *)
            echo "Usage: $0 $1 {create|delete|mount|umount}"
            exit 1
            ;;
    esac
}





mount_rootfs()
{
    mkdir -p ${FILESYSTEM_BASE}

    sudo mount -o rw,loop ${FSROOT_IMAGE_FILE} ${FILESYSTEM_BASE}  || true
    sudo chmod 777 ${FILESYSTEM_BASE}
}


umount_rootfs()
{
    if $( mountpoint -q ${FILESYSTEM_BASE} ) ;then
        sudo umount -f ${FILESYSTEM_BASE}  || true
    fi
}


rootfs_fun()
{
    case $2 in
        mount)
            mount_rootfs
            ;;
        umount)
            umount_rootfs
            ;;
        *)
            echo "Usage: $0 $1 {mount|umount}"
            exit 1
            ;;
    esac
}

mount_overlayfs()
{
    mkdir -p ${FILESYSTEM_BASE}/${FSROOT_IMAGE_FILENAME} 
	cp ${FSROOT_IMAGE_FILE}  ${FSROOT_IMAGE_FILENAME}
    sudo mount -o rw,loop ${FSROOT_IMAGE_FILENAME} ${FILESYSTEM_BASE}/${FSROOT_IMAGE_FILENAME}  || true
    #sudo mount -o rw,loop ${FSROOT_IMAGE_FILENAME} ${FILESYSTEM_BASE}/${FSROOT_IMAGE_FILENAME}  || true
	#sudo mkdir -p ${FILESYSTEM_BASE}/fsroot ${FILESYSTEM_BASE}/upper ${FILESYSTEM_BASE}/work
    #sudo chmod 777 ${FILESYSTEM_BASE}
	#sudo mount -t overlay overlay -o lowerdir=${FILESYSTEM_BASE}/${FSROOT_IMAGE_FILENAME},upperdir=${FILESYSTEM_BASE}/upper,workdir=${FILESYSTEM_BASE}/work ${FILESYSTEM_BASE}/fsroot
}


umount_overlayfs()
{
	if $( mountpoint -q ${FILESYSTEM_BASE}/${FSROOT_IMAGE_FILENAME} ) ;then
        sudo umount -f ${FILESYSTEM_BASE}/${FSROOT_IMAGE_FILENAME}  || true
    fi
    if $( mountpoint -q ${FILESYSTEM_BASE} ) ;then
        sudo umount -f ${FILESYSTEM_BASE}  || true
    fi
}


overlayfs_fun()
{
    case $2 in
        mount)
            mount_overlayfs
            ;;
        umount)
            umount_overlayfs
            ;;
        *)
            echo "Usage: $0 $1 {mount|umount}"
            exit 1
            ;;
    esac
}


DOCKER_BASE_PATH=${FILESYSTEM_ROOT}/var/lib/docker
mount_dockerfs()
{
    sudo mkdir -p ${DOCKER_BASE_PATH}
    if [[ "${SONIC_USE_TMPFS_BUILD}" == "y" ]] ; then
        sudo mount -t tmpfs -o size=${BUILD_TMP_DOCKERFS_SIZE} tmpfs ${DOCKER_BASE_PATH}
    fi
}
umount_dockerfs()
{
    if [[  "${SONIC_USE_TMPFS_BUILD}" != "y" ]] ; then
        return
    fi
    if $( mountpoint -q ${DOCKER_BASE_PATH} );then
        sudo umount -f ${DOCKER_BASE_PATH}  || true
    fi
}

dockerfs_fun()
{
    case $2 in
        mount)
            mount_dockerfs
            ;;
        umount)
            umount_dockerfs
            ;;
        *)
            echo "Usage: $0 $1 {mount|umount}"
            exit 1
            ;;
    esac
}




mount_installerfs()
{
    sudo mkdir -p ${BUILD_PATH}
    if [[ "${SONIC_USE_TMPFS_BUILD}" == "y" ]] ; then
        sudo mount -t tmpfs -o size=${BUILD_TMP_FS_SIZE} tmpfs ${BUILD_PATH}
    fi
}
umount_installerfs()
{
    if [[  "${SONIC_USE_TMPFS_BUILD}" != "y" ]] ; then
        return
    fi
    if $( mountpoint -q ${BUILD_PATH} ); then
        sudo umount ${BUILD_PATH}  || true
    fi
}

installerfs_fun()
{
    case $2 in
        mount)
            mount_installerfs
            ;;
        umount)
            umount_installerfs
            ;;
        *)
            echo "Usage: $0 $1 {mount|umount}"
            exit 1
            ;;
    esac
}




mount_allfs()
{
    mount_imagefs
    create_rootfs_image
    mount_rootfs
    mount_dockerfs
    mount_installerfs
}

umount_allfs()
{

    umount_dockerfs
    umount_rootfs
	#umount_overlayfs
    umount_imagefs
    umount_installerfs
}

allfs_fun()
{
    case $2 in
        mount)
            mount_allfs
            ;;
        umount)
            umount_allfs
            ;;
        *)
            echo "Usage: $0 $1 {mount|umount}"
            exit 1
            ;;
    esac
}


case "$1" in
    imagefs)
        imagefs_fun $1 $2
        ;;
    rootfs)
        rootfs_fun $1 $2
        ;;
    overlayfs)
        overlayfs_fun $1 $2
        ;;
    dockerfs)
        dockerfs_fun $1 $2
        ;;
    installerfs)
        installerfs_fun $1 $2
        ;;
    allfs)
        allfs_fun $1 $2
        ;;
    *)
        echo "Usage: $0 {imagefs|rootfs|overlayfs|dockerfs|installerfs|allfs} <operation type>"
        exit 1
        ;;
esac





