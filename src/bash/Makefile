SHELL = /bin/bash
.ONESHELL:
.SHELLFLAGS += -e

MAIN_TARGET = bash_$(BASH_VERSION_FULL)_$(CONFIGURED_ARCH).deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	rm -rf bash-$(BASH_VERSION_MAJOR)

	dget -u https://launchpad.net/debian/+archive/primary/+sourcefiles/bash/$(BASH_VERSION_FULL)/bash_$(BASH_VERSION_FULL).dsc

	# Apply plugin suport patches
	quilt push -a

	pushd bash-$(BASH_VERSION_MAJOR)
	# copy UT and source code.
	cp -a ../Files/. ./
	# build package
	DEB_BUILD_OPTIONS=nocheck dpkg-buildpackage -us -uc -b -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)

	popd

	mv $* $(DEST)/
