LIBSAIBCM_XGS_VERSION = 7.1.0.0-6
LIBSAIBCM_DNX_VERSION = 7.1.0.0-7
LIBSAIBCM_BRANCH_NAME = REL_7.0
LIBSAIBCM_XGS_URL_PREFIX = "https://sonicstorage.blob.core.windows.net/public/sai/bcmsai/$(LIBSAIBCM_BRANCH_NAME)/$(LIBSAIBCM_XGS_VERSION)"
LIBSAIBCM_DNX_URL_PREFIX = "https://sonicstorage.blob.core.windows.net/public/sai/bcmsai/$(LIBSAIBCM_BRANCH_NAME)/$(LIBSAIBCM_DNX_VERSION)"

BRCM_XGS_SAI = libsaibcm_$(LIBSAIBCM_XGS_VERSION)_amd64.deb
$(BRCM_XGS_SAI)_URL = "$(LIBSAIBCM_XGS_URL_PREFIX)/$(BRCM_XGS_SAI)"
BRCM_XGS_SAI_DEV = libsaibcm-dev_$(LIBSAIBCM_XGS_VERSION)_amd64.deb
$(eval $(call add_derived_package,$(BRCM_XGS_SAI),$(BRCM_XGS_SAI_DEV)))
$(BRCM_XGS_SAI_DEV)_URL = "$(LIBSAIBCM_XGS_URL_PREFIX)/$(BRCM_XGS_SAI_DEV)"

# SAI module for DNX Asic family
BRCM_DNX_SAI = libsaibcm_dnx_$(LIBSAIBCM_DNX_VERSION)_amd64.deb
$(BRCM_DNX_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/7.0/7.1.0.0-7/libsaibcm_dnx_7.1.0.0-7_amd64.deb?sv=2020-10-02&st=2022-07-23T02%3A00%3A55Z&se=2026-07-24T02%3A00%3A00Z&sr=b&sp=r&sig=AEgooC3VpB3ee%2FcxtzUIWtoaFpWbdoYltuqEXGkrPwQ%3D"

SONIC_ONLINE_DEBS += $(BRCM_XGS_SAI)
SONIC_ONLINE_DEBS += $(BRCM_DNX_SAI)
$(BRCM_XGS_SAI_DEV)_DEPENDS += $(BRCM_XGS_SAI)
$(eval $(call add_conflict_package,$(BRCM_XGS_SAI_DEV),$(LIBSAIVS_DEV)))
$(BRCM_SAI_DBG)_DEPENDS += $(BRCM_XGS_SAI)
