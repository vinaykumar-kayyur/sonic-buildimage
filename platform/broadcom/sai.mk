BRCM_SAI = libsaibcm_4.3.5.3-4_amd64.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/4.3/202012/libsaibcm_4.3.5.3-4_amd64.deb?sv=2020-08-04&st=2022-06-05T04%3A03%3A46Z&se=2037-06-06T04%3A03%3A00Z&sr=b&sp=r&sig=mW4NrbqbRxsoFP8bTcN%2F%2B7c34145pzLnPUf2ZkO%2Bs10%3D"
BRCM_SAI_DEV = libsaibcm-dev_4.3.5.3-4_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/4.3/202012/libsaibcm-dev_4.3.5.3-4_amd64.deb?sv=2020-08-04&st=2022-06-05T04%3A04%3A09Z&se=2037-06-06T04%3A04%3A00Z&sr=b&sp=r&sig=OyCbX8SNY9O91hz9rlCpetmFwXT9dsXuVM8xykkTgfQ%3D"

SONIC_ONLINE_DEBS += $(BRCM_SAI)
$(BRCM_SAI_DEV)_DEPENDS += $(BRCM_SAI)
$(eval $(call add_conflict_package,$(BRCM_SAI_DEV),$(LIBSAIVS_DEV)))
