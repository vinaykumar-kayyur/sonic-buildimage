# Centec SAI

export CENTEC_SAI_VERSION = 1.10.2-1
export CENTEC_SAI = libsai_$(CENTEC_SAI_VERSION)_$(PLATFORM_ARCH).deb
export CENTEC_SAI_DEV = libsai-dev_$(CENTEC_SAI_VERSION)_$(PLATFORM_ARCH).deb
export CENTEC_SAI_URL_PREFIX = "https://github.com/CentecNetworks/sonic-binaries/raw/master/$(PLATFORM_ARCH)/sai"

$(CENTEC_SAI)_URL = https://github.com/pettershao-ragilenetworks/sonic-binaries/raw/main/centec-arm64/sai/$(CENTEC_SAI)

SONIC_ONLINE_DEBS += $(CENTEC_SAI)
SONIC_ONLINE_DEBS += $(CENTEC_SAI_DEV)
$(CENTEC_SAI_DEV)_DEPENDS += $(CENTEC_SAI)
