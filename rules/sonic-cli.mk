# sonic-cli Debian package
SONIC_CLI_VERSION = 1.0.0
export SONIC_CLI_VERSION

SONIC_CLI = sonic-cli_$(SONIC_CLI_VERSION)_$(CONFIGURED_ARCH).deb
$(SONIC_CLI)_DEPENDS += $(LIBSWSSCOMMON_DEV)
$(SONIC_CLI)_RDEPENDS += $(LIBSWSSCOMMON)
$(SONIC_CLI)_SRC_PATH = $(SRC_PATH)/sonic-cli

SONIC_MAKE_DEBS += $(SONIC_CLI)

# The .c, .cpp, .h & .hpp files under src/{$DBG_SRC_ARCHIVE list}
# are archived into debug one image to facilitate debugging.
#
DBG_SRC_ARCHIVE += sonic-cli