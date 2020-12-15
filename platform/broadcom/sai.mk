BRCM_SAI = libsaibcm_4.2.1.5-7_amd64.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/4.2/master/libsaibcm_4.2.1.5-7_amd64.deb?sv=2019-12-12&st=2020-12-13T03%3A32%3A56Z&se=2021-12-14T03%3A32%3A00Z&sr=b&sp=r&sig=XO2u32fvb15h4RMw4wEBibfoSLkvf6%2FRPscD%2FZlkrEQ%3D"
BRCM_SAI_DEV = libsaibcm-dev_4.2.1.5-7_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/4.2/master/libsaibcm-dev_4.2.1.5-7_amd64.deb?sv=2019-12-12&st=2020-12-13T03%3A33%3A27Z&se=2021-12-14T03%3A33%3A00Z&sr=b&sp=r&sig=8K5D%2Fk%2F3PBu%2BW57%2B7EPjbDeoxSpZ2MvSEJaDtR5TmdU%3D"

SONIC_ONLINE_DEBS += $(BRCM_SAI)
$(BRCM_SAI_DEV)_DEPENDS += $(BRCM_SAI)
$(eval $(call add_conflict_package,$(BRCM_SAI_DEV),$(LIBSAIVS_DEV)))
