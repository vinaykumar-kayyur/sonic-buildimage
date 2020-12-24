.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = $(LIBYANG1)
DERIVED_TARGETS = $(LIBYANG1_DEV) $(LIBYANG1_DBG) $(LIBYANG1_CPP) $(LIBYANG1_CPP_DEV) $(LIBYANG1_CPP_DBG) $(YANG_TOOLS) $(LIBYANG1_TOOLS) $(LIBYANG1_TOOLS_DBG)

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
        # Obtaining the libyang
	rm -fr ./libyang-1.0.184
	wget -NO libyang_1.0.184-2.dsc http://deb.debian.org/debian/pool/main/liby/libyang/libyang_1.0.184-2.dsc
	wget -NO libyang_1.0.184.orig.tar.gz http://deb.debian.org/debian/pool/main/liby/libyang/libyang_1.0.184.orig.tar.gz
	wget -NO libyang_1.0.184-2.debian.tar.xz http://deb.debian.org/debian/pool/main/liby/libyang/libyang_1.0.184-2.debian.tar.xz
	dpkg-source -x libyang_1.0.184-2.dsc
	pushd libyang-1.0.184
	sed -i 's/set(LIBYANG_MAJOR_SOVERSION 1)/set(LIBYANG_MAJOR_SOVERSION 2)/' CMakeLists.txt
	sed -i 's/libyang1/libyang2/' debian/libyang1.install
	dpkg-buildpackage -rfakeroot -b -us -uc -j$(SONIC_CONFIG_MAKE_JOBS)
	popd
	mv $* $(DEST)/
	mv $(DERIVED_TARGETS) $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
