.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = libmpdec2_$(MPDECIMAL_VERSION_FULL)_$(CONFIGURED_ARCH).deb
DERIVED_TARGETS = libmpdec-dev_$(MPDECIMAL_VERSION_FULL)_$(CONFIGURED_ARCH).deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	rm -rf mpdecimal-$(MPDECIMAL_VERSION)

	apt-get -c ../../alt_apt_confdir/etc/apt/apt.conf source mpdecimal=$(MPDECIMAL_VERSION_FULL)
	pushd mpdecimal-$(MPDECIMAL_VERSION)
ifeq ($(CROSS_BUILD_ENVIRON), y)
	dpkg-buildpackage -us -uc -b -a$(CONFIGURED_ARCH) -Pcross,nocheck -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
else
	dpkg-buildpackage -us -uc -b -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
endif
	popd

	mv $* $(DERIVED_TARGETS) $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
