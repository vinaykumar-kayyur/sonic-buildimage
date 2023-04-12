.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

LIBYANG_URL = https://sonicstorage.blob.core.windows.net/debian/pool/main/liby/libyang
# debian mirror should be preferred here but requires to modify version in rules.mk
# cf https://github.com/sonic-net/sonic-buildimage/pull/13381

DSC_FILE = libyang_$(LIBYANG1_FULLVERSION).dsc

DSC_FILE_URL = $(LIBYANG_URL)/$(DSC_FILE)

MAIN_TARGET = $(LIBYANG1)
DERIVED_TARGETS = $(LIBYANG1_DEV) $(LIBYANG1_DBG) $(LIBYANG1_CPP) $(LIBYANG1_CPP_DEV) $(LIBYANG1_CPP_DBG) $(YANG_TOOLS) $(LIBYANG1_TOOLS) $(LIBYANG1_TOOLS_DBG)

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
        # Obtaining the libyang
	rm -fr ./libyang-$(LIBYANG1_VERSION)

	# download debian libyang
	dget $(DSC_FILE_URL)

	pushd libyang-$(LIBYANG1_VERSION)
	sed -i 's/set(LIBYANG_MAJOR_SOVERSION 1)/set(LIBYANG_MAJOR_SOVERSION 2)/' CMakeLists.txt
	sed -i 's/libyang1/libyang2/' debian/libyang1.install
	# Enable large file support for 32-bit arch
	echo 'add_definitions(-D_FILE_OFFSET_BITS=64)' >> CMakeLists.txt

ifeq ($(CROSS_BUILD_ENVIRON), y)
	dpkg-buildpackage -rfakeroot -b -us -uc -a$(CONFIGURED_ARCH) -Pcross,nocheck -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
else
	dpkg-buildpackage -rfakeroot -b -us -uc -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
endif
	popd

	# Move the newly-built .deb packages to the destination directory
	mv $* $(DERIVED_TARGETS) $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
