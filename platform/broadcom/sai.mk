BRCM_SAI = libsaibcm_4.3.3.4_amd64.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/4.3/master/libsaibcm_4.3.3.4_amd64.deb?sv=2015-04-05&sr=b&sig=RaM7VKtUVZgKVvCbcBp3WP7cqrLT%2BrjwHv3kLdj8zzk%3D&se=2034-12-10T05%3A39%3A44Z&sp=r"
BRCM_SAI_DEV = libsaibcm-dev_4.3.3.4_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/4.3/master/libsaibcm-dev_4.3.3.4_amd64.deb?sv=2015-04-05&sr=b&sig=im7%2Fqp2dnoQTaPhY3Jv%2BHV0eZ4mPu27BT%2FbcF%2BQxGyQ%3D&se=2034-12-10T05%3A40%3A26Z&sp=r"

BRCM_SAI_DBG = libsaibcm-dbg_4.3.0.10-3_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DBG)))
$(BRCM_SAI_DBG)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/4.3/master/libsaibcm-dbg_4.3.0.10-3_amd64.deb?sv=2019-10-10&st=2021-02-01T18%3A50%3A19Z&se=2036-02-02T18%3A50%3A00Z&sr=b&sp=r&sig=fpeFJ0AQeViX%2Bq4XZjxryEF0au2JtilumteRsZkXR6Y%3D"

SONIC_ONLINE_DEBS += $(BRCM_SAI)
$(BRCM_SAI_DEV)_DEPENDS += $(BRCM_SAI)
$(eval $(call add_conflict_package,$(BRCM_SAI_DEV),$(LIBSAIVS_DEV)))
$(BRCM_SAI_DBG)_DEPENDS += $(BRCM_SAI)
