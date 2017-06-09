# sonic-ledd (SONiC Front-panel LED control daemon) Debian package

SONIC_LEDD_VERSION = 1.0
SONIC_LEDD_VERSION_FULL = $(SONIC_LEDD_VERSION)-1

export SONIC_LEDD_VERSION SONIC_LEDD_VERSION_FULL

SONIC_LEDD = python-sonic-ledd_$(SONIC_LEDD_VERSION_FULL)_all.deb
$(SONIC_LEDD)_SRC_PATH = $(SRC_PATH)/sonic-platform-daemons/sonic-ledd
SONIC_MAKE_DEBS += $(SONIC_LEDD)
