# BFN Platform modules

GENL_PACKET_VERSION = 1.0-1
GENL_PACKET_KO_NAME = genl-packet-module
GENL_PACKET_DIR = sonic-genl-packet

GENL_PACKET_MODULE = $(GENL_PACKET_KO_NAME)_$(GENL_PACKET_VERSION)_$(CONFIGURED_ARCH).deb
$(GENL_PACKET_MODULE)_SRC_PATH = $(SRC_PATH)/$(GENL_PACKET_DIR)/$(GENL_PACKET_KO_NAME)
$(GENL_PACKET_MODULE)_DEPENDS += $(LINUX_HEADERS) $(LINUX_HEADERS_COMMON)
SONIC_DPKG_DEBS += $(GENL_PACKET_MODULE)
