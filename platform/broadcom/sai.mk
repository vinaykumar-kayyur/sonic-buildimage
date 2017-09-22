BRCM_SAI = libsaibcm_3.0.3.2-3_amd64.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/libsaibcm_3.0.3.2-3_amd64.deb?sv=2015-04-05&sr=b&sig=N8PItR5KMlFJUQICeghzwSkiuqdBNBVTYX6svqR3wcg%3D&se=2031-06-01T18%3A46%3A00Z&sp=r"

BRCM_SAI_DEV = libsaibcm-dev_3.0.3.2-3_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/libsaibcm-dev_3.0.3.2-3_amd64.deb?sv=2015-04-05&sr=b&sig=wJ%2BKxm3CzBpCnkB4Zv70wlWbt9cTEOupPrVTcJe8CGM%3D&se=2031-06-01T18%3A46%3A28Z&sp=r"

SONIC_ONLINE_DEBS += $(BRCM_SAI) $(BRCM_SAI_DEV)
$(BRCM_SAI_DEV)_DEPENDS += $(BRCM_SAI)
