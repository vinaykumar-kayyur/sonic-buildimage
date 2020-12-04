SHELL = /bin/bash
.ONESHELL:
.SHELLFLAGS += -e

MAIN_TARGET := libebpf_$(EBPF_VERSION)_$(CONFIGURED_ARCH).deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :

	pushd src
	[ ! -f ./autogen.sh ] || ./autogen.sh 
	dpkg-buildpackage -us -uc -b -j$(SONIC_CONFIG_MAKE_JOBS)
	popd

	mv $(LIBEBPF_DBG) $* $(DEST)/
