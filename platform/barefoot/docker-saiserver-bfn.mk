# docker image for bfn saiserver

DOCKER_SAISERVER_BFN = docker-saiserver$(SAITHRIFT_VER)-bfn.gz
$(DOCKER_SAISERVER_BFN)_PATH = $(PLATFORM_PATH)/docker-saiserver-bfn
$(DOCKER_SAISERVER_BFN)_DEPENDS += $(SAISERVER)
$(DOCKER_SAISERVER_BFN)_LOAD_DOCKERS += $(DOCKER_CONFIG_ENGINE_BUSTER)
SONIC_DOCKER_IMAGES += $(DOCKER_SAISERVER_BFN)
SONIC_BUSTER_DOCKERS += $(DOCKER_SAISERVER_BRCM)

$(DOCKER_SAISERVER_BFN)_CONTAINER_NAME = saiserver$(SAITHRIFT_VER)

$(DOCKER_SAISERVER_BFN)_RUN_OPT += --privileged -t
$(DOCKER_SAISERVER_BFN)_RUN_OPT += -v /host/machine.conf:/etc/machine.conf
$(DOCKER_SAISERVER_BFN)_RUN_OPT += -v /var/run/docker-saiserver:/var/run/sswsyncd
$(DOCKER_SAISERVER_BFN)_RUN_OPT += -v /etc/sonic:/etc/sonic:ro
$(DOCKER_SAISERVER_BFN)_RUN_OPT += -v /host/warmboot:/var/warmboot
