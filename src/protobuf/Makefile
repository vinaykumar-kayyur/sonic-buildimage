.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = protobuf_$(PROTOBUF_VERSION)_amd64.deb
$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :

	# Obtaining the protobuf
	rm -rf ./protobuf-$(PROTOBUF_VERSION)
	wget -N "https://github.com/protocolbuffers/protobuf/releases/download/v$(PROTOBUF_VERSION)/protobuf-cpp-$(PROTOBUF_VERSION).tar.gz"
	tar -xzf protobuf-cpp-$(PROTOBUF_VERSION).tar.gz
	rm -rf protobuf-cpp-$(PROTOBUF_VERSION).tar.gz
	cp debian protobuf-$(PROTOBUF_VERSION) -r

	pushd ./protobuf-$(PROTOBUF_VERSION)
	dpkg-buildpackage -rfakeroot -b -us -uc  -j$(SONIC_CONFIG_MAKE_JOBS)
	popd
	mv $* $(DEST)/
