.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = libpam-radius-auth_$(PAM_RADIUS_VERSION)_amd64.deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	# Obtain pam_radius
	-rm -rf ./pam_radius
	git clone https://github.com/FreeRADIUS/pam_radius.git
	pushd ./pam_radius
	# This is the latest commit with Radius MPL support
	git checkout -f 149c25df84cf5cd0e9addd9346699a9ca8fdddd2

	cp -r ../debian .
	cp -r ../patches .

	# Apply patch
	git apply patches/0001-chap-support.patch

	dpkg-buildpackage -rfakeroot -b -us -uc -nc
	popd

	mv $(DERIVED_TARGETS) $* $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
