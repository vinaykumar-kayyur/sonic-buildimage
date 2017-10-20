# Mellanox SAI

MLNX_SAI_VERSION = sonic1.9.1fixes-master
MLNX_SAI_REVISION = dc0e84b3762f847369524a917e271ceb2878b4d3

export MLNX_SAI_VERSION MLNX_SAI_REVISION

MLNX_SAI = mlnx-sai_1.mlnx.$(MLNX_SAI_VERSION)_amd64.deb
$(MLNX_SAI)_SRC_PATH = $(PLATFORM_PATH)/mlnx-sai
$(MLNX_SAI)_DEPENDS += $(MLNX_SDK_DEBS)
$(MLNX_SAI)_RDEPENDS += $(MLNX_SDK_RDEBS) $(MLNX_SDK_DEBS)
SONIC_MAKE_DEBS += $(MLNX_SAI)
