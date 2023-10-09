# docker dpu image for load
DOCKER_DPU_STEM = docker-dpu

DOCKER_DPU = $(DOCKER_DPU_STEM).gz

$(DOCKER_DPU)_PATH = $(PLATFORM_PATH)/$(DOCKER_DPU_STEM)

$(DOCKER_DPU)_LOAD_DOCKERS = $(DOCKER_DPU_BASE)

$(DOCKER_DPU)_LOAD_DOCKERS += $(DOCKER_CONFIG_ENGINE_BUSTER)

$(DOCKER_DPU)_DBG_DEPENDS += $($(DOCKER_CONFIG_ENGINE_BUSTER)_DBG_DEPENDS)

$(DOCKER_DPU)_DBG_IMAGE_PACKAGES = $($(DOCKER_CONFIG_ENGINE_BUSTER)_DBG_IMAGE_PACKAGES)

SONIC_DOCKER_IMAGES += $(DOCKER_DPU)

$(DOCKER_DPU)_PACKAGE_NAME = dpu
$(DOCKER_DPU)_CONTAINER_NAME = dpu
$(DOCKER_DPU)_VERSION = 1.0.0
$(DOCKER_DPU)_RUN_OPT += --privileged -t
$(DOCKER_DPU)_RUN_OPT += -v /etc/sonic:/etc/sonic:ro

#NIC_MOUNT="-v /dev/shm:/dev/shm -v /boot/nicA/nic_core:/nic -v /boot/nicA/shared/conf/gen:/nic/conf/gen"
$(DOCKER_DPU)_RUN_OPT += --privileged -t
$(DOCKER_DPU)_RUN_OPT += -v /host/dpu/update:/update
$(DOCKER_DPU)_RUN_OPT += -v /host/dpu/sysconfig/config0:/sysconfig/config0
$(DOCKER_DPU)_RUN_OPT += -v /host/dpu/sysconfig/config1:/sysconfig/config1
$(DOCKER_DPU)_RUN_OPT += -v /host/dpu/obfl:/obfl
$(DOCKER_DPU)_RUN_OPT += -v /host/dpu/data:/data
$(DOCKER_DPU)_RUN_OPT += -v /host/dpu/tmpfsshare:/tmp
$(DOCKER_DPU)_RUN_OPT += -v /host/dpu/runfs:/run
$(DOCKER_DPU)_RUN_OPT += -v /host/dpu/logfs:/var/log
$(DOCKER_DPU)_RUN_OPT += -v /sys:/sys
#$(DOCKER_DPU)_RUN_OPT += $NIC_MOUNT
$(DOCKER_DPU)_RUN_OPT += --net=host
$(DOCKER_DPU)_RUN_OPT += docker-dpu:v1

SONIC_BUSTER_DOCKERS += $(DOCKER_DPU)
SONIC_INSTALL_DOCKER_IMAGES += $(DOCKER_DPU)
