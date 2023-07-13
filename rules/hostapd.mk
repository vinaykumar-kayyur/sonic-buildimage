# wpa package

HOSTAPD_VERSION = 2.9.0-14
HOSTAPD_PKG_NAME = hostapd

export HOSTAPD_VERSION

HOSTAPD = hostapd_$(HOSTAPD_VERSION)_$(CONFIGURED_ARCH).deb
$(HOSTAPD)_SRC_PATH = $(SRC_PATH)/hostapd
$(HOSTAPD)_DEPENDS += $(LIBSWSSCOMMON_DEV) $(LIBNL3_DEV) $(LIBNL_GENL3_DEV) $(LIBNL_ROUTE3_DEV)
$(HOSTAPD)_RDEPENDS += $(LIBSWSSCOMMON) $(LIBNL3) $(LIBNL_GENL3) $(LIBNL_ROUTE3)
SONIC_MAKE_DEBS += $(HOSTAPD)

HOSTAPD_DBG = hostapd-dbgsym_$(HOSTAPD_VERSION)_$(CONFIGURED_ARCH).deb
$(eval $(call add_derived_package,$(HOSTAPD),$(HOSTAPD_DBG)))

# The .c, .cpp, .h & .hpp files under src/{$DBG_SRC_ARCHIVE list}
# are archived into debug one image to facilitate debugging.
#
DBG_SRC_ARCHIVE += hostapd
