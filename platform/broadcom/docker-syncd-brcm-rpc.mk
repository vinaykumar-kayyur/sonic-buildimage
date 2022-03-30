# docker image for brcm syncd with rpc

DOCKER_SYNCD_BRCM_RPC = docker-syncd-brcm-rpc.gz
$(DOCKER_SYNCD_BRCM_RPC)_PATH = $(PLATFORM_PATH)/docker-syncd-brcm-rpc
$(DOCKER_SYNCD_BRCM_RPC)_DEPENDS += $(SYNCD_RPC) $(LIBTHRIFT) $(PTF)

#Support two different versions of thrift
ifeq ($(SAITHRIFT_V2),y)
$(DOCKER_SYNCD_BRCM_RPC)_DEPENDS += $(SYNCD_RPC) $(LIBTHRIFT_0_13_0) $(LIBTHRIFT_DEV_0_13_0) $(PYTHON3_THRIFT_0_13_0) $(THRIFT_COMPILER_0_13_0) $(PTF)
else
$(DOCKER_SYNCD_BRCM_RPC)_DEPENDS += $(SYNCD_RPC) $(LIBTHRIFT) $(PTF)
endif


ifeq ($(INSTALL_DEBUG_TOOLS), y)
$(DOCKER_SYNCD_BRCM_RPC)_DEPENDS += $(SYNCD_RPC_DBG) \
                                    $(LIBSWSSCOMMON_DBG) \
                                    $(LIBSAIMETADATA_DBG) \
                                    $(LIBSAIREDIS_DBG)
endif
$(DOCKER_SYNCD_BRCM_RPC)_FILES += $(DSSERVE) $(BCMCMD) $(SUPERVISOR_PROC_EXIT_LISTENER_SCRIPT)
$(DOCKER_SYNCD_BRCM_RPC)_LOAD_DOCKERS += $(DOCKER_SYNCD_BASE)
SONIC_DOCKER_IMAGES += $(DOCKER_SYNCD_BRCM_RPC)
ifeq ($(ENABLE_SYNCD_RPC),y)
SONIC_INSTALL_DOCKER_IMAGES += $(DOCKER_SYNCD_BRCM_RPC)
endif

$(DOCKER_SYNCD_BRCM_RPC)_CONTAINER_NAME = syncd
$(DOCKER_SYNCD_BRCM_RPC)_RUN_OPT += --privileged -t
$(DOCKER_SYNCD_BRCM_RPC)_RUN_OPT += -v /host/machine.conf:/etc/machine.conf
$(DOCKER_SYNCD_BRCM_RPC)_RUN_OPT += -v /host/warmboot:/var/warmboot
$(DOCKER_SYNCD_BRCM_RPC)_RUN_OPT += -v /var/run/docker-syncd:/var/run/sswsyncd
$(DOCKER_SYNCD_BRCM_RPC)_RUN_OPT += -v /etc/sonic:/etc/sonic:ro

$(DOCKER_SYNCD_BRCM_RPC)_BASE_IMAGE_FILES += bcmcmd:/usr/bin/bcmcmd
$(DOCKER_SYNCD_BRCM_RPC)_BASE_IMAGE_FILES += bcmsh:/usr/bin/bcmsh

