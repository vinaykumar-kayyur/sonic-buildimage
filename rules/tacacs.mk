# libpam-tacplus packages

PAM_TACPLUS_VERSION = 1.4.1-1

export PAM_TACPLUS_VERSION

LIBPAM_TACPLUS = libpam-tacplus_$(PAM_TACPLUS_VERSION)_amd64.deb
$(LIBPAM_TACPLUS)_SRC_PATH = $(SRC_PATH)/tacacs
SONIC_MAKE_DEBS += $(LIBPAM_TACPLUS)

LIBTAC2 = libtac2_$(PAM_TACPLUS_VERSION)_amd64.deb
$(eval $(call add_derived_package,$(LIBPAM_TACPLUS),$(LIBTAC2)))

LIBTAC_DEV = libtac-dev_$(PAM_TACPLUS_VERSION)_amd64.deb
$(eval $(call add_derived_package,$(LIBPAM_TACPLUS),$(LIBTAC_DEV)))

LIBNSS_TACPLUS = libnss-tacplus_$(PAM_TACPLUS_VERSION)_amd64.deb
$(LIBNSS_TACPLUS)_RDEPENDS += $(LIBTAC2)
$(eval $(call add_derived_package,$(LIBPAM_TACPLUS),$(LIBNSS_TACPLUS)))
