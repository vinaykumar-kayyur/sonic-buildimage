# docker image for load

DOCKER_UBUNTU_STEM = ubuntu
DOCKER_UBUNTU = $(DOCKER_UBUNTU_STEM).gz

$(DOCKER_UBUNTU)_PACKAGE_NAME = ubuntu
$(DOCKER_UBUNTU)_CONTAINER_NAME = ubuntu
$(DOCKER_UBUNTU)_URL = https://sonicstoragepublic.blob.core.windows.net/public/ubuntu.gz
$(DOCKER_UBUNTU)_RUN_OPT += --privileged -t
$(DOCKER_UBUNTU)_RUN_OPT += -v /etc/sonic:/etc/sonic:ro

DOWNLOADED_DOCKER_IMAGES += $(DOCKER_UBUNTU)
SONIC_INSTALL_DOCKER_IMAGES += $(DOCKER_UBUNTU)
