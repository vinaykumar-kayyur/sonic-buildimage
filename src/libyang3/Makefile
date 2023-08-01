.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = $(LIBYANG3)
DERIVED_TARGETS = $(LIBYANG3_DEV)

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	# Obtaining the libyang
	rm -fr ./libyang-$(LIBYANG3_VERSION)
	git clone https://github.com/CESNET/libyang.git libyang-$(LIBYANG3_VERSION)
	#wget -Olibyang2_2.0.231.orig.tar.gz https://github.com/CESNET/libyang/releases/tag/v2.0.231
	cp -r debian/ libyang-$(LIBYANG3_VERSION)/
	pushd libyang-$(LIBYANG3_VERSION)
	git checkout tags/v2.0.231 -b libyang
	#dpkg-source -b .

	# Apply patch series
	#stg init
	#stg import -s ../patch/series

ifeq ($(CROSS_BUILD_ENVIRON), y)
	dpkg-buildpackage -rfakeroot -b -us -uc -a$(CONFIGURED_ARCH) -Pcross,nocheck -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
else
	dpkg-buildpackage -rfakeroot -b -us -uc -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
endif
	popd

	mv $(DERIVED_TARGETS) $* $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
