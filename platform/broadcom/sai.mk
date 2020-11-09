BRCM_SAI = libsaibcm_4.2.1.5_amd64.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/4.2/master/libsaibcm_4.2.1.5_amd64.deb?sv=2015-04-05&sr=b&sig=%2Bch%2F0647K8rtDU8puV9mV2hVqbEPQW4Z6oAzT%2FTRrhU%3D&se=2020-11-13T04%3A47%3A02Z&sp=r"
BRCM_SAI_DEV = libsaibcm-dev_4.2.1.5_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/4.2/master/libsaibcm-dev_4.2.1.5_amd64.deb?sv=2015-04-05&sr=b&sig=q3A%2Bbav3nQ%2BHG2O1C9lizY1430%2FUf4MmsM5mvheQkeI%3D&se=2020-11-13T04%3A48%3A09Z&sp=r"

SONIC_ONLINE_DEBS += $(BRCM_SAI)
$(BRCM_SAI_DEV)_DEPENDS += $(BRCM_SAI)
$(eval $(call add_conflict_package,$(BRCM_SAI_DEV),$(LIBSAIVS_DEV)))
