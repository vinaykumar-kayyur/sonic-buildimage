BRCM_SAI = libsaibcm_3.7.5.1-3_amd64.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/3.7/master/libsaibcm_3.7.5.1-3_amd64.deb?sv=2015-04-05&sr=b&sig=jEHMQEFOVpIxsCh0GUuHXY5EB%2BNAygbLpAxz9Is6jIg%3D&se=2034-04-13T22%3A29%3A13Z&sp=r"
BRCM_SAI_DEV = libsaibcm-dev_3.7.5.1-3_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/3.7/master/libsaibcm-dev_3.7.5.1-3_amd64.deb?sv=2015-04-05&sr=b&sig=c%2BAd3wMESlwFqRMy%2F1X3kPApuxA62JeX0n1ItWY%2BQgY%3D&se=2034-04-13T22%3A30%3A12Z&sp=r"

SONIC_ONLINE_DEBS += $(BRCM_SAI)
$(BRCM_SAI_DEV)_DEPENDS += $(BRCM_SAI)
$(eval $(call add_conflict_package,$(BRCM_SAI_DEV),$(LIBSAIVS_DEV)))
