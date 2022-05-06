#!/bin/bash

[[ ! -z "${DBGOPT}" && $0 =~ ${DBGOPT} ]] && set -x 

DOCKER_IMAGE=$1
TARGET_PATH=$2
DOCKER_IMAGE_TAG=$3
DOCKER_PATH=$4
DOCKER_FILE=$5

. scripts/utils.sh 

[ -z "$TARGET_PATH" ] && TARGET_PATH=./target

DOCKER_IMAGE_NAME=$(echo $DOCKER_IMAGE | cut -d: -f1)
DOCKER_CONTAINER=$DOCKER_IMAGE_NAME
TARGET_VERSIONS_PATH=$TARGET_PATH/versions/dockers/$DOCKER_IMAGE_NAME
BUILD_LOG_PATH=target/versions/log/$DOCKER_IMAGE_NAME
mkdir -p ${BUILD_LOG_PATH}

[ -d $TARGET_VERSIONS_PATH ] && rm -rf $TARGET_VERSIONS_PATH
mkdir -p $TARGET_VERSIONS_PATH

export DOCKER_CLI_EXPERIMENTAL=enabled

# Remove the old docker container if existing
if docker container inspect $DOCKER_IMAGE > /dev/null 2>&1; then
    docker container rm $DOCKER_IMAGE > /dev/null
fi
docker create --name $DOCKER_CONTAINER --entrypoint /bin/bash $DOCKER_IMAGE_TAG
docker cp -L $DOCKER_CONTAINER:/etc/os-release $TARGET_VERSIONS_PATH/
docker cp -L $DOCKER_CONTAINER:/usr/local/share/buildinfo/pre-versions $TARGET_VERSIONS_PATH/
docker cp -L $DOCKER_CONTAINER:/usr/local/share/buildinfo/post-versions $TARGET_VERSIONS_PATH/
docker cp -L $DOCKER_CONTAINER:/usr/local/share/buildinfo/log ${BUILD_LOG_PATH}/




# Version package cache
IMAGE_DBGS_NAME=${DOCKER_IMAGE_NAME//-/_}_image_dbgs
if [[ ${DOCKER_IMAGE_NAME} == sonic-slave-* ]]; then
	GLOBAL_CACHE_DIR=${SONIC_VERSION_CACHE_SOURCE}/${DOCKER_IMAGE_NAME}
else
	GLOBAL_CACHE_DIR=/vcache/${DOCKER_IMAGE_NAME}
fi
LOCAL_CACHE_FILE=target/vcache/${DOCKER_IMAGE_NAME}/cache.tgz

if [ ! -z ${SONIC_VERSION_CACHE} ]; then

	cat ${DOCKER_PATH}/vcache/cache.base64| base64 -d  >${LOCAL_CACHE_FILE}
	rm -f ${DOCKER_PATH}/vcache/cache.base64

	VERSION_FILES="${DOCKER_PATH}/buildinfo/versions/versions-*"
	#DEP_FILES="${DOCKER_FILE}.j2"
	if [[ ${DOCKER_IMAGE_NAME} =~ '-dbg' ]]; then
		DEP_FILES="${DOCKER_PATH}/Dockerfile-dbg.j2"
	else
		DEP_FILES="${DOCKER_PATH}/Dockerfile.j2"
	fi
	VERSION_SHA="$( (echo -n "${!IMAGE_DBGS_NAME}"; cat ${DEP_FILES} ${VERSION_FILES}) | sha1sum | awk '{print substr($1,0,23);}')"
    GLOBAL_CACHE_FILE=${GLOBAL_CACHE_DIR}/${DOCKER_IMAGE_NAME}-${VERSION_SHA}.tgz

	GIT_FILE_STATUS=$(git status -s ${DEP_FILES})

	if [ -f ${LOCAL_CACHE_FILE} ]; then
		if [[ -z ${GIT_FILE_STATUS} && ! -e ${GLOBAL_CACHE_FILE} ]]; then
			mkdir -p ${GLOBAL_CACHE_DIR}
			chmod -f 777 ${GLOBAL_CACHE_DIR}
			FLOCK ${GLOBAL_CACHE_FILE}
			cp ${LOCAL_CACHE_FILE} ${GLOBAL_CACHE_FILE} 
			chmod -f 777 ${LOCAL_CACHE_FILE} ${GLOBAL_CACHE_FILE} 
			FUNLOCK ${GLOBAL_CACHE_FILE}
		fi
	fi
fi


# Docker hub pull cache
VERSION_FILE="${BUILDINFO_PATH}/versions/versions-docker"
BUILD_DOCKER_VERSION_FILE="target/versions/default/versions-docker"
PULL_DOCKER=$(awk '/^[[:space:]]*FROM /{print $2}' ${DOCKER_FILE} ) 
VERSION=$(docker inspect -f '{{index .RepoDigests 0}}' ${PULL_DOCKER} 2>/dev/null | awk -F"@" '{print $NF}' )

if [ ! -z ${SONIC_VERSION_CACHE} ]; then
	if [ ! -z ${PULL_DOCKER} ];then

		GLOBAL_DOCKER_CACHE_FILE=${GLOBAL_CACHE_DIR}/${PULL_DOCKER//:/-}-${VERSION//:/-}.tgz
		if [ ! -f ${GLOBAL_DOCKER_CACHE_FILE} ]; then
			mkdir -p ${GLOBAL_CACHE_DIR}
			chmod -f 777 ${GLOBAL_CACHE_DIR}
			FLOCK ${GLOBAL_DOCKER_CACHE_FILE}
			docker save ${PULL_DOCKER} | gzip -c > ${GLOBAL_DOCKER_CACHE_FILE}
			chmod -f 777 ${GLOBAL_DOCKER_CACHE_FILE} 
			FUNLOCK ${GLOBAL_DOCKER_CACHE_FILE}
		fi

	fi
fi

# Update the docker version file
if [ ! -f ${BUILD_DOCKER_VERSION_FILE} ] ; then 
	mkdir -p $(dirname ${BUILD_DOCKER_VERSION_FILE})
	touch ${BUILD_DOCKER_VERSION_FILE}
fi
BUILD_VERSION=$(grep "^${PULL_DOCKER}==${VERSION}" ${BUILD_DOCKER_VERSION_FILE} | awk -F"==" '{print $NF}')
if [[ -z ${BUILD_VERSION} && ${VERSION} == sha256:* ]]; then
	echo "${PULL_DOCKER}==${VERSION}" >> ${BUILD_DOCKER_VERSION_FILE}
	sort ${BUILD_DOCKER_VERSION_FILE} -o ${BUILD_DOCKER_VERSION_FILE} -u &> /dev/null
fi


docker container rm $DOCKER_CONTAINER
