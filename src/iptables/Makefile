.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = $(IPTABLES)
DERIVED_TARGETS = libip4tc0_$(IPTABLES_VERSION_FULL)_$(CONFIGURED_ARCH).deb \
		  libip6tc0_$(IPTABLES_VERSION_FULL)_$(CONFIGURED_ARCH).deb \
		  libiptc0_$(IPTABLES_VERSION_FULL)_$(CONFIGURED_ARCH).deb \
		  libxtables12_$(IPTABLES_VERSION_FULL)_$(CONFIGURED_ARCH).deb

DSC_FILE = iptables_$(IPTABLES_VERSION_FULL).dsc
ORIG_FILE = iptables_$(IPTABLES_VERSION).orig.tar.bz2
DEBIAN_FILE = iptables_$(IPTABLES_VERSION_FULL).debian.tar.xz

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	# Remove any stale files
	rm -rf ./iptables-$(IPTABLES_VERSION)

	# Get iptables release
	apt-get -c ../../alt_apt_confdir/etc/apt/apt.conf source iptables=$(IPTABLES_VERSION_FULL)

	pushd iptables-$(IPTABLES_VERSION)
	git init
	git add -f *
	git commit -m "unmodified iptables source"

	# Apply patches
	stg init
	stg import -s ../patch/series

	# Build source and Debian packages
ifeq ($(CROSS_BUILD_ENVIRON), y)
	dpkg-buildpackage -rfakeroot -b -us -uc -a$(CONFIGURED_ARCH) -Pcross,nocheck -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
else
	dpkg-buildpackage -rfakeroot -b -us -uc -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
endif
	popd

	# Move the newly-built .deb packages to the destination directory
	mv $(DERIVED_TARGETS) $* $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
