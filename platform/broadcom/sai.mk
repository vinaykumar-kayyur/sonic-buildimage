BRCM_SAI = libsaibcm_3.7.5.2_amd64.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/3.7/libsaibcm_3.7.5.2_amd64.deb?sv=2015-04-05&sr=b&sig=QKJ2MvpYP%2BFPmJZXaNZ4M%2B1Bmk5qVTENoJsmnJgcvmo%3D&se=2034-05-16T19%3A17%3A32Z&sp=r"
BRCM_SAI_DEV = libsaibcm-dev_3.7.5.2_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/3.7/libsaibcm-dev_3.7.5.2_amd64.deb?sv=2015-04-05&sr=b&sig=%2BKKzHd1MNBSCewOZZjQcuAdjkFoR3Ppzl5gXMNGSTWM%3D&se=2034-05-16T19%3A17%3A08Z&sp=r"

SONIC_ONLINE_DEBS += $(BRCM_SAI)
$(BRCM_SAI_DEV)_DEPENDS += $(BRCM_SAI)
