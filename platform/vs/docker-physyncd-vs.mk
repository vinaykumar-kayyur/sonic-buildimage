# docker image for vs physyncd

DOCKER_PHYSYNCD_PLATFORM_CODE = vs
include $(PLATFORM_PATH)/../template/docker-physyncd-base.mk

$(DOCKER_PHYSYNCD_BASE)_DEPENDS += $(SYNCD_VS)

$(DOCKER_PHYSYNCD_BASE)_DBG_DEPENDS += $(SYNCD_VS_DBG) \
                                $(LIBSWSSCOMMON_DBG) \
                                $(LIBSAIMETADATA_DBG) \
                                $(LIBSAIREDIS_DBG) \
                                $(LIBSAIVS_DBG)

$(DOCKER_PHYSYNCD_BASE)_RUN_OPT += -v /host/warmboot:/var/warmboot
