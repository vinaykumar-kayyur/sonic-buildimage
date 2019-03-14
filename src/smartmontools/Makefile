SHELL = /bin/bash
.ONESHELL:
.SHELLFLAGS += -e


MAIN_TARGET = smartmontools_$(SMARTMONTOOLS_VERSION_FULL)_amd64.deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	rm -rf smartmontools-$(SMARTMONTOOLS_VERSION_MAJOR)
	wget -O smartmontools_$(SMARTMONTOOLS_VERSION_MAJOR).orig.tar.gz -N "http://deb.debian.org/debian/pool/main/s/smartmontools/smartmontools_$(SMARTMONTOOLS_VERSION_MAJOR).orig.tar.gz"
	wget -O smartmontools_$(SMARTMONTOOLS_VERSION_FULL).dsc -N "http://deb.debian.org/debian/pool/main/s/smartmontools/smartmontools_$(SMARTMONTOOLS_VERSION_FULL).dsc"
	wget -O smartmontools_$(SMARTMONTOOLS_VERSION_FULL).debian.tar.xz -N "http://deb.debian.org/debian/pool/main/s/smartmontools/smartmontools_$(SMARTMONTOOLS_VERSION_FULL).debian.tar.xz"
	dpkg-source -x smartmontools_$(SMARTMONTOOLS_VERSION_FULL).dsc

	pushd smartmontools-$(SMARTMONTOOLS_VERSION_MAJOR)
	dpkg-buildpackage -us -uc -b -j$(SONIC_CONFIG_MAKE_JOBS)
	popd

	mv $* $(DEST)/
