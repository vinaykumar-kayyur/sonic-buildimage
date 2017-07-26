.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = libpam-tacplus_$(PAM_TACPLUS_VERSION)_amd64.deb
DERIVED_TARGETS = libtac2_$(PAM_TACPLUS_VERSION)_amd64.deb \
		  libtac-dev_$(PAM_TACPLUS_VERSION)_amd64.deb \
		  libnss-tacplus_$(PAM_TACPLUS_VERSION)_amd64.deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	# Obtain pam_tacplus
	rm -rf ./pam_tacplus
	git clone https://github.com/jeroennijhof/pam_tacplus.git 
	pushd ./pam_tacplus
	git checkout -f 11ac166

	# Apply patch
	git apply ../0001-Add-config-for-source-ip-address.patch
	git apply ../0002-Add-nss-tacplus.patch

	dpkg-buildpackage -rfakeroot -b -us -uc
	popd

	mv $(DERIVED_TARGETS) $* $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
