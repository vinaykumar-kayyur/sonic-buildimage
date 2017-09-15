BRCM_SAI = libsaibcm_3.0.3.2_amd64.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/libsaibcm_3.0.3.2_amd64.deb?sv=2015-04-05&sr=b&sig=Xly0vL6lps8EeSXSO43TeuW%2FHTT1inQU8%2FBZPDstEzw%3D&se=2031-05-25T18%3A37%3A15Z&sp=r"

BRCM_SAI_DEV = libsaibcm-dev_3.0.3.2_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/libsaibcm-dev_3.0.3.2_amd64.deb?sv=2015-04-05&sr=b&sig=Dl%2BAVY0qcheTqDAyRVqxZ5ab8hsSCH4NKzmHq4BrIrs%3D&se=2031-05-25T18%3A37%3A41Z&sp=r"

SONIC_ONLINE_DEBS += $(BRCM_SAI) $(BRCM_SAI_DEV)
$(BRCM_SAI_DEV)_DEPENDS += $(BRCM_SAI)
