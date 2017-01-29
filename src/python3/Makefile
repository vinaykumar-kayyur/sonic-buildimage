.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

PYTHON_VER=3.6.0
PYTHON_DEB_VER=1
PYTHON_PNAME=python3.6

MAIN_TARGET = lib$(PYTHON_PNAME)-minimal_$(PYTHON_VER)-$(PYTHON_DEB_VER)_amd64.deb
DERIVED_TARGETS = lib$(PYTHON_PNAME)-stdlib_$(PYTHON_VER)-$(PYTHON_DEB_VER)_amd64.deb \
				  lib$(PYTHON_PNAME)_$(PYTHON_VER)-$(PYTHON_DEB_VER)_amd64.deb \
				  $(PYTHON_PNAME)-minimal_$(PYTHON_VER)-$(PYTHON_DEB_VER)_amd64.deb \
				  $(PYTHON_PNAME)_$(PYTHON_VER)-$(PYTHON_DEB_VER)_amd64.deb \
				  lib$(PYTHON_PNAME)-dev_$(PYTHON_VER)-$(PYTHON_DEB_VER)_amd64.deb
				  #$(PYTHON_PNAME)-dev_$(PYTHON_VER)-$(PYTHON_DEB_VER)_amd64.deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	## Obtaining the python3
	wget http://http.debian.net/debian/pool/main/p/$(PYTHON_PNAME)/$(PYTHON_PNAME)_$(PYTHON_VER).orig.tar.xz -O $(PYTHON_PNAME)_$(PYTHON_VER).orig.tar.xz
	wget http://http.debian.net/debian/pool/main/p/$(PYTHON_PNAME)/$(PYTHON_PNAME)_$(PYTHON_VER)-$(PYTHON_DEB_VER).debian.tar.xz -O $(PYTHON_PNAME)_$(PYTHON_VER)-$(PYTHON_DEB_VER).debian.tar.xz
	wget http://http.debian.net/debian/pool/main/p/$(PYTHON_PNAME)/$(PYTHON_PNAME)_$(PYTHON_VER)-$(PYTHON_DEB_VER).dsc -O $(PYTHON_PNAME)_$(PYTHON_VER)-$(PYTHON_DEB_VER).dsc
	
	## Build
	dpkg-source -x $(PYTHON_PNAME)_$(PYTHON_VER)-$(PYTHON_DEB_VER).dsc
	pushd $(PYTHON_PNAME)-$(PYTHON_VER)
	sudo apt-get install devscripts
	mk-build-deps
	sudo dpkg -i $(PYTHON_PNAME)-build-deps_$(PYTHON_VER)-$(PYTHON_DEB_VER)_amd64.deb || sudo apt-get install -f
	dpkg-buildpackage -us -uc -b
	popd
	
	cp $(DERIVED_TARGETS) $* $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
