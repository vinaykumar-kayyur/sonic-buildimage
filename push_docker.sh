DOCKER_IMAGE_FILE=$1
REGISTRY_SERVER=$2
REGISTRY_PORT=$3
REGISTRY_USERNAME=$4
REGISTRY_PASSWD=$5
DOCKER_IMAGE_TAG=""
PLATFORM=""
SONIC_VERSION=""

shift 5

if [ "$#" != "0" ]
then
    DOCKER_IMAGE_TAG=$1
    shift
fi

if [ "$#" != "0" ]
then
    PLATFORM=$1
    shift
fi

if [ "$#" != "0" ]
then
    SONIC_VERSION=$1
fi

push_it() {
    # $1 - Given image name
    # $2 - Remote image name

    docker tag $1 $2
    echo "Pushing $2"
    image_sha=$(docker push $2 | sed -n "s/.*: digest: sha256:\([0-9a-f]*\).*/\\1/p")
    echo "Remove $2"
    docker rmi $2 || true
    echo "Image sha256: $image_sha"
}

set -e

echo "Loading image ${DOCKER_IMAGE_FILE}"
docker load < ${DOCKER_IMAGE_FILE}

## Fetch the Jenkins build number if inside it
[ ${BUILD_NUMBER} ] || {
    echo "No BUILD_NUMBER found, setting to 0."
    BUILD_NUMBER="0"
}

## Login the docker image registry server
## Note: user name and password are passed from command line
docker login -u ${REGISTRY_USERNAME} -p "${REGISTRY_PASSWD}" ${REGISTRY_SERVER}:${REGISTRY_PORT}

## Get Docker image name
docker_image_name=$(basename ${DOCKER_IMAGE_FILE} | cut -d. -f1)
remote_image_name=${REGISTRY_SERVER}:${REGISTRY_PORT}/${docker_image_name}

[ -z "${DOCKER_IMAGE_TAG}" ] || {
    push_it ${docker_image_name} ${remote_image_name}:${DOCKER_IMAGE_TAG}
}

[ -n "${SONIC_VERSION}" ] || {
    # If SONIC_VERSION is not given, tag it with build number.
    timestamp="$(date -u +%Y%m%d)"
    build_version="${timestamp}.bld-${BUILD_NUMBER}"
    push_it ${docker_image_name} ${remote_image_name}:${build_version}
}

[ -z "${SONIC_VERSION}" ] || {
    remote_image_name=${REGISTRY_SERVER}/sonic-dockers/${PLATFORM}/${docker_image_name}:${SONIC_VERSION}
    push_it ${docker_image_name} ${remote_image_name}
}

docker rmi $docker_image_name || true
echo "Job completed"

