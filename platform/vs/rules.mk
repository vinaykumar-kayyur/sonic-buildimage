include $(PLATFORM_PATH)/syncd-vs.mk
include $(PLATFORM_PATH)/docker-sonic-vs.mk
include $(PLATFORM_PATH)/docker-syncd-vs.mk
include $(PLATFORM_PATH)/docker-orchagent-vs.mk
include $(PLATFORM_PATH)/one-image.mk

SONIC_ALL += $(SONIC_ONE_IMAGE) $(DOCKER_SONIC_VS)
