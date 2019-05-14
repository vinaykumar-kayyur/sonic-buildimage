.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = $(LIBYANG)
DERIVED_TARGETS = $(LIBYANG_DEV)
DEPS = $(DEST)/$(SWIG_BASE) $(DEST)/$(SWIG)

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	rm -fr ./libyang-$(LIBYANG_VERSION)
	sudo dpkg -i $(DEPS)
	wget -N http://deb.debian.org/debian/pool/main/liby/libyang/libyang_0.16.105.orig.tar.gz
	wget -O libyang_$(LIBYANG_VERSION).dsc -N http://deb.debian.org/debian/pool/main/liby/libyang/libyang_0.16.105-1.dsc
	wget -O libyang_$(LIBYANG_VERSION)-$(LIBYANG_SUBVERSION).debian.tar.xz -N http://deb.debian.org/debian/pool/main/liby/libyang/libyang_0.16.105-1.debian.tar.xz
	dpkg-source -x libyang_$(LIBYANG_VERSION).dsc

	pushd ./libyang-$(LIBYANG_VERSION)
	dpkg-buildpackage -rfakeroot -b -us -uc -j$(SONIC_CONFIG_MAKE_JOBS)
	popd

	mv $(DERIVED_TARGETS) $* $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
