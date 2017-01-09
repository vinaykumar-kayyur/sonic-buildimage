.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = cavm_platform_modules.deb
DEB_BUILD_DIR = cavm-platform-modules-deb
KVERSION = linux-3.16.36

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	# get sources
	rm -rf SONiC
	git clone https://github.com/edge-core/SONiC.git

	# build
	pushd SONiC/AS7512-32X/module/

	KERNEL_SRC=/sonic/src/sonic-linux-kernel/$(KVERSION)/debian/build/build_amd64_none_amd64 make
	popd
	mkdir -p $(DEB_BUILD_DIR)/lib/modules/$(KVERSION)

	cp SONiC/AS7512-32X/module/*.ko $(DEB_BUILD_DIR)/lib/modules/$(KVERSION)
	cp -r DEBIAN $(DEB_BUILD_DIR)
	dpkg-deb -b  $(DEB_BUILD_DIR) $(MAIN_TARGET)

	mv $(MAIN_TARGET) $(DEST)/
	rm -rf $(DEB_BUILD_DIR)

