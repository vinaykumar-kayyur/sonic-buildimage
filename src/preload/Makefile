.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = libgcovpreload_$(GCOV_PRELOAD_VERSION_FULL)_$(CONFIGURED_ARCH).deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	pushd gcov_preload
	dpkg-buildpackage -rfakeroot -d -b -us -uc -j$(SONIC_CONFIG_MAKE_JOBS)
	popd
	mv $* $(DEST)/
