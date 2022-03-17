# This script is for reproducible build.
# Reproducible build for docker enabled: Before build docker image, this script will change image:tag to image:tag@sha256:xxx in DOCKERFILE.
# And record image sha256 to a target file.
#!/bin/bash

IMAGENAME=$1
DOCKERFILE=$2
ARCH=$3
DOCKERFILE_TARGE=$4
DISTRO=$5

repo_root=$(dirname $(dirname $(realpath $0)))
version_file=$repo_root/files/build/versions/default/versions-docker
new_version_file=$repo_root/target/versions/default/versions-docker
mkdir -p $(dirname $new_version_file)

. src/sonic-build-hooks/buildinfo/config/buildinfo.config

image_tag=$(grep "^FROM " $DOCKERFILE | awk '{print$2}')
image_tag_noprefix=$image_tag
[ -n "$DEFAULT_CONTAINER_REGISTRY" ] && image_tag_noprefix=$(echo $image_tag | sed "s#$DEFAULT_CONTAINER_REGISTRY##")
image=$(echo $image_tag | cut -f1 -d:)
hash_value=$(grep "${ARCH}:${image_tag_noprefix}" $version_file 2> /dev/null | awk -F== '{print$2}')

echo "=============== Begin ===============" >> $new_version_file.log
echo "input: $1,$2,$3,$4,$5" >> $new_version_file.log
echo "FROM $image_tag" >> $new_version_file.log
echo "image_tag_noprefix: $image_tag_noprefix" >> $new_version_file.log
echo "repo_root: $repo_root" >> $new_version_file.log
echo "local image: $(if [ -f $repo_root/target/$image.gz ];then echo true;else echo false;fi)" >> $new_version_file.log
echo "hash_value: $hash_value" >> $new_version_file.log
echo "SONIC_VERSION_CONTROL_COMPONENTS: $SONIC_VERSION_CONTROL_COMPONENTS" >> $new_version_file.log
echo "DEFAULT_CONTAINER_REGISTRY: $DEFAULT_CONTAINER_REGISTRY" >> $new_version_file.log

[ -f "$repo_root/target/$image.gz" ] && exit 0

if [[ ",$SONIC_VERSION_CONTROL_COMPONENTS," == *,all,* ]] || [[ ",$SONIC_VERSION_CONTROL_COMPONENTS," == *,docker,* ]]; then
    if [ -z $hash_value ];then
        echo "Error: ${ARCH}:$image_tag_noprefix hash value not found!!!" >> $new_version_file.log
        exit 0
    fi
    oldimage=$image_tag
    newimage="${oldimage}@$hash_value"
    echo "sed -i \"s#$oldimage#$newimage#\" $DOCKERFILE" >> $new_version_file.log
    sed -i "s#$oldimage#$newimage#" $DOCKERFILE
else
    hash_value=$(docker pull $image_tag 2>> $new_version_file.log | grep Digest | awk '{print$2}')
    if [ -z $hash_value ];then
        echo "docker pull: $(docker pull $image_tag 2>/dev/null)" >> $new_version_file.log
        exit 0
    fi
fi

if [ -n "$hash_value" ];then
    echo -e "${ARCH}:${image_tag_noprefix}==$hash_value" >> $new_version_file
    sort -u $new_version_file -o $new_version_file
fi