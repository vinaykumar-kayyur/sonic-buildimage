# Centec SAI

export CENTEC_SAI_VERSION = 1.10.2-1
export CENTEC_SAI = libsai_$(CENTEC_SAI_VERSION)_$(PLATFORM_ARCH).deb

$(CENTEC_SAI)_URL = https://github.com/pettershao-ragilenetworks/sonic-binaries/blob/main/centec-arm64/sai/libsai_1.10.2-1_arm64.deb


SONIC_ONLINE_DEBS += $(CENTEC_SAI)

