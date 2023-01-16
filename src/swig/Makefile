.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = $(SWIG_BASE)
DERIVED_TARGETS = $(SWIG) $(SWIG_DBG)

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	rm -fr ./swig-$(SWIG_VERSION) *.deb
	apt-get -c ../../alt_apt_confdir/etc/apt/apt.conf source swig=$(SWIG_VERSION_FULL)

	pushd ./swig-$(SWIG_VERSION)
ifeq ($(CROSS_BUILD_ENVIRON), y)
	dpkg-buildpackage -rfakeroot -b -us -uc -a$(CONFIGURED_ARCH) -Pcross,nocheck -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
else
	dpkg-buildpackage -rfakeroot -b -us -uc -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
endif
	popd

	mv $(DERIVED_TARGETS) $* $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
