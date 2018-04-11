BRCM_SAI = libsaibcm_3.1.3.4-9_amd64.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/libsaibcm_3.1.3.4-9_amd64.deb?sv=2015-04-05&sr=b&sig=J2TrGxJuOEKXNPOw%2B00%2BL8LLbAmvg9NQtqb73HPsEUY%3D&se=2031-12-19T21%3A33%3A18Z&sp=r"

BRCM_SAI_DEV = libsaibcm-dev_3.1.3.4-9_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/libsaibcm-dev_3.1.3.4-9_amd64.deb?sv=2015-04-05&sr=b&sig=mEIYvBBUKIFwUpGvL6%2FOd6c2Wl0jS6rO9ZizOiPu1fA%3D&se=2031-12-19T21%3A32%3A42Z&sp=r"

SONIC_ONLINE_DEBS += $(BRCM_SAI) $(BRCM_SAI_DEV)
$(BRCM_SAI_DEV)_DEPENDS += $(BRCM_SAI)
