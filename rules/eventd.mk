# eventd package

EVENTD = eventd.0.0_$(CONFIGURED_ARCH).deb
$(EVENTD)_SRC_PATH = $(SRC_PATH)/sonic-eventd
$(EVENTD)_DEPENDS += $(LIBSWSSCOMMON)  $(LIBSWSSCOMMON_DEV)

$(EVENTD)_RDEPENDS += $(LIBSWSSCOMMON)
SONIC_DPKG_DEBS += $(EVENTD)

EVENTD_DBG = eventd-dbg_1.0.0_$(CONFIGURED_ARCH).deb
$(EVENTD_DBG)_DEPENDS += $(EVENTD)
$(EVENTD_DBG)_RDEPENDS += $(EVENTD)
$(eval $(call add_derived_package,$(EVENTD),$(EVENTD_DBG)))

# The .c, .cpp, .h & .hpp files under src/{$DBG_SRC_ARCHIVE list}
# are archived into debug one image to facilitate debugging.
#
DBG_SRC_ARCHIVE += sonic-eventd

