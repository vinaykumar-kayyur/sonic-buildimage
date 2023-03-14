.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = debootstrap_$(DEBOOTSTRAP_VERSION_FULL)_all.deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	# Remove any stale files
	rm -rf ./debootstrap-$(DEBOOTSTRAP_VERSION_FULL) ./debootstrap*.{deb,udeb,dsc}

	# Get source package
	apt-get -c ../../alt_apt_confdir/etc/apt/apt.conf source debootstrap=$(DEBOOTSTRAP_VERSION_FULL)

	# Build source and Debian packages
	pushd debootstrap-$(DEBOOTSTRAP_VERSION_FULL)
	patch -p1 -i ../proc-mount.patch
	dpkg-buildpackage -rfakeroot -b -us -uc -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
	popd

	# Move the newly-built .deb packages to the destination directory
	mv $(DERIVED_TARGETS) $* $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)

