SHELL = /bin/bash
.ONESHELL:
.SHELLFLAGS += -e

THRIFT_VERSION = 0.13.0

MAIN_TARGET = libthrift_$(THRIFT_VERSION)_$(CONFIGURED_ARCH).deb
DERIVED_TARGETS = libthrift-dev_$(THRIFT_VERSION)_$(CONFIGURED_ARCH).deb \
		  python-thrift_$(THRIFT_VERSION)_$(CONFIGURED_ARCH).deb \
		  thrift-compiler_$(THRIFT_VERSION)_$(CONFIGURED_ARCH).deb

THRIFT_ARCHIVE_URL = https://github.com/apache/thrift/archive/refs/tags/v$(THRIFT_VERSION).tar.gz

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	rm -rf thrift-$(THRIFT_VERSION)*

	wget "$(THRIFT_ARCHIVE_URL)" -O thrift-$(THRIFT_VERSION).tar.gz
	tar -xf thrift-$(THRIFT_VERSION).tar.gz --exclude="debian"
	cp -r debian thrift-$(THRIFT_VERSION)/debian

	pushd thrift-$(THRIFT_VERSION)

	DEB_BUILD_OPTIONS=nocheck dpkg-buildpackage -d -rfakeroot -b -us -uc -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
	popd

	mv $(DERIVED_TARGETS) $* $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
