# linux kernel package for marvell armhf

KVERSION_armhf = 4.4.8


LINUX_KERNEL_armhf = linux-image-4.4.8_4.4.8-4_armhf.deb
$(LINUX_KERNEL_armhf)_PATH = /sonic
SONIC_COPY_DEBS += $(LINUX_KERNEL_armhf)
