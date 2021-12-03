# USBMOUNT

USBMOUNT_VERSION_BASE = 0.0.24
USBMOUNT_VERSION = $(USBMOUNT_VERSION_BASE)

export USBMOUNT_VERSION_BASE
export USBMOUNT_VERSION

LIB_LOCK_FILE_BIN_DEB = liblockfile-bin_1.14-1.1_amd64.deb
$(LIB_LOCK_FILE_BIN_DEB)_URL = http://ftp.us.debian.org/debian/pool/main/libl/liblockfile/liblockfile-bin_1.14-1.1_amd64.deb
SONIC_ONLINE_DEBS += $(LIB_LOCK_FILE_BIN_DEB) 

LIB_LOCK_FILE_DEB = liblockfile1_1.14-1.1_amd64.deb
$(LIB_LOCK_FILE_DEB)_URL = http://ftp.us.debian.org/debian/pool/main/libl/liblockfile/liblockfile1_1.14-1.1_amd64.deb
SONIC_ONLINE_DEBS += $(LIB_LOCK_FILE_DEB)

LOCK_FILE_PROGS_DEB = lockfile-progs_0.1.18_amd64.deb
$(LOCK_FILE_PROGS_DEB)_URL = http://ftp.us.debian.org/debian/pool/main/l/lockfile-progs/lockfile-progs_0.1.18_amd64.deb
SONIC_ONLINE_DEBS += $(LOCK_FILE_PROGS_DEB) 

USBMOUNT = usbmount_0.0.24_all.deb
$(USBMOUNT)_SRC_PATH = $(SRC_PATH)/usbmount
SONIC_MAKE_DEBS += $(USBMOUNT)

# The .c, .cpp, .h & .hpp files under src/{$DBG_SRC_ARCHIVE list}
# are archived into debug one image to facilitate debugging.
#
DBG_SRC_ARCHIVE += usbmount
