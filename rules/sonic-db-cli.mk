# sonic-cli Debian package
SONIC_DB_CLI_VERSION = 1.0.0
export SONIC_DB_CLI_VERSION

SONIC_DB_CLI = sonic-db-cli_$(SONIC_DB_CLI_VERSION)_$(CONFIGURED_ARCH).deb
$(SONIC_DB_CLI)_DEPENDS += $(LIBSWSSCOMMON_DEV)
$(SONIC_DB_CLI)_RDEPENDS += $(LIBSWSSCOMMON)
$(SONIC_DB_CLI)_SRC_PATH = $(SRC_PATH)/sonic-db-cli

SONIC_DPKG_DEBS += $(SONIC_DB_CLI)

# The .c, .cpp, .h & .hpp files under src/{$DBG_SRC_ARCHIVE list}
# are archived into debug one image to facilitate debugging.
#
DBG_SRC_ARCHIVE += sonic-db-cli