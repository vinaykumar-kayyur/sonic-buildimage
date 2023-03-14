SHELL = /bin/bash
.ONESHELL:
.SHELLFLAGS += -e

MAIN_TARGET = iproute2_$(IPROUTE2_VERSION_FULL)_$(CONFIGURED_ARCH).deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	# Remove any stale files
	rm -rf iproute2-$(IPROUTE2_VERSION)

	apt-get -c ../../alt_apt_confdir/etc/apt/apt.conf source iproute2=$(IPROUTE2_VERSION_FULL)

	pushd iproute2-$(IPROUTE2_VERSION)

	patch -p1 < ../patch/0001-patch-macsec-xpn-support.patch

ifeq ($(CROSS_BUILD_ENVIRON), y)
	patch -p1 < ../patch/cross-compile-changes.patch
	dpkg-buildpackage -us -uc -b -a$(CONFIGURED_ARCH) -Pcross,nocheck -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
else
	dpkg-buildpackage -us -uc -b -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
endif
	popd

	mv $* $(DEST)/
