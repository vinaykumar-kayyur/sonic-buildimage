DOCKER_GBSYNCD_PLATFORM_CODE = credo

LIBSAI_CREDO = libsai-credo_1.0_amd64.deb
$(LIBSAI_CREDO)_URL =

ifneq ($($(LIBSAI_CREDO)_URL),)
include $(PLATFORM_PATH)/../template/docker-gbsyncd-base.mk
SONIC_ONLINE_DEBS += $(LIBSAI_CREDO)
$(DOCKER_GBSYNCD_BASE)_DEPENDS += $(SYNCD) $(LIBSAI_CREDO)
endif
