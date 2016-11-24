SHELL = /bin/bash

MAIN_TARGET = libhiredis0.13_0.13.3-2_amd64.deb
DERIVED_TARGETS = libhiredis-dbg_0.13.3-2_amd64.deb libhiredis-dev_0.13.3-2_amd64.deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	wget -O hiredis_0.13.3.orig.tar.gz http://http.debian.net/debian/pool/main/h/hiredis/hiredis_0.13.3.orig.tar.gz
	wget -O hiredis_0.13.3-2.debian.tar.xz http://http.debian.net/debian/pool/main/h/hiredis/hiredis_0.13.3-2.debian.tar.xz
	wget -O hiredis_0.13.3-2.dsc http://http.debian.net/debian/pool/main/h/hiredis/hiredis_0.13.3-2.dsc
	dpkg-source -x hiredis_0.13.3-2.dsc
	pushd hiredis-0.13.3; fakeroot debian/rules binary; popd
	mv $* $(DERIVED_TARGETS) $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
