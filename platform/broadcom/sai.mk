BRCM_SAI = libsaibcm_3.7.3.2_amd64.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/3.7/libsaibcm_3.7.3.2_amd64.deb?sv=2015-04-05&sr=b&sig=KOnFbUGXmKb%2Fn9ca3CTvKxs6vYyILUQJy4Dh0nFjQXk%3D&se=2029-09-22T23%3A16%3A57Z&sp=r"

BRCM_SAI_DEV = libsaibcm-dev_3.7.3.2_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/3.7/libsaibcm-dev_3.7.3.2_amd64.deb?sv=2015-04-05&sr=b&sig=xfEJ303VAnheuikvYLpf0VukXrN%2FLc6dFu%2B45ZEGclY%3D&se=2029-09-22T23%3A17%3A44Z&sp=r"

SONIC_ONLINE_DEBS += $(BRCM_SAI)
$(BRCM_SAI_DEV)_DEPENDS += $(BRCM_SAI)
