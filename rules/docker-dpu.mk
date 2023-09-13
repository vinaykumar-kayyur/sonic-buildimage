# docker image for load

DOCKER_DPU_STEM = docker-dpu
DOCKER_DPU = $(DOCKER_DPU_STEM).gz

$(DOCKER_DPU)_PACKAGE_NAME = dpu
$(DOCKER_DPU)_CONTAINER_NAME = dpu
$(DOCKER_DPU)_URL = https://sonicstoragepublic.blob.core.windows.net/public/ubuntu.gz
$(DOCKER_DPU)_MACHINE = vs
$(DOCKER_DPU)_VERSION = 1.0.0
$(DOCKER_DPU)_RUN_OPT += --privileged -t
$(DOCKER_DPU)_RUN_OPT += -v /etc/sonic:/etc/sonic:ro

DOWNLOADED_DOCKER_IMAGES += $(DOCKER_DPU)
SONIC_INSTALL_DOCKER_IMAGES += $(DOCKER_DPU)
