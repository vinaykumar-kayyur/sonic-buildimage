.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = audisp-tacplus_$(AUDISP_TACPLUS_VERSION)_$(CONFIGURED_ARCH).deb
DERIVED_TARGETS = libtac2_$(PAM_TACPLUS_VERSION)_$(CONFIGURED_ARCH).deb \
		  libtac-dev_$(PAM_TACPLUS_VERSION)_$(CONFIGURED_ARCH).deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	# Obtain audisp-tacplus
	rm -rf ./audisp-tacplus

	git clone https://github.com/daveolson53/audisp-tacplus.git

	# checkout by sha1
	pushd ./pam_tacplus
	git checkout 559c9f22edd4f2dea0ecedffb3ad9502b12a75b6
	popd

	# Apply plugin suport patches
	quilt push -a

	# build package
	pushd ./pam_tacplus
	dpkg-buildpackage -rfakeroot -b -us -uc -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
	popd

	mv $(DERIVED_TARGETS) $* $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
