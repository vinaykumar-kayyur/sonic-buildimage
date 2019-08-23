# linux kernel package for marvell arm64

KVERSION = 4.4.120


LINUX_KERNEL = linux-image-4.4.120-arm64.deb
export LINUX_KERNEL

$(LINUX_KERNEL)_SRC_PATH = $(PLATFORM_PATH)/linux
SONIC_MAKE_DEBS += $(LINUX_KERNEL)
