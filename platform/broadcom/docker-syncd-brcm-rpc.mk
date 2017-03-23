# docker image for brcm syncd

DOCKER_SYNCD_BRCM_RPC = docker-syncd-brcm-rpc.gz
$(DOCKER_SYNCD_BRCM_RPC)_PATH = $(PLATFORM_PATH)/docker-syncd-brcm-rpc
$(DOCKER_SYNCD_BRCM_RPC)_DEPENDS += $(SYNCD)
$(DOCKER_SYNCD_BRCM_RPC)_FILES += $(DSSERVE) $(BCMCMD)
$(DOCKER_SYNCD_BRCM_RPC)_LOAD_DOCKERS += $(DOCKER_BASE)
SONIC_DOCKER_IMAGES += $(DOCKER_SYNCD_BRCM_RPC)

$(DOCKER_SYNCD_BRCM_RPC)_CONTAINER_NAME = syncd
$(DOCKER_SYNCD_BRCM_RPC)_RUN_OPT += --net=host --privileged -t
$(DOCKER_SYNCD_BRCM_RPC)_RUN_OPT += -v /host/machine.conf:/etc/machine.conf
$(DOCKER_SYNCD_BRCM_RPC)_RUN_OPT += -v /var/run/docker-syncd:/var/run/sswsyncd
$(DOCKER_SYNCD_BRCM_RPC)_RUN_OPT += -v /etc/sonic:/etc/sonic:ro

$(DOCKER_SYNCD_BRCM)_BASE_IMAGE_FILES += bcmcmd:/usr/bin/bcmcmd

