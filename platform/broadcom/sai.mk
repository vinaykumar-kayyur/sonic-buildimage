BRCM_SAI = libsaibcm_3.7.3.3_amd64.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/3.7/libsaibcm_3.7.3.3_amd64.deb?sv=2015-04-05&sr=b&sig=zxLDHUSAGGKBTaO89EyTDB9Su7LCdTZY6OJARLvANMQ%3D&se=2020-11-28T22%3A54%3A04Z&sp=r"

BRCM_SAI_DEV = libsaibcm-dev_3.7.3.3_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/3.7/libsaibcm-dev_3.7.3.3_amd64.deb?sv=2015-04-05&sr=b&sig=3p1iVtVhWNqHcGd44XRfZorWiU4Fj9Xt7C22pyeRNv0%3D&se=2020-11-28T23%3A05%3A39Z&sp=r"

SONIC_ONLINE_DEBS += $(BRCM_SAI)
$(BRCM_SAI_DEV)_DEPENDS += $(BRCM_SAI)
