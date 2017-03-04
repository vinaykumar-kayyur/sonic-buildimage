.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = saiserver

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :

	rm -rf SAI
	git clone https://github.com/opencomputeproject/SAI
	pushd SAI
	git checkout origin/v0.9.4 -b v0.9.4

	# Build the package
	pushd test/saithrift
	
	make

	popd
	popd

	mv ./SAI/test/saithrift/$* $(DEST)/
