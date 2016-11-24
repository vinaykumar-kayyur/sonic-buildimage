# libhiredis package
LIBHIREDIS = libhiredis0.13_0.13.3-2_amd64.deb
$(LIBHIREDIS)_SRC_PATH = $(SRC_PATH)/hiredis
$(LIBHIREDIS)_DEPENDS += $(REDIS_SERVER) $(REDIS_TOOLS) $(REDIS_SENTINEL)
$(LIBHIREDIS)_RDEPENDS += $(REDIS_SERVER) $(REDIS_TOOLS) $(REDIS_SENTINEL)
SONIC_MAKE_DEBS += $(LIBHIREDIS)

LIBHIREDIS_DEV = libhiredis-dev_0.13.3-2_amd64.deb
$(eval $(call add_derived_package,$(LIBHIREDIS),$(LIBHIREDIS_DEV)))

LIBHIREDIS_DBG = libhiredis-dbg_0.13.3-2_amd64.deb
$(eval $(call add_derived_package,$(LIBHIREDIS),$(LIBHIREDIS_DBG)))
