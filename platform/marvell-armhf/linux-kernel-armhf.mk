# linux kernel package for marvell armhf

KVERSION = 4.4.8


LINUX_KERNEL = linux-image-4.4.8_4.4.8-4_armhf.deb
$(LINUX_KERNEL)_PATH = /sonic
SONIC_COPY_DEBS += $(LINUX_KERNEL)
