.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = sonic-device-data_$(SONIC_DEVICE_DATA_VERSION_FULL)_all.deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
    # Remove any stale data
    rm -rf ./device

    cp -f ../../device .

	# Build the package
	dpkg-buildpackage -rfakeroot -b -us -uc

	mv $* $(DEST)/
