#!/bin/sh

cd $(dirname $0)
cd ../src/isc-dhcp/

# retrieve current version values of dhcpd from makefile
eval $(grep '^ISC_DHCP_VERSION =' ../../rules/isc-dhcp.mk | sed -e 's/ *= */=/')
eval $(grep '^ISC_DHCP_VERSION_FULL =' ../../rules/isc-dhcp.mk | sed -e 's/ *= */=/')
# before parsing with awk regex, apply backslash to dots to avoid ambiguous detection
ISC_DHCP_VERSION=$(echo $ISC_DHCP_VERSION | sed 's/\./\\./g')
# next, use eval and awk to parse 'apt-cache showsrc' output and retrieve available versions from debian repositories
# pipe result to a unique and version sort (-u and -V options) and tail to get the last version
eval $(echo "version=\$(apt-cache -c ../../alt_apt_confdir/etc/apt/apt.conf showsrc isc-dhcp | awk  -F\"[' ]\" '/^Version: $ISC_DHCP_VERSION[^0-9]*/{print \$2}' | sort -uV |tail -1)")
# previous line will be interpreted as follow (modulo version changes)
# version=$(apt-cache -c ../../alt_apt_confdir/etc/apt/apt.conf showsrc isc-dhcp | awk  -F"[' ]" '/^Version: 4\.4\.1[^0-9]/{print $2}' | sort -uV |tail -1)
if [ -z "$version" ]; then
	eval echo "ERROR No candidate version in apt sources for isc-dhcp $ISC_DHCP_VERSION. Exiting" >&2
	exit 3
fi
if [ "$version" != "$ISC_DHCP_VERSION_FULL" ]; then
	echo "WARNING $ISC_DHCP_VERSION_FULL and latest version $version differs." >&2
	backslashedfullversion=$(echo $ISC_DHCP_VERSION_FULL | sed 's/\./\\./g')
	if [ -z "$(eval "apt-cache -c ../../alt_apt_confdir/etc/apt/apt.conf showsrc isc-dhcp | grep '^Version: $backslashedfullversion$'")" ];then
		echo "WARNING No candidate version in apt sources for $ISC_DHCP_VERSION_FULL. Updating rules/isc-dhcpd.mk to use latest version $version instead." >&2
		sed -i_ "s/^ISC_DHCP_VERSION_FULL = .*/ISC_DHCP_VERSION_FULL = $version/g" ../../rules/isc-dhcp.mk
	fi
fi
