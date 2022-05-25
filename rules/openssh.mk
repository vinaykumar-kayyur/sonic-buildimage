# openssh package

OPENSSH_VERSION = 8.4p1
OPENSSH_VERSION_FULL = ${ISC_DHCP_VERSION}-2~bpo10+1

export OPENSSH_VERSION OPENSSH_VERSION_FULL

OPENSSH_SERVER = openssh-server_$(OPENSSH_VERSION_FULL)_$(CONFIGURED_ARCH).deb
$(OPENSSH_SERVER)_SRC_PATH = $(SRC_PATH)/openssh
SONIC_MAKE_DEBS += $(OPENSSH_SERVER)

# The .c, .cpp, .h & .hpp files under src/{$DBG_SRC_ARCHIVE list}
# are archived into debug one image to facilitate debugging.
#
DBG_SRC_ARCHIVE += openssh
