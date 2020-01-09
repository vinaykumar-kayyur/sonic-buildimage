SHELL = /bin/bash
.ONESHELL:
.SHELLFLAGS += -e

MAIN_TARGET = $(LIBSNMP_BASE)
DERIVED_TARGETS = \
	$(SNMPTRAPD) \
	$(SNMP) \
	$(SNMPD) \
	$(SNMP_DBG) \
	$(SNMPD_DBG) \
	$(LIBSNMP) \
	$(LIBSNMP_DBG) \
	$(LIBSNMP_DEV) \
	$(LIBSNMP_PERL) \
	$(TKMIB)

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	rm -rf net-snmp-$(SNMPD_VERSION)

	# download debian net-snmp from Azure cache. Debian packages are obtained from:
	# https://packages.debian.org/sid/libsnmp-dev
	wget -NO net-snmp_$(SNMPD_VERSION_FULL).dsc "https://sonicstorage.blob.core.windows.net/packages/net-snmp_5.8+dfsg-2.dsc?sv=2015-04-05&sr=b&sig=BXvY%2BFaOQ7utLcU%2FubM%2F1Fm%2FAxinYHjjw6iE9MzwJD4%3D&se=2033-09-16T21%3A48%3A19Z&sp=r"
	wget -NO net-snmp_$(SNMPD_VERSION).orig.tar.xz "https://sonicstorage.blob.core.windows.net/packages/net-snmp_5.8+dfsg.orig.tar.xz?sv=2015-04-05&sr=b&sig=WE5XDcTJeMib0SZC0%2Fc%2BlUDKM1ZSkJUhvXISbYz%2F4GY%3D&se=2033-09-16T21%3A48%3A49Z&sp=r"
	wget -NO net-snmp_$(SNMPD_VERSION_FULL).debian.tar.xz "https://sonicstorage.blob.core.windows.net/packages/net-snmp_5.8+dfsg-2.debian.tar.xz?sv=2015-04-05&sr=b&sig=25RA8gIphn0EyeUpZRwSTAm4z69NJrIFJyY6KkC9PMs%3D&se=2033-09-16T21%3A47%3A28Z&sp=r" 
	dpkg-source -x net-snmp_$(SNMPD_VERSION_FULL).dsc

	pushd net-snmp-$(SNMPD_VERSION)
	git init
	git add -f .
	git commit -m "unmodified snmpd source"

	# Apply patches
	stg init
	stg import -s ../patch-$(SNMPD_VERSION)/series

	fakeroot debian/rules -j$(SONIC_CONFIG_MAKE_JOBS) binary
	popd

	mv $(DERIVED_TARGETS) $* $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
