#! /bin/bash 

DOCKER_IMAGE_FILE=$1
REGISTRY_SERVER=$2
REGISTRY_USERNAME=$3
REGISTRY_PASSWD=$4
PLATFORM=$5
SONIC_VERSION=$6
DOCKER_IMAGE_TAG=$7

push_it() {
    docker tag $1 $2
    echo "Pushing $2"
    image_sha=$(docker push $2 | sed -n "s/.*: digest: sha256:\([0-9a-f]*\).*/\\1/p")
    echo "Remove $2"
    docker rmi $2 || true
    echo "Image sha256: $image_sha"
}

set -e
echo "Docker load $DOCKER_IMAGE_FILE"
docker load < $DOCKER_IMAGE_FILE

## Login the docker image registry server
## Note: user name and password are passed from command line
echo "Docker login $REGISTRY_USERNAME@$REGISTRY_SERVER"
docker login -u $REGISTRY_USERNAME -p "$REGISTRY_PASSWD" $REGISTRY_SERVER

## Get image name
docker_image_name=$(basename $DOCKER_IMAGE_FILE | cut -d. -f1)

remote_image_name=$REGISTRY_SERVER/sonic-dockers/$PLATFORM/$docker_image_name
push_it $docker_image_name $remote_image_name:$SONIC_VERSION

if [ ! -z $DOCKER_IMAGE_TAG ]
then
    push_it $docker_image_name $remote_image_name:$DOCKER_IMAGE_TAG
fi

echo "Remove $docker_image_name"
docker rmi $docker_image_name || true
echo "Job completed"
