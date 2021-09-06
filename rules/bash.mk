# bash package
#
# Created to patch plugin support in the bash-package included in Debian-10 (Buster)
# release.

# Bash major release-number corresponding to Debian-10 (Buster)
BASH_VERSION_MAJOR = 5.0
# Bash complete release-number. This image contains all 5.0 fixes  up to patch '4'.
BASH_VERSION_FULL = $(BASH_VERSION_MAJOR)-4

export BASH_VERSION_MAJOR BASH_VERSION_FULL

BASH = bash_$(BASH_VERSION_FULL)_$(CONFIGURED_ARCH).deb
$(BASH)_SRC_PATH = $(SRC_PATH)/bash
SONIC_MAKE_DEBS += $(BASH)
