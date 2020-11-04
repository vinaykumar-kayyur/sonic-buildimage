.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = $(LIBCJSON)

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	# Obtain libcjson
	rm -rf ./cJSON-$(LIBCJSON_VERSION)
	wget -N "https://github.com/DaveGamble/cJSON/archive/v$(LIBCJSON_VERSION).tar.gz"
	tar -xzf v$(LIBCJSON_VERSION).tar.gz

	cp -r debian ./cJSON-$(LIBCJSON_VERSION)
	pushd ./cJSON-$(LIBCJSON_VERSION)
	dpkg-buildpackage -rfakeroot -b -us -uc -j$(SONIC_CONFIG_MAKE_JOBS)
	popd

	mv ./$* $(DEST)/
