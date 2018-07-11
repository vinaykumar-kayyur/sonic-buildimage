# libsaithrift-dev package

LIBSAITHRIFT_DEV_BRCM = libsaithrift-dev_1.3.0_amd64.deb
$(LIBSAITHRIFT_DEV_BRCM)_SRC_PATH = $(SRC_PATH)/sonic-sairedis/SAI
$(LIBSAITHRIFT_DEV_BRCM)_DEPENDS += $(LIBTHRIFT) $(LIBTHRIFT_DEV) $(THRIFT_COMPILER) $(BRCM_SAI) $(BRCM_SAI_DEV)
$(LIBSAITHRIFT_DEV_BRCM)_RDEPENDS += $(LIBTHRIFT) $(BRCM_SAI)
SONIC_DPKG_DEBS += $(LIBSAITHRIFT_DEV_BRCM)
