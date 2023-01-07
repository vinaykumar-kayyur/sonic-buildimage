# Centec SAI

export CENTEC_SAI_VERSION = 1.10.2-1
export CENTEC_SAI = libsai_$(CENTEC_SAI_VERSION)_$(PLATFORM_ARCH).deb

$(CENTEC_SAI)_URL = https://github.com/pettershao-ragilenetworks/sonic-binaries/raw/main/centec-arm64/sai/libsai_$(CENTEC_SAI_VERSION)_$(PLATFORM_ARCH).deb
$(CENTEC_SAI)_DEPENDS += $(LIBNL3) $(LIBNL3_DEV) $(LIBNL_GENL3) $(LIBNL_GENL3_DEV)

SONIC_ONLINE_DEBS += $(CENTEC_SAI)

