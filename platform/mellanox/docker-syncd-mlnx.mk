# docker image for mlnx syncd

DOCKER_SYNCD_PLATFORM_CODE = mlnx
include $(PLATFORM_PATH)/../template/docker-syncd-base.mk

$(DOCKER_SYNCD_BASE)_DEPENDS += $(SYNCD) $(PYTHON_SDK_API)
$(DOCKER_SYNCD_BASE)_PYTHON_DEBS += $(MLNX_SFPD)


$(DOCKER_SYNCD_BASE)_RUN_OPT += -v /host/warmboot:/var/warmboot

