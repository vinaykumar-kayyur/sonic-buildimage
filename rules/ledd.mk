# ledd (SONiC Front-panel LED control daemon) Debian package

LEDD_VERSION = 1.0
LEDD_VERSION_FULL = $(LEDD_VERSION)-1

export LEDD_VERSION LEDD_VERSION_FULL

LEDD = ledd_$(LEDD_VERSION_FULL)_all.deb
$(LEDD)_SRC_PATH = $(SRC_PATH)/sonic-platform-daemons/sonic-ledd
SONIC_MAKE_DEBS += $(LEDD)
