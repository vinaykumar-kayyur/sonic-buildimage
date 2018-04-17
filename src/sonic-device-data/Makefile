.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = sonic-device-data_$(SONIC_DEVICE_DATA_VERSION_FULL)_all.deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	pushd ./src

	# Remove any stale data
	rm -rf ./device

	# Create a new dir and copy all ONIE-platform-string-named dirs into it
	mkdir ./device
	cp -r ../../../device/*/* ./device/

	# Execute Broadcom config file test
	pushd ../tests/
	for f in `find ../../../device -name "*.config.bcm"`; do
		echo ./config_checker $$f
		./config_checker $$f
	done
	popd

	# Build the package
	dpkg-buildpackage -rfakeroot -b -us -uc

	popd

	mv $* $(DEST)/
