.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = $(KDUMP_TOOLS)

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	# Remove any stale files
	rm -rf ./kdump-tools-$(KDUMP_TOOLS_VERSION)*

	# Get kdump-tools release
	dget https://deb.debian.org/debian/pool/main/k/kdump-tools/kdump-tools_$(KDUMP_TOOLS_VERSION).dsc
	pushd ./kdump-tools-$(KDUMP_TOOLS_VERSION)

	git init
	git add -f *
	git commit -m "unmodified kdump-tools source"

	# Apply patches
	stg init
	stg import -s ../patch/series

	# Build source and Debian packages
ifeq ($(CROSS_BUILD_ENVIRON), y)
	sed -i "s/dh_auto_build \-\-/dh_auto_build -- TARGET=$(CONFIGURED_ARCH)/" debian/rules
	CONFIG_SITE=/etc/dpkg-cross/cross-config.$(CONFIGURED_ARCH) LD_LIBRARY_PATH=$(CROSS_LIB_PATH) dpkg-buildpackage -rfakeroot -b -us -uc -a$(CONFIGURED_ARCH) -Pcross,nocheck -Tbinary-indep -j$(SONIC_CONFIG_MAKE_JOBS)
else
	dpkg-buildpackage -rfakeroot -b -us -uc -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
endif
	popd

	# Move the newly-built .deb packages to the destination directory
	mv $* $(DEST)/
