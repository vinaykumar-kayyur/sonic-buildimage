.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = socat_$(SOCAT_VERSION_FULL)_$(CONFIGURED_ARCH).deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	# Remove any stale files
	rm -rf ./socat-$(SOCAT_VERSION)

	# Get source package
	apt-get -c ../../alt_apt_confdir/etc/apt/apt.conf source socat=$(SOCAT_VERSION_FULL)

	# Build source and Debian packages
	pushd socat-$(SOCAT_VERSION)
	patch -p0 < ../enable_readline.patch
ifeq ($(CROSS_BUILD_ENVIRON), y)
	dpkg-buildpackage -rfakeroot -b -us -uc -a$(CONFIGURED_ARCH) -Pcross,nocheck -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
else
	DEB_BUILD_OPTIONS=nocheck dpkg-buildpackage -rfakeroot -Pnocheck -b -us -uc -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
endif
	popd

	# Move the newly-built .deb packages to the destination directory
	mv $(DERIVED_TARGETS) $* $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)

