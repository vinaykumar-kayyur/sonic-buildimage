# libpam-tacplus packages

PAM_TACPLUS_VERSION = 1.4.1-1

LIBTAC2 = libtac2_$(PAM_TACPLUS_VERSION)_amd64.deb
$(LIBTAC2)_SRC_PATH = $(SRC_PATH)/tacacs/sonic-pam-tacplus
SONIC_DPKG_DEBS += $(LIBTAC2)

LIBPAM_TACPLUS = libpam-tacplus_$(PAM_TACPLUS_VERSION)_amd64.deb
$(LIBPAM_TACPLUS)_RDEPENDS += $(LIBTAC2)
$(LIBPAM_TACPLUS)_SRC_PATH = $(SRC_PATH)/tacacs/sonic-pam-tacplus
SONIC_DPKG_DEBS += $(LIBPAM_TACPLUS)
$(eval $(call add_derived_package,$(LIBTAC2),$(LIBPAM_TACPLUS)))

LIBTAC_DEV = libtac-dev_$(PAM_TACPLUS_VERSION)_amd64.deb
$(LIBTAC_DEV)_RDEPENDS += $(LIBTAC2)
$(eval $(call add_derived_package,$(LIBTAC2),$(LIBTAC_DEV)))

# libnss-tacplus packages

NSS_TACPLUS_VERSION = 1.0.3-1

LIBNSS_TACPLUS = libnss-tacplus_$(NSS_TACPLUS_VERSION)_amd64.deb
$(LIBNSS_TACPLUS)_DEPENDS += $(LIBTAC_DEV)
$(LIBNSS_TACPLUS)_RDEPENDS += $(LIBTAC2)
$(LIBNSS_TACPLUS)_SRC_PATH = $(SRC_PATH)/tacacs/sonic-nss-tacplus
SONIC_DPKG_DEBS += $(LIBNSS_TACPLUS)
$(eval $(call add_derived_package,$(LIBTAC2)))

