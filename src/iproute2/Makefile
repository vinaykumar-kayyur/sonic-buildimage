SHELL = /bin/bash
.ONESHELL:
.SHELLFLAGS += -e

MAIN_TARGET = iproute2_$(IPROUTE2_VERSION)_$(CONFIGURED_ARCH).deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	# Remove any stale files
	rm -rf iproute2-$(IPROUTE2_VERSION)

	git clone https://salsa.debian.org/debian/iproute2.git iproute2-$(IPROUTE2_VERSION)

	pushd iproute2-$(IPROUTE2_VERSION)
	git checkout -b $(IPROUTE2_VERSION) debian/$(IPROUTE2_VERSION)

	stg init
	stg import -s ../patch/series

	dpkg-buildpackage -us -uc -b -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
	popd

	mv $* $(DEST)/
