SHELL = /bin/bash
.ONESHELL:
.SHELLFLAGS += -e

THRIFT_VERSION = 0.11.0
THRIFT_VERSION_FULL = $(THRIFT_VERSION)-4

MAIN_TARGET = libthrift-$(THRIFT_VERSION)_$(THRIFT_VERSION_FULL)_amd64.deb
DERIVED_TARGETS = libthrift-dev_$(THRIFT_VERSION_FULL)_amd64.deb \
		  python-thrift_$(THRIFT_VERSION_FULL)_amd64.deb \
		  thrift-compiler_$(THRIFT_VERSION_FULL)_amd64.deb

THRIFT_LINK_PRE = http://http.debian.net/debian/pool/main/t/thrift
# THRIFT_LINK_PRE = https://sonicstorage.blob.core.windows.net/packages/debian

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	rm -rf thrift-$(THRIFT_VERSION)

	wget -NO "thrift_$(THRIFT_VERSION).orig.tar.gz" "$(THRIFT_LINK_PRE)/thrift_$(THRIFT_VERSION).orig.tar.gz"
	wget -NO "thrift_$(THRIFT_VERSION_FULL).debian.tar.xz" "$(THRIFT_LINK_PRE)/thrift_$(THRIFT_VERSION_FULL).debian.tar.xz"
	wget -NO "thrift_$(THRIFT_VERSION_FULL).dsc" "$(THRIFT_LINK_PRE)/thrift_$(THRIFT_VERSION_FULL).dsc"

	dpkg-source -x thrift_$(THRIFT_VERSION_FULL).dsc
	pushd thrift-$(THRIFT_VERSION)
	CXXFLAGS="-DFORCE_BOOST_SMART_PTR" DEB_BUILD_OPTIONS=nocheck dpkg-buildpackage -d -rfakeroot -b -us -uc -j$(SONIC_CONFIG_MAKE_JOBS)
	popd

	mv $(DERIVED_TARGETS) $* $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
