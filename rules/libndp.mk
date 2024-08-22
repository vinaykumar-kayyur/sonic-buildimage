# libndp-tools package, in bookworm this can probably be removed
# Force debian 12 package as debian 11 doesn't support 
# required libndp-tools version.

LIBNDP_TOOLS_VERSION = 1.8
LIBNDP_TOOLS_VERSION_FULL = ${LIBNDP_TOOLS_VERSION}-1+deb12u1

export LIBNDP_TOOLS_VERSION LIBNDP_TOOLS_VERSION_FULL

LIBNDP_TOOLS = libndp-tools_$(LIBNDP_TOOLS_VERSION_FULL)_amd64.deb
$(LIBNDP_TOOLS)_SRC_PATH = $(SRC_PATH)/ndptool
SONIC_MAKE_DEBS += $(LIBNDP_TOOLS)

export LIBNDP_TOOLS