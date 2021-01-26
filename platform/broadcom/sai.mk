BRCM_SAI = libsaibcm_4.3.0.10-2_amd64.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/4.3/master/libsaibcm_4.3.0.10-2_amd64.deb?sv=2015-04-05&sr=b&sig=WmZegm2db91OxDM8vA%2FjRAhhAZHJWE7yrTug5S784co%3D&se=2022-06-10T02%3A35%3A42Z&sp=r"
BRCM_SAI_DEV = libsaibcm-dev_4.3.0.10-2_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/4.3/master/libsaibcm-dev_4.3.0.10-2_amd64.deb?sv=2015-04-05&sr=b&sig=mI3xjiOeQANZweWt115wjSE5q1jLPYLJRC4FYIlJ8nY%3D&se=2022-06-10T02%3A36%3A30Z&sp=r"

SONIC_ONLINE_DEBS += $(BRCM_SAI)
$(BRCM_SAI_DEV)_DEPENDS += $(BRCM_SAI)
$(eval $(call add_conflict_package,$(BRCM_SAI_DEV),$(LIBSAIVS_DEV)))
