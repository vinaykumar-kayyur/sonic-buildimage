#!/bin/bash

[[ ! -z "${DBGOPT}" && $0 =~ ${DBGOPT} ]] && set -x 

ARCH=$1
DISTRO=$2
TARGET=$3
FILESYSTEM_ROOT=$4
VERSIONS_PATH=$TARGET/versions/host-image
IMAGENAME="host-image"

. scripts/utils.sh 

[ -d $VERSIONS_PATH ] && sudo rm -rf $VERSIONS_PATH
mkdir -p $VERSIONS_PATH

sudo LANG=C chroot $FILESYSTEM_ROOT post_run_buildinfo ${IMAGENAME}

cp -r $FILESYSTEM_ROOT/usr/local/share/buildinfo/pre-versions $VERSIONS_PATH/
cp -r $FILESYSTEM_ROOT/usr/local/share/buildinfo/post-versions $VERSIONS_PATH/


# Version cache 
HOST_IMAGE_NAME=host-image
HOST_IMAGE_PATH=${VERSIONS_PATH}
GLOBAL_CACHE_DIR=/vcache/${HOST_IMAGE_NAME}
HOST_IMAGE_SRC_PATH=files/build/versions/${HOST_IMAGE_NAME}

if [ ! -z ${SONIC_VERSION_CACHE} ]; then
 
	#cat ${FILESYSTEM_ROOT}/etc/apt/apt.conf.d/dpkg-cache
	sudo rm -f ${FILESYSTEM_ROOT}/etc/apt/apt.conf.d/dpkg-cache
	sudo rm -rf ${FILESYSTEM_ROOT}/sonic


	if [[ ! -f ${HOST_IMAGE_PATH}/post-versions/versions-web ]]; then
		cp ${HOST_IMAGE_SRC_PATH}/versions-web ${HOST_IMAGE_PATH}/post-versions/versions-web
	fi

	VERSION_FILES="${HOST_IMAGE_PATH}/post-versions/versions-*-${DISTRO}-${ARCH} ${HOST_IMAGE_PATH}/post-versions/versions-web"
	DEP_FILES="build_debian.sh files/build_templates/sonic_debian_extension.j2"
	VERSION_SHA="$( cat ${DEP_FILES} ${VERSION_FILES} | sha1sum | awk '{print substr($1,0,23);}')"

	GLOBAL_CACHE_FILE=${GLOBAL_CACHE_DIR}/${HOST_IMAGE_NAME}-${VERSION_SHA}.tgz
	LOCAL_CACHE_DIR=target/vcache/${HOST_IMAGE_NAME}
	LOCAL_CACHE_FILE=${LOCAL_CACHE_DIR}/cache.tgz
	GIT_FILE_STATUS=$(git status -s ${DEP_FILES})

	mkdir -p ${LOCAL_CACHE_DIR} ${GLOBAL_CACHE_DIR}
	sudo chmod -f 777 ${LOCAL_CACHE_DIR} ${GLOBAL_CACHE_DIR}
	BIN_CACHE_PATH=${FILESYSTEM_ROOT}/sonic/target/vcache/${HOST_IMAGE_NAME}
	#sudo mkdir -p ${BIN_CACHE_PATH}
	#sudo tar -C ${BIN_CACHE_PATH} -cf ${LOCAL_CACHE_FILE} .

	# Save it into version cache
	if [[ -z ${GIT_FILE_STATUS} && ! -f ${GLOBAL_CACHE_FILE} ]]; then
		
		FLOCK ${GLOBAL_CACHE_FILE}
		cp ${LOCAL_CACHE_FILE} ${GLOBAL_CACHE_FILE}
		sudo chmod -f 777 ${GLOBAL_CACHE_FILE}
		FUNLOCK ${GLOBAL_CACHE_FILE}
	fi

fi


