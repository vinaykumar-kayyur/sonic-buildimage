.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = wpasupplicant_$(WPASUPPLICANT_VERSION)_$(CONFIGURED_ARCH).deb
DERIVED_TARGETS = wpasupplicant-dbgsym_$(WPASUPPLICANT_VERSION)_$(CONFIGURED_ARCH).deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	# Remove any stale files
	rm -rf ./wpa

	# Clone wpa repo
#	git clone https://github.com/Azure/sonic-wpa-supplicant.git
#	pushd ./sonic-wpa-supplicant/wpa_supplicant
#
#	# Reset HEAD to the commit of the proper tag
#	# NOTE: Using "git checkout <tag_name>" here detaches our HEAD,
#	# which stg doesn't like, so we use this method instead
#	# NOTE: For some reason, tags in the Debian monit repo are prefixed with "1%"
#	git checkout wpa/$(WPASUPPLICANT_VERSION)
#
#	# Build source and Debian packages
#	cp defconfig .config
#	make -j$(SONIC_CONFIG_MAKE_JOBS)
	
	git clone https://salsa.debian.org/debian/wpa.git
	pushd ./wpa
	git reset --hard debian/2\%$(WPASUPPLICANT_VERSION)
	dpkg-buildpackage -rfakeroot -b -us -uc -j$(SONIC_CONFIG_MAKE_JOBS)

	popd

	# Move the newly-built .deb packages to the destination directory
	mv $(DERIVED_TARGETS) $* $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
