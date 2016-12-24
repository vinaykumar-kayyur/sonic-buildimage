BRCM_SAI = libsaibcm_2.0.3.7_amd64.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/libsaibcm_2.0.3.7_amd64.deb?sv=2015-04-05&sr=b&sig=3S9pY5Allql4fguipFdilJ%2BzP%2Ff4dvUFe3mNY3uhCIc%3D&se=2030-09-02T21%3A43%3A38Z&sp=r"

BRCM_SAI_DEV = libsaibcm-dev_2.0.3.7_amd64.deb
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/libsaibcm-dev_2.0.3.7_amd64.deb?sv=2015-04-05&sr=b&sig=ztk12uK%2BN1LpCqsZM35YBs8m90OCPWMsjj%2FnY3IcJ7g%3D&se=2030-09-02T21%3A44%3A18Z&sp=r"

$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))

SONIC_ONLINE_DEBS += $(BRCM_SAI)

$(BRCM_SAI)_DEPENDS += $(BRCM_OPENNSL)
$(BRCM_SAI_DEV)_DEPENDS += $(BRCM_SAI)
