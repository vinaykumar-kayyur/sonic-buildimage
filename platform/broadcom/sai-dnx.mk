BRCM-DNX_SAI = libsaibcm-dnx_4.3.0.13-1_amd64.deb
$(BRCM-DNX_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/4.3/master/libsaibcm-dnx_4.3.0.13-1_amd64.deb?sv=2015-04-05&sr=b&sig=8UlGRZ1Fx%2B2%2BcWUK8zL%2F1FCQKEA%2FBay2tV3gF%2B4F9DU%3D&se=2034-10-31T04%3A53%3A51Z&sp=r"
BRCM-DNX_SAI_DEV = libsaibcm-dnx-dev_4.3.0.13-1_amd64.deb
$(eval $(call add_derived_package,$(BRCM-DNX_SAI),$(BRCM-DNX_SAI_DEV)))
$(BRCM-DNX_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/4.3/master/libsaibcm-dnx-dev_4.3.0.13-1_amd64.deb?sv=2015-04-05&sr=b&sig=OoJwgS%2FHyV2vPJOgeABjr1eeCa12vi8cNCASSMl%2Bt5w%3D&se=2034-10-31T04%3A54%3A31Z&sp=r"

SONIC_ONLINE_DEBS += $(BRCM-DNX_SAI)
$(BRCM-DNX_SAI_DEV)_DEPENDS += $(BRCM-DNX_SAI)
#$(eval $(call add_conflict_package,$(BRCM-DNX_SAI_DEV),$(LIBSAIVS_DEV)))
