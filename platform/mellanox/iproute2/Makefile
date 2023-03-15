SHELL = /bin/bash
.ONESHELL:
.SHELLFLAGS += -e

MAIN_TARGET = iproute2-mlnx_$(IPROUTE2_MLNX_VERSION_FULL)_$(CONFIGURED_ARCH).deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	# Remove any stale files
	rm -rf iproute2*

	# Download iproute2 from debian repository
	dget http://deb.debian.org/debian/pool/main/i/iproute2/iproute2_$(IPROUTE2_MLNX_VERSION_FULL).dsc

	pushd iproute2-$(IPROUTE2_MLNX_VERSION)

	# Create git repository to apply patches with stg
	git init
	git add -f *
	git commit -qm "initial commit"

	# Apply Patches
	stg init
	stg import -s ../patch/series

	# Build debian
	dpkg-buildpackage -us -uc -b -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)

	mv ../$(MAIN_TARGET) $(DEST)/
	popd
