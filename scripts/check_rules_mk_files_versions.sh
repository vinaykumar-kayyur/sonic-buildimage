#!/bin/sh

# NOTICE
# For the given hardcoded list of packages sources below, this script scrolls corresponding versions declared in "rules/{pkcgsrcname}.mk" files
# and then compares them to the ones available with the command "apt-cache showsrc {pkcgsrcname}".
# If the configured full version is available, nothing will be done.
# The sources shall be retrieved later with the command 'apt-get source {pkcgsrcname}={version_full}" w/o any trouble.
# NB:  Though, if the latest available version in "apt-cache showsrc" matching the (base) version declared  in "rules/{pkcgsrcname}.mk"
#      is different than {fullversion}, a warning will be issued on stderr to encourage an update.
# If the configured full version is not available, there are 2 possibilities.
# - If there is an available version in "apt-cache showsrc" matching the (base) version declared,
#   "rules/{pkcgsrcname}.mk" {version_full} value will be modified on-the-fly to use it.
#   If several matching versions are available, the latest one will be preferred.
# - If none is available, the script will exit with an error code and stops the whole compilation process.
#   This will prevent starting a long build process condamned to fail and thus spare precious time and computing ressources.
#   NB: This is the main purpose of this script.

cd $(dirname $0)
cd ..
rootdir=$(pwd)
for pkgsrcname in \
       bash \
       debootstrap \
       hiredis \
       ifupdown2 \
       iproute2 \
       iptables \
       isc-dhcp \
       kdump-tools \
       libyang1 \
       lm-sensors \
       snmpd \
       ;do
    basevarname=$(echo $pkgsrcname"_VERSION" | tr [a-z\-] [A-Z_])

    cd $rootdir/src/$pkgsrcname/

    i=0
    # retrieve current version values of package sources from makefile rules
    # usually there is only one value configured but there are some exceptions such as snmpd
    # versions differ between the target debian versions -> loop required in that case
    for line in $(grep "^$basevarname =" ../../rules/$pkgsrcname.mk | sed -e 's/ *= */=/'); do
         i=$((i+1))
         value=$(echo $line | sed 's/.*= *//g')
         eval "$basevarname=$value"
	 # we assume the full versions appears in the same order
         eval $(grep "^$basevarname\_FULL =" ../../rules/$pkgsrcname.mk | sed -e 's/ *= */=/' | head -$i | tail -1)
         # before parsing with awk regex, apply backslash to dots and plus to avoid ambiguous detection
         eval "versionpattern=\$(echo \$$basevarname | sed -e 's/"'\./\\\\.'"/g' -e 's/"'\+/\\\\+/g'"')"

         # next, use eval and awk to parse 'apt-cache showsrc' output and retrieve available versions from debian repositories
         # pipe result to a unique and version sort (-u and -V options) and tail to get the last version
         eval $(echo "version=\$(apt-cache -c ../../alt_apt_confdir/etc/apt/apt.conf showsrc $pkgsrcname | awk  -F\"[' ]\" '/^Version: (1:)*$versionpattern[^0-9]*/{print \$2}' | cut -d: -f2- | sort -uV | tail -1)")
         # previous line will be interpreted as follow (modulo package name and version changes)
         # version=$(apt-cache -c ../../alt_apt_confdir/etc/apt/apt.conf showsrc isc-dhcp | awk  -F"[' ]" '/^Version: (1:)*4\.4\.1[^0-9]*/{print $2}' | cut -d: -f2- | sort -uV |tail -1)
         if [ -z "$version" ]; then
             eval echo "ERROR No candidate version in apt sources for $pkgsrcname \$$basevarname. Exiting" >&2
             exit 3
         fi
         if [ "$version" != "$(eval echo \$$basevarname\_FULL)" ]; then
             echo "WARNING $(eval echo \$$basevarname\_FULL) and latest version $version differs." >&2
             eval backslashedfullversion=$(echo "\$(echo \$$basevarname\_FULL| sed 's/\./\\\\./g')")
             if [ -z "$(eval "apt-cache -c ../../alt_apt_confdir/etc/apt/apt.conf showsrc $pkgsrcname | grep '^Version: \(1:\)*$backslashedfullversion$'")" ];then
                 echo "WARNING No candidate version in apt sources for $(eval echo \$$basevarname\_FULL). Updating rules/$pkgsrcname.mk to use latest version $version instead." >&2
                 linenumber=$(grep -n "^$basevarname\_FULL =" ../../rules/$pkgsrcname.mk | head -$i | tail -1 | cut -d: -f1)
                 sed -i_ "$linenumber,+0s/^$basevarname\_FULL = .*/$basevarname\_FULL = $version/g" ../../rules/$pkgsrcname.mk
             fi
         fi
    done
done
