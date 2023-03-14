# bash package
#
# Created to patch plugin support in the bash-package included in Debian-11 (Bullseye)
# release.

# Bash major release-number corresponding to Debian-11 (Bullseye)
BASH_VERSION = 5.1
# Bash complete release-number. This image contains all 5.1 fixes  up to patch '2'.
BASH_VERSION_FULL = ${BASH_VERSION}-2+deb11u1

# BASH_VERSION cannot be directly exported w/o side-effects
# it is already used with a different value by iptables sources
BASH_VERSION_MAJOR = $(BASH_VERSION)
export BASH_VERSION_MAJOR BASH_VERSION_FULL

BASH = bash_$(BASH_VERSION_FULL)_$(CONFIGURED_ARCH).deb
$(BASH)_SRC_PATH = $(SRC_PATH)/bash
SONIC_MAKE_DEBS += $(BASH)
