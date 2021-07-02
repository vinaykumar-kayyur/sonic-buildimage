#!/bin/bash

IMAGENAME=$1
DOCKERFILE=$2
ARCH=$3
DOCKERFILE_TARGE=$4
DISTRO=$5

version_file=files/build/versions/default/versions-docker
new_version_file=target/versions/build/versions-docker
mkdir -p $new_version_file

. src/sonic-build-hooks/buildinfo/config/buildinfo.config

image_tag=`grep "^FROM " $DOCKERFILE | awk '{print$2}'`
image=`echo $image_tag | cut -f1 -d:`
tag=`echo $image_tag | cut -f2 -d:`

# if docker image not in white list, exit
if [[ "$IMAGENAME" != sonic-slave-* ]] && [[ "$IMAGENAME" != docker-base* ]];then
    exit 0
fi

if [[ ",$SONIC_VERSION_CONTROL_COMPONENTS," == *,all,* ]] || [[ ",$SONIC_VERSION_CONTROL_COMPONENTS," == *,docker,* ]]; then
    if [ -f $version_file ];then
        hash_value=`grep "${ARCH}:${image_tag}" $version_file | awk -F== '{print$2}'`
    else
        hash_value=
    fi
    oldstr=${image_tag//\//\\/}
    newstr="${oldstr}@$hash_value"
    if [ -z $hash_value ];then
        newstr=unknown
    fi
    sed -i "s/$oldstr/$newstr/" $DOCKERFILE
    echo -e "\n${ARCH}:${image_tag}==$hash_value" >> $new_version_file
else
    hash_value_latest=`docker pull $image_tag | grep Digest | awk '{print$2}'`
    echo -e "\n${ARCH}:${image_tag}==$hash_value_latest" >> $new_version_file
fi
