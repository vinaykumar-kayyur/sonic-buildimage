BRCM_SAI = libsaibcm_4.2.1.5_amd64-buster.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/4.2/master/libsaibcm_4.2.1.5_amd64-buster.deb?sv=2019-12-12&st=2020-11-24T21%3A45%3A37Z&se=2021-11-25T21%3A45%3A00Z&sr=b&sp=r&sig=6we05VowbABC4VhxUOQlZdnfohRgqpOMUxYdL9O4sX0%3D"
BRCM_SAI_DEV = libsaibcm-dev_4.2.1.5_amd64-buster.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/4.2/master/libsaibcm-dev_4.2.1.5_amd64-buster.deb?sv=2019-12-12&st=2020-11-24T21%3A46%3A53Z&se=2021-11-25T21%3A46%3A00Z&sr=b&sp=r&sig=efXrwkOa1EVVecQCYslN%2BMTXhxWj4RuwKm06Uh%2B5M3I%3D"

SONIC_ONLINE_DEBS += $(BRCM_SAI)
$(BRCM_SAI_DEV)_DEPENDS += $(BRCM_SAI)
$(eval $(call add_conflict_package,$(BRCM_SAI_DEV),$(LIBSAIVS_DEV)))
