#!/bin/sh

# this bootstraps an alternate apt configuration directory for non-root users
# callable via the -c option with most apt commands

DIR=${1:-alt_apt_confdir}

cd $(dirname $0)
cd ..
initdir=$(pwd)
echo "Entering alternate apt configuration directory $DIR creation"
[ -d $DIR ] && echo "WARNING removing $DIR existing directory " >&2 && rm -rf $DIR
mkdir -p $DIR
cd  $DIR

# Debian keyring and its GPG files are needed to authenticate packages and their sources.
# The following commands install them manually # and by the way starts the skeleton creation
# of the alternate apt configuration folder.
echo -n "retrieving official debian archive keyring package..."
wget -q https://ftp.debian.org/debian/pool/main/d/debian-archive-keyring/debian-archive-keyring_2021.1.1_all.deb || exit 2
# The HTTPS URL guarantees a safe source and bootstraps the security of downloaded sources to come.
echo "OK"
echo -n "unpacking official debian archive keyring package content..."
ar -x debian-archive-keyring_2021.1.1_all.deb || exit 3
tar xJf data.tar.xz || exit 4
echo "OK"

currentdir=$(pwd)

echo -n "configuring alternate apt configuration directory..."
mkdir -p lib/apt/partial/ lib/dpkg/ cache/apt/archives/partial/ etc/apt/preferences.d/
touch lib/dpkg/status

echo "deb http://deb.debian.org/debian/ bullseye main contrib non-free
deb-src http://deb.debian.org/debian/ bullseye main contrib non-free

deb https://deb.debian.org/debian-security bullseye-security main contrib
deb-src https://deb.debian.org/debian-security bullseye-security main contrib

deb http://deb.debian.org/debian/ buster main contrib non-free
deb-src http://deb.debian.org/debian/ buster main contrib non-free
">etc/apt/sources.list

echo "APT::Default-Release "bullseye";
Dir::State \"../../$DIR/lib/apt\";
Dir::State::status \"../../$DIR/lib/dpkg/status\";
Dir::Etc \"../../$DIR/etc/apt/sources.list\";
Dir::Etc::SourceList \"../../$DIR/etc/apt/sources.list\";
Dir::Etc::sourceparts \"../../$DIR/etc/apt/sources.list.d\";
Dir::Etc::preferences "../../$DIR/etc/apt/preferences";
Dir::Etc::preferencesparts "../../$DIR/etc/apt/preferences.d";
Dir::Cache \"../../$DIR/cache/apt\";
pkgCacheGen::Essential \"none\";
Dir::Etc::trusted \"../../$DIR/etc/apt/trusted.gpg\";
Dir::Etc::trustedparts \"../../$DIR/etc/apt/trusted.gpg.d\";
">etc/apt/apt.conf
echo "OK"


# apt-get update must be run once to fill cache files
echo -n "filling alternate apt configuration directory cache..."
cd $initdir/src/isc-dhcp/
DEBIAN_FRONTEND=noninteractive apt-get -qq -c ../../$DIR/etc/apt/apt.conf update || exit 5
echo "OK"

cd $currentdir
