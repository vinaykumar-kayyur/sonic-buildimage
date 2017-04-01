CAVM_SAI_URL = https://github.com/XPliant/OpenXPS/raw/7704afc78cc1ce3b4e2aca6659afa9dc171ba874/SAI

CAVM_XPNET_DEB = xp80-Pcie-Endpoint.deb
$(CAVM_XPNET_DEB)_URL = $(CAVM_SAI_URL)/netdev/$(CAVM_XPNET_DEB)

SONIC_ONLINE_DEBS += $(CAVM_XPNET_DEB)
