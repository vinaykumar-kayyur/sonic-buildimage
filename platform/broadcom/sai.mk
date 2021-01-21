BRCM_SAI = libsaibcm_4.2.1.5-10_amd64.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/4.3/master/libsaibcm_4.3.0.10_amd64.deb?sv=2015-04-05&sr=b&sig=yKic6%2FwJ2mHM6n4lXrR32yqEsLt01EUzqxIuOAvV7uQ%3D&se=2022-01-21T23%3A13%3A54Z&sp=r"
BRCM_SAI_DEV = libsaibcm-dev_4.2.1.5-10_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/4.3/master/libsaibcm-dev_4.3.0.10_amd64.deb?sv=2015-04-05&sr=b&sig=IAx7bmd0mgQL8DyF345jQOQHRxwx9wen2AyWdacfmw4%3D&se=2022-01-21T23%3A15%3A30Z&sp=r"

SONIC_ONLINE_DEBS += $(BRCM_SAI)
$(BRCM_SAI_DEV)_DEPENDS += $(BRCM_SAI)
$(eval $(call add_conflict_package,$(BRCM_SAI_DEV),$(LIBSAIVS_DEV)))
