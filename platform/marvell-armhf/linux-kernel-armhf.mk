# linux kernel package for marvell armhf

KVERSION = 4.4.8


LINUX_KERNEL = linux-image-4.4.8_4.4.8-4_armhf.deb
$(LINUX_KERNEL)_SRC_PATH = $(PLATFORM_PATH)/linux
SONIC_MAKE_DEBS += $(LINUX_KERNEL)
