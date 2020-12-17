BRCM_SAI = libsaibcm_4.2.1.5-7_amd64.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/4.2/master/buster/libsaibcm_4.2.1.5-7_amd64.deb?sv=2019-12-12&st=2020-12-17T07%3A42%3A58Z&se=2030-12-18T07%3A42%3A00Z&sr=b&sp=r&sig=UEgPboasxJklhZcoRQBU%2Fapsj%2Bs32xgW0jLO%2FKc%2Fxe4%3D"
BRCM_SAI_DEV = libsaibcm-dev_4.2.1.5-7_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/4.2/master/buster/libsaibcm-dev_4.2.1.5-7_amd64.deb?sv=2019-12-12&st=2020-12-17T07%3A43%3A34Z&se=2030-12-18T07%3A43%3A00Z&sr=b&sp=r&sig=q6JBdPCSW7LC5NHhVZ28ORm%2FcKgUuqwM8cCSJZLXPUM%3D"

SONIC_ONLINE_DEBS += $(BRCM_SAI)
$(BRCM_SAI_DEV)_DEPENDS += $(BRCM_SAI)
$(eval $(call add_conflict_package,$(BRCM_SAI_DEV),$(LIBSAIVS_DEV)))
