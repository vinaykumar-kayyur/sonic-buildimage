# sonic-cli packages

CLI_VERSION = 1.0.0

SONIC_CLI = sonic-cli-$(CLI_VERSION)-Linux.deb
$(SONIC_CLI)_DEPENDS += $(LIBTAC_DEV)
$(SONIC_CLI)_SRC_PATH = $(SRC_PATH)/sonic-utilities/sonic-cli
SONIC_CMAKE_DEBS += $(SONIC_CLI)
