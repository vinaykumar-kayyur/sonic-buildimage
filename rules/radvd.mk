# radvd package

RADVD_VERSION = 2.17-2~bpo9+1

export RADVD_VERSION

RADVD = radvd_$(RADVD_VERSION)_amd64.deb
$(RADVD)_SRC_PATH = $(SRC_PATH)/radvd
SONIC_MAKE_DEBS += $(RADVD)
SONIC_STRETCH_DEBS += $(RADVD)

RADVD_DBG = radvd-dbgsym_$(RADVD_VERSION)_amd64.deb
$(eval $(call add_derived_package,$(RADVD),$(RADVD_DBG)))
