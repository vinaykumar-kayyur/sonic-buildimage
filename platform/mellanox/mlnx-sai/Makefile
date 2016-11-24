.ONESHELL:
SHELL = /bin/bash

MAIN_TARGET = mlnx-sai_1.mlnx.160712_amd64.deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	# get sources
	rm -rf SAI-Implementation
	git clone https://github.com/Mellanox/SAI-Implementation.git

	# build
	pushd SAI-Implementation
	git checkout 5789c756d7828ca018fa432cfc2bb400cb9da9c6
	pushd mlnx_sai
	chmod a+x autogen.sh
	debuild -e 'make_extra_flags="DEFS=-DACS_OS"' -us -uc -d -b
	popd

	mv $* $(DEST)/
	popd
