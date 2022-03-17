.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = $(LIBYANG)
DERIVED_TARGETS = $(LIBYANG_DEV) $(LIBYANG_DBG) $(LIBYANG_PY3) $(LIBYANG_CPP)

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
        # Obtaining the libyang
	rm -fr ./libyang-$(LIBYANG_VERSION)
	git clone https://github.com/CESNET/libyang.git libyang-$(LIBYANG_VERSION)
	pushd libyang-$(LIBYANG_VERSION)
	git checkout tags/v1.0-r4 -b libyang
	# Apply patch series
	stg init
	stg import -s ../patch/series
 
ifeq ($(CROSS_BUILD_ENVIRON), y)
	patch -p1 < ../patch/cross-compile-changes.patch
	sed -i "s/cmake/CC=$$CROSS_CC CXX=$$CROSS_CXX cmake/g" packages/debian.rules.in
	sed -i "/Architecture/ s/any/$$CONFIGURED_ARCH/; /Build-Depends/ s/gcc//" packages/debian.control.in
endif

	mkdir build
	pushd build
ifeq ($(CROSS_BUILD_ENVIRON), y)
	CC=$(CROSS_CC) CXX=$(CROSS_CXX) cmake ..
	make CC=$(CROSS_CC) CXX=$(CROSS_CXX) build-deb
else
	cmake ..
	make build-deb
endif

	pushd debs
	mv $* $(DEST)/
	mv $(DERIVED_TARGETS) $(DEST)/
	popd

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
