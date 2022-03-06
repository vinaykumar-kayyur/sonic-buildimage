# This script is for reproducible build.
# Reproducible build for docker enabled: Before build docker image, this script will change image:tag to image:sha256 in DOCKERFILE.
# And record image sha256 to a target file.
#!/bin/bash

IMAGENAME=$1
DOCKERFILE=$2
ARCH=$3
DOCKERFILE_TARGE=$4
DISTRO=$5

version_file=files/build/versions/default/versions-docker
new_version_file=target/versions/default/versions-docker
mkdir -p target/versions/default

. src/sonic-build-hooks/buildinfo/config/buildinfo.config

image_tag=$(grep "^FROM " $DOCKERFILE | awk '{print$2}')
hash_value=$(grep "${ARCH}:${image_tag}" $version_file 2>/dev/null | awk -F== '{print$2}')
oldimage=$image_tag
newimage=$image_tag
prefix=$SONIC_DEFAULT_CONTAINER_REGISTRY

# if it is loaded from file, exit
[ -f target/${image_tag}.gz-load.log ] && echo "loaded: $image_tag" >> $new_version_file.log && exit 0

# Debug info to logfile
echo "=================================================" >> $new_version_file.log
echo "Input: $@" >> $new_version_file.log
echo "Image: $image_tag" >> $new_version_file.log
echo "hash in config: $hash_value" >> $new_version_file.log
echo "Default ACR: $prefix" >> $new_version_file.log
echo "target/${image_tag}.gz-load.log: $(ls target/${image_tag}.gz-load.log 2>&1)" >> $new_version_file.log
echo "-------------------------------------------------" >> $new_version_file.log

if [[ ",$SONIC_VERSION_CONTROL_COMPONENTS," == *,all,* ]] || [[ ",$SONIC_VERSION_CONTROL_COMPONENTS," == *,docker,* ]]; then
    # version control On
    i=0
    for image in $prefix$image_tag@$hash_value $image_tag@$hash_value $prefix$image_tag
    do
        ((i++))
        if docker pull $image 1>/dev/null;then
            echo "$i: success! pulled image from $image" >> $new_version_file.log
            newimage=$image
            break
        else
            echo "$i: failed!  pulled image from $image" >> $new_version_file.log
        fi
    done
    echo "replace $oldimage with $newimage" >> $new_version_file.log
    sed -i "s#$oldimage#$newimage#" $DOCKERFILE
else
    # version control OFF
    i=0
    for image in $prefix$image_tag $image_tag
    do
        ((i++))
        if docker pull $image 1>/dev/null;then
            echo "$i: success! pulled image from $image" >> $new_version_file.log
            echo -e "${ARCH}:${image_tag}==$(docker pull $image | grep Digest | awk '{print$2}')" >> $new_version_file
            sort -u $new_version_file -o $new_version_file
            break
        else
            echo "$i: failed!  pulled image from $image" >> $new_version_file.log
        fi
    done
fi
