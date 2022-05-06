#!/bin/bash

[[ ! -z "${DBGOPT}" && $0 =~ ${DBGOPT} ]] && set -x 

IMAGENAME=$1
DOCKERFILE=$2
ARCH=$3
DOCKERFILE_TARGET=$4
DISTRO=$5

. scripts/utils.sh 

[ -z "$BUILD_SLAVE" ] && BUILD_SLAVE=n
[ -z "$DOCKERFILE_TARGET" ] && DOCKERFILE_TARGET=$DOCKERFILE
DOCKERFILE_PATH=$(dirname "$DOCKERFILE_TARGET")
BUILDINFO_PATH="${DOCKERFILE_PATH}/buildinfo"
BUILDINFO_VERSION_PATH="${BUILDINFO_PATH}/versions"
DOCKER_PATH=$(dirname $DOCKERFILE)

[ -d $BUILDINFO_PATH ] && rm -rf $BUILDINFO_PATH
mkdir -p $BUILDINFO_VERSION_PATH

# Get the debian distribution from the docker base image
if [ -z "$DISTRO" ]; then
    DOCKER_BASE_IMAGE=$(grep "^FROM" $DOCKERFILE | head -n 1 | awk '{print $2}')
    DISTRO=$(docker run --rm --entrypoint "" $DOCKER_BASE_IMAGE cat /etc/os-release | grep VERSION_CODENAME | cut -d= -f2)
    [ -z "$DISTRO" ] && DISTRO=jessie
fi

# add script for reproducible build. using sha256 instead of tag for docker base image.
scripts/docker_version_control.sh $@

if [ ! -z ${SONIC_VERSION_CACHE} ]; then
	export PIP_CACHE_DIR=/sonic/target/vcache/${IMAGENAME}/pip
fi

DOCKERFILE_PRE_SCRIPT='# Auto-Generated for buildinfo
ARG SONIC_VERSION_CACHE
COPY ["buildinfo", "/usr/local/share/buildinfo"]
COPY vcache/ /sonic/target/vcache/'${IMAGENAME}'
RUN dpkg -i /usr/local/share/buildinfo/sonic-build-hooks_1.0_all.deb
ENV IMAGENAME='${IMAGENAME}'
ENV DISTRO='${DISTRO}'
ENV PIP_CACHE_DIR='${PIP_CACHE_DIR}'
RUN pre_run_buildinfo '${IMAGENAME}'
RUN apt-get update && apt-get install -y rsync
'

# Add the auto-generate code if it is not added in the target Dockerfile
if [ ! -f $DOCKERFILE_TARGET ] || ! grep -q "Auto-Generated for buildinfo" $DOCKERFILE_TARGET; then
    # Insert the docker build script before the RUN command
    LINE_NUMBER=$(grep -Fn -m 1 'RUN' $DOCKERFILE | cut -d: -f1)
    TEMP_FILE=$(mktemp)
    awk -v text="${DOCKERFILE_PRE_SCRIPT}" -v linenumber=$LINE_NUMBER 'NR==linenumber{print text}1' $DOCKERFILE > $TEMP_FILE

    # Append the docker build script at the end of the docker file
    echo -e "\nRUN post_run_buildinfo ${IMAGENAME} " >> $TEMP_FILE

    cat $TEMP_FILE > $DOCKERFILE_TARGET
    rm -f $TEMP_FILE
fi

# Copy the build info config
mkdir -p ${BUILDINFO_PATH}
cp -rf src/sonic-build-hooks/buildinfo/* $BUILDINFO_PATH

# Generate the version lock files
scripts/versions_manager.py generate -t "$BUILDINFO_VERSION_PATH" -n "$IMAGENAME" -d "$DISTRO" -a "$ARCH"

touch $BUILDINFO_VERSION_PATH/versions-deb


# Version cache 
DOCKER_IMAGE_NAME=${IMAGENAME}
IMAGE_DBGS_NAME=${DOCKER_IMAGE_NAME//-/_}_image_dbgs

if [[ ${DOCKER_IMAGE_NAME} == sonic-slave-* ]]; then
	GLOBAL_CACHE_DIR=${SONIC_VERSION_CACHE_SOURCE}/${DOCKER_IMAGE_NAME}
else
	GLOBAL_CACHE_DIR=/vcache/${DOCKER_IMAGE_NAME}
fi

LOCAL_CACHE_DIR=target/vcache/${DOCKER_IMAGE_NAME}
mkdir -p ${LOCAL_CACHE_DIR} ${DOCKER_PATH}/vcache
chmod -f 777 ${LOCAL_CACHE_DIR} ${DOCKER_PATH}/vcache

if [ ! -z ${SONIC_VERSION_CACHE} ]; then

	VERSION_FILES="${DOCKER_PATH}/buildinfo/versions/versions-*"
	#DEP_FILES="${DOCKERFILE}.j2"
	if [[ ${DOCKER_IMAGE_NAME} =~ '-dbg' ]]; then
		DEP_FILES="${DOCKER_PATH}/Dockerfile-dbg.j2"
	else
		DEP_FILES="${DOCKER_PATH}/Dockerfile.j2"
	fi
	VERSION_SHA="$( (echo -n "${!IMAGE_DBGS_NAME}"; cat ${DEP_FILES} ${VERSION_FILES}) | sha1sum | awk '{print substr($1,0,23);}')"

	GLOBAL_CACHE_FILE=${GLOBAL_CACHE_DIR}/${DOCKER_IMAGE_NAME}-${VERSION_SHA}.tgz
	LOCAL_CACHE_FILE=${LOCAL_CACHE_DIR}/cache.tgz
	GIT_FILE_STATUS=$(git status -s ${DEP_FILES})

	if [[ ! -f ${LOCAL_CACHE_FILE} ]]; then
		tar -zcf ${LOCAL_CACHE_FILE} -T /dev/null
		chmod -f 777 ${LOCAL_CACHE_FILE}
	fi

	if [[ -z ${GIT_FILE_STATUS} &&  -e ${GLOBAL_CACHE_FILE} ]]; then
		cp ${GLOBAL_CACHE_FILE} ${LOCAL_CACHE_FILE}
		touch ${GLOBAL_CACHE_FILE}
	fi

	ln -f ${LOCAL_CACHE_FILE} ${DOCKER_PATH}/vcache/


else
	# Delete the cache file if version cache is disabled.
	rm -f ${DOCKER_PATH}/vcache/cache.tgz
fi

# Docker hub pull cache
VERSION_FILE="${BUILDINFO_PATH}/versions/versions-docker"
PULL_DOCKER=$(awk '/^[[:space:]]*FROM /{print $2}' ${DOCKERFILE} ) 

if [ -f ${VERSION_FILE} ]; then

	VERSION=$(grep "^${PULL_DOCKER}=" ${VERSION_FILE} | awk -F"==" '{print $NF}')
	GLOBAL_DOCKER_CACHE_FILE=${GLOBAL_CACHE_DIR}/${PULL_DOCKER//:/-}-${VERSION//:/-}.tgz
	if [[ ! -z ${VERSION} && ! -z ${PULL_DOCKER} && ( ${SONIC_VERSION_CONTROL_COMPONENTS} == "docker" || ${SONIC_VERSION_CONTROL_COMPONENTS} == "all" ) ]]; then

		if [ -f ${GLOBAL_DOCKER_CACHE_FILE} ]; then
			docker load < ${GLOBAL_DOCKER_CACHE_FILE}
		else
			docker pull ${PULL_DOCKER}@${VERSION}
		fi
	fi

fi



