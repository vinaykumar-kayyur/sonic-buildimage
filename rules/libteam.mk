# libteam packages

LIBTEAM = libteam5_1.26-1_amd64.deb
$(LIBTEAM)_SRC_PATH = $(SRC_PATH)/libteam
$(LIBTEAM)_DEPENDS += $(LIBNL_GENL3_DEV) $(LIBNL_CLI_DEV)
SONIC_MAKE_DEBS += $(LIBTEAM)

LIBTEAM_DEV = libteam-dev_1.26-1_amd64.deb
$(LIBTEAM_DEV)_DEPENDS += $(LIBTEAMDCT)
$(eval $(call add_derived_package,$(LIBTEAM),$(LIBTEAM_DEV)))

LIBTEAMDCT = libteamdctl0_1.26-1_amd64.deb
$(eval $(call add_derived_package,$(LIBTEAM),$(LIBTEAMDCT)))

LIBTEAM_UTILS = libteam-utils_1.26-1_amd64.deb
$(LIBTEAM_UTILS)_DEPENDS += $(LIBTEAMDCT)
$(eval $(call add_derived_package,$(LIBTEAM),$(LIBTEAM_UTILS)))
