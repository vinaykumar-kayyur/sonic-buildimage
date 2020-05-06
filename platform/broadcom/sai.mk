BRCM_SAI = libsaibcm_3.7.4.2_amd64.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/3.7/libsaibcm_3.7.4.2_amd64.deb?sv=2015-04-05&sr=b&sig=sxAe6FwisgN2YRTJsjA8t6hDxGrReguhluh4xnQrbQ4%3D&se=2034-01-13T18%3A01%3A24Z&sp=r"
BRCM_SAI_DEV = libsaibcm-dev_3.7.4.2_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/3.7/libsaibcm-dev_3.7.4.2_amd64.deb?sv=2015-04-05&sr=b&sig=3v%2B7qSNXqbwFqAGgExS4PY9tDpcNiR6pi9xBEQYXv4g%3D&se=2034-01-13T18%3A06%3A39Z&sp=r"

SONIC_ONLINE_DEBS += $(BRCM_SAI)
$(BRCM_SAI_DEV)_DEPENDS += $(BRCM_SAI)
