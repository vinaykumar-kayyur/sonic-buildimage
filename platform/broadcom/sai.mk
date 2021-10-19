BRCM_SAI = libsaibcm_6.0.0.10_amd64.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/6.0/master/libsaibcm_6.0.0.10_amd64.deb?sv=2020-08-04&st=2021-10-18T20%3A10%3A37Z&se=2030-10-19T20%3A10%3A00Z&sr=b&sp=r&sig=4pIluTLBmfOizMOlk93%2F73hrYH%2B0wnPizinxzgdZeuw%3D"
BRCM_SAI_DEV = libsaibcm-dev_6.0.0.10_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/6.0/master/libsaibcm-dev_6.0.0.10_amd64.deb?sv=2020-08-04&st=2021-10-18T20%3A33%3A23Z&se=2030-10-19T20%3A33%3A00Z&sr=b&sp=r&sig=22zGsALAPStYDs42Ryegtf23zUvy9Hc0F9%2F6FOIdEn0%3D"

# SAI module for DNX Asic family
BRCM_DNX_SAI = libsaibcm_dnx_6.0.0.10_amd64.deb
$(BRCM_DNX_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/6.0/master/libsaibcm_dnx_6.0.0.10_amd64.deb?sv=2020-08-04&st=2021-10-19T05%3A15%3A02Z&se=2030-10-20T05%3A15%3A00Z&sr=b&sp=r&sig=tibPfsZy32BbX%2F7IM4Hhy%2FBRh35yY5F7q9xJA7HaNe4%3D"

SONIC_ONLINE_DEBS += $(BRCM_SAI)
SONIC_ONLINE_DEBS += $(BRCM_DNX_SAI)
$(BRCM_SAI_DEV)_DEPENDS += $(BRCM_SAI)
$(eval $(call add_conflict_package,$(BRCM_SAI_DEV),$(LIBSAIVS_DEV)))
