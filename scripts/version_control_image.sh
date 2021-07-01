#!/bin/bash

# parse parameters & setup vars
parse_config(){
    if [ -f /usr/local/share/buildinfo/scripts/buildinfo_base.sh ];then
        # inside slave docker
        . /usr/local/share/buildinfo/scripts/buildinfo_base.sh
        version_file=$VERSION_PATH/versions-image
        new_version_file=$BUILD_VERSION_PATH/versions-image
    else
        # outside slave docker
        version_file=files/build/versions/default/versions-image
        new_version_file=target/versions/build/build-sonic-slave-$DISTRO/versions-image
    fi
    dir=`dirname $new_version_file`
    mkdir -p $dir
    touch $new_version_file
}

main(){
    parse_config
    docker_file=$1

    image_tag=`grep "^FROM " $docker_file | awk '{print$2}'`
    image=`echo $image_tag | cut -f1 -d:`
    tag=`echo $image_tag | cut -f2 -d:`
    # if docker image load from local build, exit.
    if [ -f target/${image_tag}.gz ]; then
        exit 0
    fi
    if [[ ",$SONIC_VERSION_CONTROL_COMPONENTS," == *,all,* ]] || [[ ",$SONIC_VERSION_CONTROL_COMPONENTS," == *,docker,* ]]; then
        if [ ! -f $version_file ];then
            echo "Failed to access $version_file"
            exit 1
        fi
        hash_value=`grep $image_tag $version_file | awk -F== '{print$2}'`
        if [ -z $hash_value ];then
            echo "Failed to verify the docker image: $image_tag, the hash value is not specified"
            exit 1
        fi
        oldstr=${image//\//\\/}
        newstr="${oldstr}@$hash_value"
        sed -i "s/$oldstr/$newstr/" $docker_file
    fi
    hash_value_latest=`docker pull $image_tag | grep Digest | awk '{print$2}'`

    echo -e "\n$image_tag==$hash_value_latest" >> $new_version_file
    sort -u $new_version_file -o $new_version_file
}

main "$@"
