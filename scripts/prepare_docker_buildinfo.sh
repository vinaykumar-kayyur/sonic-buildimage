#!/bin/bash

IMAGENAME=$1
DOCKERFILE=$2
ARCH=$3
DOCKERFILE_TARGE=$4
DISTRO=$5

[ -z "$BUILD_SLAVE" ] && BUILD_SLAVE=n
[ -z "$DOCKERFILE_TARGE" ] && DOCKERFILE_TARGE=$DOCKERFILE
DOCKERFILE_PATH=$(dirname "$DOCKERFILE_TARGE")
BUILDINFO_PATH="${DOCKERFILE_PATH}/buildinfo"
BUILDINFO_VERSION_PATH="${BUILDINFO_PATH}/versions"

[ -d $BUILDINFO_PATH ] && rm -rf $BUILDINFO_PATH
mkdir -p $BUILDINFO_VERSION_PATH

# Get the debian distribution from the docker base image
if [ -z "$DISTRO" ]; then
    DOCKER_BASE_IMAGE=$(grep "^FROM" $DOCKERFILE | head -n 1 | awk '{print $2}')
    DISTRO=$(docker run --rm --entrypoint "" $DOCKER_BASE_IMAGE cat /etc/os-release | grep VERSION_CODENAME | cut -d= -f2)
    [ -z "$DISTRO" ] && DISTRO=jessie
fi

version_control(){
    version_file=files/build/versions/default/versions-docker
    new_version_file=target/versions/build/versions-docker

    dir=`dirname $new_version_file`
    mkdir -p $dir
    touch $new_version_file

    image_tag=`grep "^FROM " $DOCKERFILE | awk '{print$2}'`
    image=`echo $image_tag | cut -f1 -d:`
    tag=`echo $image_tag | cut -f2 -d:`
    # if docker image load from local build, return.
    if [ -f target/${image_tag}.gz ]; then
        return 0
    fi
    # if docker image load from local cache, return.
    docker inspect --type image image_tag &> /dev/null && return 0
    if [[ ",$SONIC_VERSION_CONTROL_COMPONENTS," == *,all,* ]] || [[ ",$SONIC_VERSION_CONTROL_COMPONENTS," == *,docker,* ]]; then
        if [ ! -f $version_file ];then
            echo "Failed to access $version_file"
            exit 1
        fi
        hash_value=`grep "${ARCH}:${image_tag}" $version_file | awk -F== '{print$2}'`
        if [ -z $hash_value ];then
            echo "Failed to verify the docker image: ${ARCH}:${image_tag}, the hash value is not specified"
            exit 1
        fi
        oldstr=${image//\//\\/}
        newstr="${oldstr}@$hash_value"
        sed -i "s/$oldstr/$newstr/" $DOCKERFILE
        echo -e "\n${ARCH}:${image_tag}==$hash_value" >> $new_version_file
    else
        hash_value_latest=`docker pull $image_tag | grep Digest | awk '{print$2}'`
        echo -e "\n${ARCH}:${image_tag}==$hash_value_latest" >> $new_version_file
    fi
}
version_control

DOCKERFILE_PRE_SCRIPT='# Auto-Generated for buildinfo
COPY ["buildinfo", "/usr/local/share/buildinfo"]
RUN dpkg -i /usr/local/share/buildinfo/sonic-build-hooks_1.0_all.deb
RUN pre_run_buildinfo'

# Add the auto-generate code if it is not added in the target Dockerfile
if [ ! -f $DOCKERFILE_TARGE ] || ! grep -q "Auto-Generated for buildinfo" $DOCKERFILE_TARGE; then
    # Insert the docker build script before the RUN command
    LINE_NUMBER=$(grep -Fn -m 1 'RUN' $DOCKERFILE | cut -d: -f1)
    TEMP_FILE=$(mktemp)
    awk -v text="${DOCKERFILE_PRE_SCRIPT}" -v linenumber=$LINE_NUMBER 'NR==linenumber{print text}1' $DOCKERFILE > $TEMP_FILE

    # Append the docker build script at the end of the docker file
    echo -e "\nRUN post_run_buildinfo" >> $TEMP_FILE

    cat $TEMP_FILE > $DOCKERFILE_TARGE
    rm -f $TEMP_FILE
fi

# Copy the build info config
cp -rf src/sonic-build-hooks/buildinfo/* $BUILDINFO_PATH

# Generate the version lock files
scripts/versions_manager.py generate -t "$BUILDINFO_VERSION_PATH" -n "$IMAGENAME" -d "$DISTRO" -a "$ARCH"

touch $BUILDINFO_VERSION_PATH/versions-deb
