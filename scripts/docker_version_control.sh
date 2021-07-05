#!/bin/bash

IMAGENAME=$1
DOCKERFILE=$2
ARCH=$3
DOCKERFILE_TARGE=$4
DISTRO=$5

version_file=files/build/versions/default/versions-docker
new_version_file=target/versions/default/versions-docker
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
    fi
    if [ -z $hash_value ];then
        hash_value=unknown
    fi
    oldimage=${image_tag//\//\\/}
    newimage="${oldstr}@$hash_value"
    sed -i "s/$oldimage/$newimage/" $DOCKERFILE
else
    hash_value=`docker pull $image_tag | grep Digest | awk '{print$2}'`
fi
if [[ "$hash_value" != "unknown" ]];then
    echo -e "${ARCH}:${image_tag}==$hash_value" >> $new_version_file
fi
