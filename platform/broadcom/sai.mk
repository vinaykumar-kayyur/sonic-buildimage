BRCM_SAI = libsaibcm_3.5.3.3m-1_amd64.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/3.5/libsaibcm_3.5.3.3m-1_amd64.deb?sv=2015-04-05&sr=b&sig=lQe95VWDf1x%2BQJaB4BpyBLYEmShQgRJIOWseFZgG%2BDM%3D&se=2033-07-26T04%3A11%3A58Z&sp=r"

BRCM_SAI_DEV = libsaibcm-dev_3.5.3.3m-1_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/3.5/libsaibcm-dev_3.5.3.3m-1_amd64.deb?sv=2015-04-05&sr=b&sig=RwL2o9S5he4JJ3oF2RDvZeBdzfAb%2BFojD4rsEM3kvhI%3D&se=2033-07-26T04%3A10%3A48Z&sp=r"

SONIC_ONLINE_DEBS += $(BRCM_SAI)
$(BRCM_SAI_DEV)_DEPENDS += $(BRCM_SAI)
