# sonic broadcom raw image installer

SONIC_RAW_IMAGE = sonic-broadcom.raw
$(SONIC_RAW_IMAGE)_MACHINE = broadcom
$(SONIC_RAW_IMAGE)_IMAGE_TYPE = raw
$(SONIC_RAW_IMAGE)_DEPENDS += $(BRCM_OPENNSL_KERNEL)
$(SONIC_RAW_IMAGE)_INSTALLS += $(DELL_S6000_PLATFORM_MODULE) \
                               $(DELL_Z9100_PLATFORM_MODULE) \
                               $(DELL_S6100_PLATFORM_MODULE) \
                               $(INGRASYS_S8900_54XC_PLATFORM_MODULE) \
                               $(INGRASYS_S8900_64XC_PLATFORM_MODULE) \
                               $(INGRASYS_S9100_PLATFORM_MODULE) \
                               $(ACCTON_AS7712_32X_PLATFORM_MODULE) \
                               $(INVENTEC_D7032Q28B_PLATFORM_MODULE) \
                               $(CEL_DX010_PLATFORM_MODULE)
$(SONIC_RAW_IMAGE)_DOCKERS += $(SONIC_INSTALL_DOCKER_IMAGES)
SONIC_INSTALLERS += $(SONIC_RAW_IMAGE)
