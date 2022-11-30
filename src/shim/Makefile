SHELL = /bin/bash
.ONESHELL:
.SHELLFLAGS += -e

MAIN_TARGET = shim-unsigned_$(SHIM_FULL_VERSION)_$(CONFIGURED_ARCH).deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	#rm -rf shim-$(SHIM_VERSION)
	#wget -O shim_$(SHIM_VERSION).orig.tar.bz2 http://deb.debian.org/debian/pool/main/s/shim/shim_$(SHIM_VERSION).orig.tar.bz2
	#wget -O shim_$(SHIM_FULL_VERSION).dsc http://deb.debian.org/debian/pool/main/s/shim/shim_$(SHIM_FULL_VERSION).dsc
	#wget -O shim_$(SHIM_FULL_VERSION).debian.tar.xz http://deb.debian.org/debian/pool/main/s/shim/shim_$(SHIM_FULL_VERSION).debian.tar.xz

	#dpkg-source -x shim_$(SHIM_FULL_VERSION).dsc

	pushd shim-$(SHIM_VERSION)

	DEB_BUILD_OPTIONS=nocheck dpkg-buildpackage -us -uc -b -a$(CONFIGURED_ARCH) -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
	popd

	# Copy monolithic efi binary for secureboot
	mv $* $(DEST)/
