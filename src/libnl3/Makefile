.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = libnl-3-200_$(LIBNL3_VERSION)_$(CONFIGURED_ARCH).deb
DERIVED_TARGETS = libnl-3-dev_$(LIBNL3_VERSION)_$(CONFIGURED_ARCH).deb \
		  libnl-genl-3-200_$(LIBNL3_VERSION)_$(CONFIGURED_ARCH).deb \
		  libnl-genl-3-dev_$(LIBNL3_VERSION)_$(CONFIGURED_ARCH).deb \
		  libnl-route-3-200_$(LIBNL3_VERSION)_$(CONFIGURED_ARCH).deb \
		  libnl-route-3-dev_$(LIBNL3_VERSION)_$(CONFIGURED_ARCH).deb  \
		  libnl-nf-3-200_$(LIBNL3_VERSION)_$(CONFIGURED_ARCH).deb \
		  libnl-nf-3-dev_$(LIBNL3_VERSION)_$(CONFIGURED_ARCH).deb \
		  libnl-cli-3-200_$(LIBNL3_VERSION)_$(CONFIGURED_ARCH).deb \
		  libnl-cli-3-dev_$(LIBNL3_VERSION)_$(CONFIGURED_ARCH).deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	# Obtaining the libnl3
	rm -rf ./libnl3-$(LIBNL3_VERSION_BASE)
	wget -O libnl3_$(LIBNL3_VERSION_BASE).orig.tar.gz -N "https://sonicstorage.blob.core.windows.net/packages/libnl3_$(LIBNL3_VERSION_BASE).orig.tar.gz?sv=2015-04-05&sr=b&sig=0HR%2FrWWL54Vl07bQCEX2MNxAnuGkci4KJqxNuDrv%2BCI%3D&se=2033-09-10T22%3A29%3A11Z&sp=r"
	dpkg-source -x libnl3_$(LIBNL3_VERSION).dsc

	pushd ./libnl3-$(LIBNL3_VERSION_BASE)
	dpkg-buildpackage -rfakeroot -b -us -uc -j$(SONIC_CONFIG_MAKE_JOBS)
	popd

	mv $(DERIVED_TARGETS) $* $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
