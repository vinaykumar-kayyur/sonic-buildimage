BRCM_SAI = libsaibcm_3.1.3.5-6_amd64.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/libsaibcm_3.1.3.5-6_amd64.deb?sv=2015-04-05&sr=b&sig=KUQq4AhA7LkJquKgaDTJt8qhKbl9%2FrqlgRZJDLurfKI%3D&se=2032-04-19T04%3A19%3A32Z&sp=r"

BRCM_SAI_DEV = libsaibcm-dev_3.1.3.5-6_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/libsaibcm-dev_3.1.3.5-6_amd64.deb?sv=2015-04-05&sr=b&sig=b8V1m1uiMznZFVGZER4ZjC6wyFx94A1NYWXbMNJ5OU0%3D&se=2032-04-19T04%3A18%3A50Z&sp=r"

SONIC_ONLINE_DEBS += $(BRCM_SAI) $(BRCM_SAI_DEV)
$(BRCM_SAI_DEV)_DEPENDS += $(BRCM_SAI)
