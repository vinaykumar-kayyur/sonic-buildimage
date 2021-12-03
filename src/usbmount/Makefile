.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = usbmount_0.0.24_all.deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	# Obtaining usbmount
	rm -rf ./usbmount
	git clone https://github.com/rbrito/usbmount.git usbmount
	pushd ./usbmount
	git checkout master

	dpkg-buildpackage -rfakeroot -b -us -uc -j$(SONIC_CONFIG_MAKE_JOBS)
	popd

	mv $(DERIVED_TARGETS) $* $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
