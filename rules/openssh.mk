# openssh packages

OPENSSH_VERSION = 7.9p1-10+deb10u2

export OPENSSH_VERSION

OPENSSH = openssh_$(OPENSSH_VERSION)_$(CONFIGURED_ARCH).deb
$(OPENSSH)_SRC_PATH = $(SRC_PATH)/openssh
SONIC_MAKE_DEBS += $(OPENSSH)

# The .c, .cpp, .h & .hpp files under src/{$DBG_SRC_ARCHIVE list}
# are archived into debug one image to facilitate debugging.
#
DBG_SRC_ARCHIVE += openssh
