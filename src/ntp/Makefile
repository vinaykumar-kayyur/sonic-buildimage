SHELL = /bin/bash
.ONESHELL:
.SHELLFLAGS += -e

MAIN_TARGET = ntp_$(NTP_VERSION_FULL)_amd64.deb

DSC_FILE = ntp_$(NTP_VERSION_FULL).dsc

DSC_FILE_URL = https://sonicstorage.blob.core.windows.net/packages/debian/$(DSC_FILE)?sv=2015-04-05&sr=b&sig=HxuXOJsIfkj3lF2TlCShil7lFFf90Zh8oBNTfaka%2FNc%3D&se=2155-12-30T06%3A25%3A21Z&sp=r

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	rm -rf ntp-$(NTP_VERSION)
	dget -u $(DSC_FILE_URL)

	pushd ntp-$(NTP_VERSION)

	git init
	git add -f *
	git commit -m "original source files"

	stg init
	stg import -s ../patch/series

	dpkg-buildpackage -us -uc -b -j$(SONIC_CONFIG_MAKE_JOBS)
	popd

	mv $* $(DEST)/
