ONIE_RECOVERY_IMAGE = onie-recovery-x86_64-kvm_x86_64-r0.iso
$(ONIE_RECOVERY_IMAGE)_URL = "https://sonicstorage.blob.core.windows.net/packages/onie/onie-recovery-x86_64-kvm_x86_64-r0.iso?sv=2015-04-05&sr=b&sig=XMAk1cttBFM369CMbihe5oZgXwe4uaDVfwg4CTLT%2F5U%3D&se=2155-10-13T10%3A40%3A13Z&sp=r"

ONIE_RECOVERY_MKVM_4ASIC_IMAGE = onie-recovery-x86_64-mkvm_x86_64_4_asic-r0.iso
$(ONIE_RECOVERY_MKVM_4ASIC_IMAGE)_URL = "https://sonicstorage.blob.core.windows.net/packages/onie/onie-recovery-x86_64-mkvm_x86_64_4_asic-r0.iso?sv=2020-04-08&st=2021-08-04T22%3A17%3A35Z&se=2030-08-05T22%3A17%3A00Z&sr=b&sp=r&sig=hT3bEyT2RbTTSGy4uLCAKzXXtBI2xTh3G%2BDxTmaf6R4%3D"

ONIE_RECOVERY_MKVM_6ASIC_IMAGE = onie-recovery-x86_64-mkvm_x86_64_6_asic-r0.iso
$(ONIE_RECOVERY_MKVM_6ASIC_IMAGE)_URL = "https://sonicstorage.blob.core.windows.net/packages/onie/onie-recovery-x86_64-mkvm_x86_64_6_asic-r0.iso?sv=2020-04-08&st=2021-08-04T22%3A22%3A47Z&se=2030-08-05T22%3A22%3A00Z&sr=b&sp=r&sig=VdDP%2Bvx%2BxwL4Ca8Un%2BN28pVbPHAxyYmO04MTtjfN%2FTY%3D"

SONIC_ONLINE_FILES += $(ONIE_RECOVERY_IMAGE) $(ONIE_RECOVERY_MKVM_4ASIC_IMAGE) $(ONIE_RECOVERY_MKVM_6ASIC_IMAGE)
