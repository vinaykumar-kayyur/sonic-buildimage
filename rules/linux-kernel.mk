# linux kernel package

KVERSION_SHORT = 5.10.0-12-2
KVERSION = $(KVERSION_SHORT)-$(CONFIGURED_ARCH)
KERNEL_VERSION = 5.10.103
KERNEL_SUBVERSION = 1
ifeq ($(CONFIGURED_ARCH), armhf)
# Override kernel version for ARMHF as it uses arm MP (multi-platform) for short version
KVERSION = $(KVERSION_SHORT)-armmp
endif

# Place an URL here to .tar.gz file if you want to include those patches
EXTERNAL_KERNEL_PATCHES =

export KVERSION_SHORT KVERSION KERNEL_VERSION KERNEL_SUBVERSION EXTERNAL_KERNEL_PATCHES

LINUX_HEADERS_COMMON = linux-headers-$(KVERSION_SHORT)-common_$(KERNEL_VERSION)-$(KERNEL_SUBVERSION)_all.deb
$(LINUX_HEADERS_COMMON)_SRC_PATH = $(SRC_PATH)/sonic-linux-kernel
SONIC_MAKE_DEBS += $(LINUX_HEADERS_COMMON)

LINUX_HEADERS = linux-headers-$(KVERSION)_$(KERNEL_VERSION)-$(KERNEL_SUBVERSION)_$(CONFIGURED_ARCH).deb
$(eval $(call add_derived_package,$(LINUX_HEADERS_COMMON),$(LINUX_HEADERS)))

ifeq ($(CONFIGURED_ARCH), armhf)
	LINUX_KERNEL = linux-image-$(KVERSION)_$(KERNEL_VERSION)-$(KERNEL_SUBVERSION)_$(CONFIGURED_ARCH).deb
else
	LINUX_KERNEL = linux-image-$(KVERSION)-unsigned_$(KERNEL_VERSION)-$(KERNEL_SUBVERSION)_$(CONFIGURED_ARCH).deb
endif
$(eval $(call add_derived_package,$(LINUX_HEADERS_COMMON),$(LINUX_KERNEL)))
