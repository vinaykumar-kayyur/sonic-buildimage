# bond package

BOND_VERSION = 8.0.1

BOND = libbond_$(BOND_VERSION)-1_$(CONFIGURED_ARCH).deb
$(BOND)_SRC_PATH = $(SRC_PATH)/bond
ifneq ($(CONFIGURED_ARCH), amd64)
SONIC_MAKE_DEBS += $(BOND)
endif

# Export these variables so they can be used in a sub-make
export BOND_VERSION
export BOND
