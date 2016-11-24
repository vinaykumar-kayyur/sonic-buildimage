.ONESHELL:
SHELL = /bin/bash

MAIN_TARGET = initramfs-tools_0.120_all.deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	# Obtaining the initramfs-tools
	rm -rf ./initramfs-tools
	git clone --branch v0.120 https://anonscm.debian.org/git/kernel/initramfs-tools.git ./initramfs-tools

	# Patch
	pushd ./initramfs-tools
	patch -p1 < ../loopback-file-system-support.patch

	# Build the package
	rm -f debian/*.debhelper.log
	dpkg-buildpackage -rfakeroot -b -us -uc
	popd

	mv $* $(DEST)/
