#!/bin/bash

[[ ! -z "${DBGOPT}" && $0 =~ ${DBGOPT} ]] && set -x 

set -x

ARCH=$1
DISTRO=$2
FILESYSTEM_ROOT=$3
HOST_IMAGE_NAME=host-image
IMAGENAME=${HOST_IMAGE_NAME}

. /usr/local/share/buildinfo/scripts/buildinfo_base.sh
VERSION_DEB_PREFERENCE="01-versions-deb"
BUILDINFO_PATH=${FILESYSTEM_ROOT}/usr/local/share/buildinfo
BUILDINFO_VERSION_PATH=${FILESYSTEM_ROOT}/usr/local/share/buildinfo/versions
BUILDINFO_VERSION_DEB=${BUILDINFO_VERSION_PATH}/${VERSION_DEB_PREFERENCE}
OVERRIDE_VERSION_PATH=files/build/versions/host-image
DIFF_VERSIONS_PATH=$BUILDINFO_PATH/diff-versions

mkdir -p $BUILDINFO_PATH

# Copy the build info config
cp -rf src/sonic-build-hooks/buildinfo/* $BUILDINFO_PATH/

# Generate version lock files
scripts/versions_manager.py generate -t "$BUILDINFO_VERSION_PATH" -m "$OVERRIDE_VERSION_PATH" -d "$DISTRO" -a "$ARCH"

if [ "$ENABLE_VERSION_CONTROL_DEB" == "y" ]; then
    cp -f $BUILDINFO_VERSION_DEB ${FILESYSTEM_ROOT}/etc/apt/preferences.d/
fi

sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "dpkg -i /usr/local/share/buildinfo/sonic-build-hooks_1.0_all.deb"
sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "pre_run_buildinfo"
sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo DISTRO=${DISTRO} >> /usr/local/share/buildinfo/config/buildinfo.config"
sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo IMAGENAME=${IMAGENAME} >> /usr/local/share/buildinfo/config/buildinfo.config"


# Version cache 
HOST_IMAGE_PATH=files/build/versions/${HOST_IMAGE_NAME}
GLOBAL_CACHE_DIR=/vcache/${HOST_IMAGE_NAME}
APT_CACHE_PATH=${FILESYSTEM_ROOT}/var/cache/apt/archives
BIN_CACHE_PATH=${FILESYSTEM_ROOT}/sonic/target/vcache/${HOST_IMAGE_NAME}
mkdir -p ${BIN_CACHE_PATH}/deb ${APT_CACHE_PATH}

if [ ! -z ${SONIC_VERSION_CACHE} ]; then

	# Skip the deletion of cache files
	cat <<-EOF >${FILESYSTEM_ROOT}/etc/apt/apt.conf.d/dpkg-cache
	DPkg::Post-Invoke { "test -f /usr/bin/rsync && rsync -avzh --ignore-errors /var/cache/apt/archives/ /sonic/target/vcache/${HOST_IMAGE_NAME}/deb/; rm -f /var/cache/apt/archives/partial/*.deb /var/cache/apt/*.bin || true"; };
	APT::Update::Post-Invoke { "test -f /usr/bin/rsync && rsync -avzh --ignore-errors /var/cache/apt/archives/ /sonic/target/vcache/${HOST_IMAGE_NAME}/deb/; rm -f /var/cache/apt/archives/partial/*.deb /var/cache/apt/*.bin || true"; };
	APT::Keep-Downloaded-Packages "true";
	EOF

	VERSION_FILES="${HOST_IMAGE_PATH}/versions-*-${DISTRO}-${ARCH} ${HOST_IMAGE_PATH}/versions-web"
	DEP_FILES="build_debian.sh files/build_templates/sonic_debian_extension.j2"
	VERSION_SHA="$( cat ${DEP_FILES} ${VERSION_FILES} | sha1sum | awk '{print substr($1,0,23);}')"

	GLOBAL_CACHE_FILE=${GLOBAL_CACHE_DIR}/${HOST_IMAGE_NAME}-${VERSION_SHA}.tgz
	LOCAL_CACHE_DIR=target/vcache/${HOST_IMAGE_NAME}
	LOCAL_CACHE_FILE=${LOCAL_CACHE_DIR}/cache.tgz
	GIT_FILE_STATUS=$(git status -s ${DEP_FILES})

	if [[ ! -f ${LOCAL_CACHE_FILE} ]]; then
		mkdir -p ${LOCAL_CACHE_DIR}
		chmod -f 777 ${LOCAL_CACHE_DIR}
		tar -zcf ${LOCAL_CACHE_FILE} -T /dev/null
		chmod -f 777 ${LOCAL_CACHE_FILE}
	fi

	if [[ -z ${GIT_FILE_STATUS} &&  -e ${GLOBAL_CACHE_FILE} ]]; then
		cp ${GLOBAL_CACHE_FILE} ${LOCAL_CACHE_FILE}
		touch ${GLOBAL_CACHE_FILE}
	fi
	cp ${LOCAL_CACHE_FILE} ${BIN_CACHE_PATH}

	# disable the validity check
	# cp files/apt/apt.conf.d/no-check-valid-until  /etc/apt/apt.conf.d


fi

sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "pre_run_buildinfo ${HOST_IMAGE_NAME}"
sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "apt-get update && apt-get -y install rsync "
