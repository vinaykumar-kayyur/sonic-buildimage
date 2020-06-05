# linux kernel package for centec arm64

LINUX_KERNEL_DTB_INITRAMFS = linux-dtb-initramfs_1.0.deb
$(LINUX_KERNEL_DTB_INITRAMFS)_URL = https://github.com/CentecNetworks/sonic-binaries/raw/master/$(PLATFORM_ARCH)/kernel/$(LINUX_KERNEL_DTB_INITRAMFS)
SONIC_ONLINE_DEBS += $(LINUX_KERNEL_DTB_INITRAMFS)
SONIC_STRETCH_DEBS += $(LINUX_KERNEL_DTB_INITRAMFS)
