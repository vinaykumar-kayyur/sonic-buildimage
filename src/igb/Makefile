.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = igb.ko

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	rm -rf ./igb-$(IGB_DRIVER_VERSION)
	wget -O igb-$(IGB_DRIVER_VERSION).tar.gz "http://downloads.sourceforge.net/project/e1000/igb%20stable/5.3.5.4/igb-5.3.5.4.tar.gz?r=https%3A%2F%2Fsourceforge.net%2Fprojects%2Fe1000%2Ffiles%2Figb%2520stable%2F5.3.5.4%2F&ts=1482880840&use_mirror=pilotfiber"
	tar xzf igb-$(IGB_DRIVER_VERSION).tar.gz

	# Patch
	pushd ./igb-$(IGB_DRIVER_VERSION)
	patch -p1 < ../0001-add-support-for-BCM54616-phy-for-intel-igb-driver.patch

	# Build the package
	pushd src
	export BUILD_KERNEL=3.16.0-4-amd64
	make
	popd

	popd
	mv ./igb-$(IGB_DRIVER_VERSION)/src/$* $(DEST)/
