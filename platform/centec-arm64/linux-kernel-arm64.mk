# linux kernel package for centec arm64

LINUX_KERNEL_DTB = linux-dtb_1.0.0-1_arm64.deb
$(LINUX_KERNEL_DTB)_URL = https://github.com/CentecNetworks/sonic-binaries/raw/master/$(PLATFORM_ARCH)/kernel/$(LINUX_KERNEL_DTB)
SONIC_ONLINE_DEBS += $(LINUX_KERNEL_DTB)
