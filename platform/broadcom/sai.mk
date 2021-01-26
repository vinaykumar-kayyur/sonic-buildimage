BRCM_SAI = libsaibcm_4.3.3.4_amd64.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/4.3/master/libsaibcm_4.3.3.4_amd64.deb?sv=2015-04-05&sr=b&sig=RaM7VKtUVZgKVvCbcBp3WP7cqrLT%2BrjwHv3kLdj8zzk%3D&se=2034-12-10T05%3A39%3A44Z&sp=r"
BRCM_SAI_DEV = libsaibcm-dev_4.3.3.4_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/4.3/master/libsaibcm-dev_4.3.3.4_amd64.deb?sv=2015-04-05&sr=b&sig=im7%2Fqp2dnoQTaPhY3Jv%2BHV0eZ4mPu27BT%2FbcF%2BQxGyQ%3D&se=2034-12-10T05%3A40%3A26Z&sp=r"

BRCM_SAI_DBG = libsaibcm-dbg_4.2.2.4_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DBG)))
$(BRCM_SAI_DBG)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/4.2/master/buster/libsaibcm-dbg_4.2.2.4_amd64.deb?sv=2015-04-05&sr=b&sig=6NLCDzW3WYs5Yui4grSEFxNbY9XoK7Dv3I4xRv1w4AY%3D&se=2048-06-11T17%3A24%3A27Z&sp=r"

SONIC_ONLINE_DEBS += $(BRCM_SAI)
$(BRCM_SAI_DEV)_DEPENDS += $(BRCM_SAI)
$(eval $(call add_conflict_package,$(BRCM_SAI_DEV),$(LIBSAIVS_DEV)))
$(BRCM_SAI_DBG)_DEPENDS += $(BRCM_SAI)
