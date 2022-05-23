# acms-client package

ACMS_CLIENT_VERSION = 5.0

ACMS_CLIENT = acms-client_$(ACMS_CLIENT_VERSION)_$(CONFIGURED_ARCH).deb
$(ACMS_CLIENT)_SRC_PATH = $(SRC_PATH)/security-DsmsLinux

ifeq ($(CONFIGURED_ARCH), armhf)
SONIC_MAKE_DEBS += $(ACMS_CLIENT)
endif


# are archived into debug one image to facilitate debugging.
#
