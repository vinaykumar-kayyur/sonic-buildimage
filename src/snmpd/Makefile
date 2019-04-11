SHELL = /bin/bash
.ONESHELL:
.SHELLFLAGS += -e

MAIN_TARGET = libsnmp-base_$(SNMPD_VERSION_FULL)_all.deb
DERIVED_TARGETS = snmptrapd_$(SNMPD_VERSION_FULL)_amd64.deb \
		  snmp_$(SNMPD_VERSION_FULL)_amd64.deb \
		  snmpd_$(SNMPD_VERSION_FULL)_amd64.deb \
		  libsnmp30_$(SNMPD_VERSION_FULL)_amd64.deb \
		  libsnmp30-dbg_$(SNMPD_VERSION_FULL)_amd64.deb \
		  libsnmp-dev_$(SNMPD_VERSION_FULL)_amd64.deb \
		  libsnmp-perl_$(SNMPD_VERSION_FULL)_amd64.deb \
		  python-netsnmp_$(SNMPD_VERSION_FULL)_amd64.deb \
		  tkmib_$(SNMPD_VERSION_FULL)_all.deb

SNMP_URL = http://ftp.debian.org/debian/pool/main/n/net-snmp

DSC_FILE = net-snmp_$(SNMPD_VERSION_FULL).dsc
ORIG_FILE = net-snmp_$(SNMPD_VERSION).orig.tar.xz
DEBIAN_FILE = net-snmp_$(SNMPD_VERSION_FULL).debian.tar.xz

DSC_FILE_URL = $(SNMP_URL)/$(DSC_FILE)
ORIG_FILE_URL = $(SNMP_URL)/$(ORIG_FILE)
DEBIAN_FILE_URL = $(SNMP_URL)/$(DEBIAN_FILE)

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	rm -rf net-snmp-$(SNMPD_VERSION)

	# download debian net-snmp
	wget -O "$(DSC_FILE)" $(DSC_FILE_URL)
	wget -O "$(ORIG_FILE)" $(ORIG_FILE_URL)
	wget -O "$(DEBIAN_FILE)" $(DEBIAN_FILE_URL)
	dpkg-source -x net-snmp_$(SNMPD_VERSION_FULL).dsc

	pushd net-snmp-$(SNMPD_VERSION)
	git init
	git add -f *
	git commit -m "unmodified snmpd source"

	# Apply patches
	stg init
	stg import -s ../patch-$(SNMPD_VERSION)/series

	fakeroot debian/rules -j$(SONIC_CONFIG_MAKE_JOBS) binary
	popd

	mv $(DERIVED_TARGETS) $* $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)

