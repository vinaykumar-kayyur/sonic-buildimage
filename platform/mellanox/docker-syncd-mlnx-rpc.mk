# docker image for mlnx syncd

DOCKER_SYNCD_MLNX_RPC = docker-syncd-mlnx-rpc.gz
$(DOCKER_SYNCD_MLNX_RPC)_PATH = $(PLATFORM_PATH)/docker-syncd-mlnx-rpc
$(DOCKER_SYNCD_MLNX_RPC)_DEPENDS += $(SYNCD) $(MFT) $(PYTHON_SDK_API)
$(DOCKER_SYNCD_MLNX_RPC)_FILES += $(MLNX_FW)
$(DOCKER_SYNCD_MLNX_RPC)_LOAD_DOCKERS += $(DOCKER_BASE)
SONIC_DOCKER_IMAGES += $(DOCKER_SYNCD_MLNX_RPC)

$(DOCKER_SYNCD_MLNX_RPC)_CONTAINER_NAME = syncd
$(DOCKER_SYNCD_MLNX_RPC)_RUN_OPT += --net=host --privileged -t
$(DOCKER_SYNCD_MLNX_RPC)_RUN_OPT += -v /host/machine.conf:/etc/machine.conf
$(DOCKER_SYNCD_MLNX_RPC)_RUN_OPT += -v /etc/sonic:/etc/sonic:ro
