BRCM_SAI = libsaibcm_3.3.3.1-2_amd64.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/3.3/libsaibcm_3.3.3.1-2_amd64.deb?sv=2015-04-05&sr=b&sig=qJZiMT3u8SF1bzMnEmIITKSvf11lR7B1jkd8HdLvWV0%3D&se=2032-08-23T02%3A26%3A39Z&sp=r"

BRCM_SAI_DEV = libsaibcm-dev_3.3.3.1-2_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/3.3/libsaibcm-dev_3.3.3.1-2_amd64.deb?sv=2015-04-05&sr=b&sig=rdxgnXiCUG%2FPMkTdOtLuyVRAtqzJrwmATtqSgvUaPPM%3D&se=2032-08-23T02%3A26%3A07Z&sp=r"

SONIC_ONLINE_DEBS += $(BRCM_SAI)
$(BRCM_SAI_DEV)_DEPENDS += $(BRCM_SAI)
