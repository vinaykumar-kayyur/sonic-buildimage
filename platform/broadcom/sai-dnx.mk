BRCM_DNX_SAI = libsaibcm_dnx_4.3.3.1-1_amd64.deb
$(BRCM_DNX_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/4.3/master/libsaibcm_dnx_4.3.3.1-1_amd64.deb?sv=2015-04-05&sr=b&sig=6dfTLPsvg%2BtK9u23Z%2BEeqQWj3GCiBvlv8lbwEwv5k7U%3D&se=2034-11-15T22%3A02%3A40Z&sp=r"
BRCM_DNX_SAI_DEV = libsaibcm_dnx-dev_4.3.3.1-1_amd64.deb
$(eval $(call add_derived_package,$(BRCM_DNX_SAI),$(BRCM_DNX_SAI_DEV)))
$(BRCM_DNX_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/4.3/master/libsaibcm_dnx-dev_4.3.3.1-1_amd64.deb?sv=2015-04-05&sr=b&sig=0FpubRB0zxgWhSovC5maX8w5pH83vE8WjPml40KWt24%3D&se=2034-11-15T22%3A03%3A43Z&sp=r"

SONIC_ONLINE_DEBS += $(BRCM_DNX_SAI)
$(BRCM_DNX_SAI_DEV)_DEPENDS += $(BRCM_DNX_SAI)
#$(eval $(call add_conflict_package,$(BRCM_DNX_SAI_DEV),$(LIBSAIVS_DEV)))
