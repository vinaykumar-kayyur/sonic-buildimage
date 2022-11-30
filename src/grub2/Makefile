SHELL = /bin/bash
.ONESHELL:
.SHELLFLAGS += -e

MAIN_TARGET = grub-efi-$(CONFIGURED_ARCH)-bin_$(GRUB2_FULL_VERSION)_$(CONFIGURED_ARCH).deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	rm -rf grub2-$(GRUB2_VERSION)
	wget -O grub2_$(GRUB2_VERSION).orig.tar.xz http://deb.debian.org/debian/pool/main/g/grub2/grub2_$(GRUB2_VERSION).orig.tar.xz
	wget -O grub2_$(GRUB2_FULL_VERSION).dsc http://deb.debian.org/debian/pool/main/g/grub2/grub2_$(GRUB2_FULL_VERSION).dsc
	wget -O grub2_$(GRUB2_FULL_VERSION).debian.tar.xz http://deb.debian.org/debian/pool/main/g/grub2/grub2_$(GRUB2_FULL_VERSION).debian.tar.xz
	# wget -O grub2_$(GRUB2_VERSION).orig.tar.xz.asc http://deb.debian.org/debian/pool/main/g/grub2/grub2_$(GRUB2_VERSION).orig.tar.xz.asc

	dpkg-source -x grub2_$(GRUB2_FULL_VERSION).dsc

	pushd grub2-$(GRUB2_VERSION)

	DEB_BUILD_OPTIONS=nocheck dpkg-buildpackage -us -uc -b -a$(CONFIGURED_ARCH) -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
	popd

	# Copy monolithic efi binary for secureboot
	mv $* $(DEST)/
