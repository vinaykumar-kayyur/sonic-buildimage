#!/bin/bash

# parse parameters & setup vars
parse_config(){
    if [ -f /usr/local/share/buildinfo/scripts/buildinfo_base.sh ];then
        # inside slave docker
        version_file=$VERSION_PATH/versions-image
        new_version_file=$BUILD_VERSION_PATH/versions-image
    else
        # outside slave docker
        version_file=files/build/versions/default/versions-image
        new_version_file=target/versions/build/build-sonic-slave-$DISTRO/versions-image
    fi
    dir=`dirname $new_version_file`
    mkdir -p $dir
}

main(){
    parse_config
    docker_file=$1

    image_tag=`grep "^FROM " $docker_file | awk '{print$2}'`
    hash_value_latest=`docker pull $image_tag | grep Digest | awk '{print$2}'`
    [ -f $version_file ] && hash_value=`grep $image_tag $version_file | awk -F== '{print$2}'`

    oldstr=${image_tag//\//\\/}
    newstr=`echo $oldstr | awk -F: '{print$1}'`@$hash_value

    if [[ ",$SONIC_VERSION_CONTROL_COMPONENTS," == *,all,* ]] || [[ ",$SONIC_VERSION_CONTROL_COMPONENTS," == *,docker,* ]]; then
        # version control
        [ ! -z "$hash_value" ] && result_str=`sed -i "s/$oldstr/$newstr/" $docker_file`
    else
        # record version file
        echo "$image_tag==$hash_value_latest" >> $new_version_file
    fi
}

main $@
