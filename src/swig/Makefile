.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = $(SWIG_BASE)
DERIVED_TARGETS = $(SWIG) $(SWIG_DBG)

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	rm -fr ./swig-$(SWIG_VERSION) *.deb
	wget -N http://deb.debian.org/debian/pool/main/s/swig/swig_3.0.12.orig.tar.gz
	wget -O swig_$(SWIG_VERSION).dsc -N http://deb.debian.org/debian/pool/main/s/swig/swig_3.0.12-2.dsc
	wget -O swig_$(SWIG_VERSION)-$(SWIG_SUBVERSION).debian.tar.xz -N http://deb.debian.org/debian/pool/main/s/swig/swig_3.0.12-2.debian.tar.xz
	dpkg-source -x swig_$(SWIG_VERSION).dsc

	pushd ./swig-$(SWIG_VERSION)
	dpkg-buildpackage -rfakeroot -b -us -uc -j$(SONIC_CONFIG_MAKE_JOBS)
	popd

	mv $(DERIVED_TARGETS) $* $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
