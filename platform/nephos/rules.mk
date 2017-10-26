include $(PLATFORM_PATH)/sdk.mk
include $(PLATFORM_PATH)/sai.mk
include $(PLATFORM_PATH)/platform-modules-ingrasys.mk
include $(PLATFORM_PATH)/docker-orchagent-nephos.mk
include $(PLATFORM_PATH)/docker-syncd-nephos.mk
include $(PLATFORM_PATH)/docker-syncd-nephos-rpc.mk
include $(PLATFORM_PATH)/one-image.mk
include $(PLATFORM_PATH)/one-aboot.mk
include $(PLATFORM_PATH)/libsaithrift-dev.mk
include $(PLATFORM_PATH)/python-saithrift.mk
include $(PLATFORM_PATH)/docker-ptf-nephos.mk

NPX_DIAG = npx_diag
$(NPX_DIAG)_URL = "ftp://sonic:sonic@172.19.77.245/lib/nephos/npx_diag_0.0.0-20171002"

DSSERVE = dsserve
$(DSSERVE)_URL = "https://sonicstorage.blob.core.windows.net/packages/20170518/dsserve?sv=2015-04-05&sr=b&sig=gyNbgSL%2FvpMXDdpboVkIJcTKMRdGgEaOR9OukHhEsu8%3D&se=2030-03-31T23%3A06%3A35Z&sp=r"

SONIC_ONLINE_FILES += $(NPX_DIAG) $(DSSERVE)

SONIC_ALL += $(SONIC_ONE_IMAGE) $(SONIC_ONE_ABOOT_IMAGE) \
             $(DOCKER_FPM) \
             $(DOCKER_PTF_NEPHOS) \
             $(DOCKER_SYNCD_NEPHOS_RPC)

# Inject nephos sai into sairedis
$(LIBSAIREDIS)_DEPENDS += $(NEPHOS_SAI) $(NEPHOS_SAI_DEV) $(LIBSAITHRIFT_DEV_NEPHOS)

# Runtime dependency on nephos sai is set only for syncd
$(SYNCD)_RDEPENDS += $(NEPHOS_SAI)
