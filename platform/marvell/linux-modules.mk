# linux kernel package for marvell modules

# Add platform specific MOD
LINUX_KERNEL_MOD = linux-module-5.10.0-18-amd64.deb
$(LINUX_KERNEL_MOD)_URL = https://github.com/Marvell-switching/sonic-marvell-binaries/raw/master/amd64/kernel/$(LINUX_KERNEL_MOD)
SONIC_ONLINE_DEBS += $(LINUX_KERNEL_MOD)
