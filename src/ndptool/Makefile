.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e
export USE_SSL=1

MAIN_TARGET = $(LIBNDP_TOOLS)
DERIVED_TARGETS = $(LIBNDP0)

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	# Remove any stale files
	rm -rf ./libndp-$(LIBNDP_TOOLS_VERSION)

	# Get libndp-tools release, debian files
	dget -u http://http.debian.net/debian/pool/main/libn/libndp/libndp_$(LIBNDP_TOOLS_VERSION_FULL).dsc

	# Build source and Debian packages
	pushd ./libndp-$(LIBNDP_TOOLS_VERSION)
ifeq ($(CROSS_BUILD_ENVIRON), y)
	DEB_BUILD_OPTIONS="USE_SSL=1" dpkg-buildpackage -rfakeroot -d -b -us -uc -a$(CONFIGURED_ARCH) -Pcross,nocheck -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
else
	DEB_BUILD_OPTIONS="USE_SSL=1" dpkg-buildpackage -rfakeroot -d -b -us -uc -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
endif
	popd

	# Move the newly-built .deb packages to the destination directory
	mv $* $(DERIVED_TARGETS) $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)