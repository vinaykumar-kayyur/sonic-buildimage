BRCM_SAI = libsaibcm_3.0.3.2-1_amd64.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/libsaibcm_3.0.3.2-1_amd64.deb?sv=2015-04-05&sr=b&sig=lPxg6uBDx7UhFXw3kk00mOUbEskXImII4BBzTFpsxxU%3D&se=2031-05-30T22%3A18%3A52Z&sp=r"

BRCM_SAI_DEV = libsaibcm-dev_3.0.3.2-1_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/libsaibcm-dev_3.0.3.2-1_amd64.deb?sv=2015-04-05&sr=b&sig=hZoGZKc013UJnxlSep4f5K8wwESyjE4bhzm9Hw%2BAhg8%3D&se=2031-05-30T22%3A19%3A24Z&sp=r"

SONIC_ONLINE_DEBS += $(BRCM_SAI) $(BRCM_SAI_DEV)
$(BRCM_SAI_DEV)_DEPENDS += $(BRCM_SAI)
