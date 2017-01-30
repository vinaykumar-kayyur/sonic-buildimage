BRCM_SAI = libsaibcm_2.1.3.1+0-20170130225436.9-1.gbpfe8392_amd64.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/libsaibcm_2.1.3.1+0-20170130225436.9-1.gbpfe8392_amd64.deb?sv=2015-04-05&sr=b&sig=zLSoMFtrvdnAZ7ND5wLvBCK0ZL%2BQurqDiO2qjT7QoLk%3D&se=2030-10-09T23%3A06%3A30Z&sp=r"

BRCM_SAI_DEV = libsaibcm-dev_2.1.3.1+0-20170130225436.9-1.gbpfe8392_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/libsaibcm-dev_2.1.3.1+0-20170130225436.9-1.gbpfe8392_amd64.deb?sv=2015-04-05&sr=b&sig=GYAUp0P9uWoiAz9oSklrfcRSbwG3IaoDiRBtHY2tQ7A%3D&se=2030-10-09T23%3A07%3A10Z&sp=r"

SONIC_ONLINE_DEBS += $(BRCM_SAI) $(BRCM_SAI_DEV)
$(BRCM_SAI)_DEPENDS += $(BRCM_OPENNSL)
$(BRCM_SAI_DEV)_DEPENDS += $(BRCM_SAI)
