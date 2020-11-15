# docker image for lldp agent

DOCKER_LLDP_STEM = docker-lldp
DOCKER_LLDP = $(DOCKER_LLDP_STEM).gz
DOCKER_LLDP_DBG = $(DOCKER_LLDP_STEM)-$(DBG_IMAGE_MARK).gz

$(DOCKER_LLDP)_PATH = $(DOCKERS_PATH)/docker-lldp

$(DOCKER_LLDP)_DEPENDS += $(LLDPD) $(LIBSWSSCOMMON) $(PYTHON_SWSSCOMMON) $(PYTHON3_SWSSCOMMON)

$(DOCKER_LLDP)_DBG_DEPENDS = $($(DOCKER_CONFIG_ENGINE_BUSTER)_DBG_DEPENDS)
$(DOCKER_LLDP)_DBG_DEPENDS += $(LLDPD_DBG) $(LIBSWSSCOMMON_DBG)

$(DOCKER_LLDP)_DBG_IMAGE_PACKAGES = $($(DOCKER_CONFIG_ENGINE_BUSTER)_DBG_IMAGE_PACKAGES)

$(DOCKER_LLDP)_PYTHON_WHEELS += $(DBSYNCD_PY2)
$(DOCKER_LLDP)_LOAD_DOCKERS += $(DOCKER_CONFIG_ENGINE_BUSTER)

SONIC_DOCKER_IMAGES += $(DOCKER_LLDP)
SONIC_INSTALL_DOCKER_IMAGES += $(DOCKER_LLDP)

SONIC_DOCKER_DBG_IMAGES += $(DOCKER_LLDP_DBG)
SONIC_INSTALL_DOCKER_DBG_IMAGES += $(DOCKER_LLDP_DBG)

$(DOCKER_LLDP)_CONTAINER_NAME = lldp
$(DOCKER_LLDP)_RUN_OPT += --privileged -t
$(DOCKER_LLDP)_RUN_OPT += -v /etc/sonic:/etc/sonic:ro
$(DOCKER_LLDP)_RUN_OPT += -v /usr/share/sonic/scripts:/usr/share/sonic/scripts:ro

$(DOCKER_LLDP)_BASE_IMAGE_FILES += lldpctl:/usr/bin/lldpctl
$(DOCKER_LLDP)_BASE_IMAGE_FILES += lldpcli:/usr/bin/lldpcli
$(DOCKER_LLDP)_BASE_IMAGE_FILES += monit_lldp:/etc/monit/conf.d
$(DOCKER_LLDP)_FILES += $(SUPERVISOR_PROC_EXIT_LISTENER_SCRIPT)
