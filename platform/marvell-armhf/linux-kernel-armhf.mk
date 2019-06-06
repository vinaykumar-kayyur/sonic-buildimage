# linux kernel package for marvell armhf

#KVERSION_armhf = 3.10.70-gd896b34_3.10.70-gd896b34-3
KVERSION_armhf = 3.10.70-gd896b34

#LINUX_HEADERS_armhf = linux-headers-3.10.70-gd896b34_3.10.70-gd896b34-3_armel.deb
#$(LINUX_HEADERS_armhf)_PATH = /sonic
#SONIC_COPY_DEBS += $(LINUX_HEADERS_armhf)

LINUX_KERNEL_armhf = linux-image-3.10.70-gd896b34_3.10.70-gd896b34-3_armel.deb
$(LINUX_KERNEL_armhf)_PATH = /sonic
SONIC_COPY_DEBS += $(LINUX_KERNEL_armhf)
