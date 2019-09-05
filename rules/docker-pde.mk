# Docker image for SONiC Platform Development Environment (PDE)


ifeq ($(ENABLE_PDE), y)

DOCKER_PDE_STEM = docker-pde
DOCKER_PDE = $(DOCKER_PDE_STEM).gz
DOCKER_PDE_DBG = $(DOCKER_PDE_STEM)-$(DBG_IMAGE_MARK).gz

$(DOCKER_PDE)_PATH = $(DOCKERS_PATH)/$(DOCKER_PDE_STEM)

$(DOCKER_PDE)_DEPENDS += $(BRCM_SAI) $(PDE_TEST_HOST)
$(DOCKER_PDE)_PYTHON_DEBS += $(SONIC_PDE_TESTS)
$(DOCKER_PDE)_PYTHON_WHEELS += $(SONIC_PLATFORM_COMMON_PY2)

$(DOCKER_PDE)_DBG_DEPENDS = $($(DOCKER_CONFIG_ENGINE_STRETCH)_DBG_DEPENDS)
$(DOCKER_PDE)_DBG_IMAGE_PACKAGES = $($(DOCKER_CONFIG_ENGINE_STRETCH)_DBG_IMAGE_PACKAGES)

$(DOCKER_PDE)_LOAD_DOCKERS = $(DOCKER_CONFIG_ENGINE_STRETCH)

SONIC_DOCKER_IMAGES += $(DOCKER_PDE)
SONIC_STRETCH_DOCKERS += $(DOCKER_PDE)
SONIC_INSTALL_DOCKER_IMAGES += $(DOCKER_PDE)

SONIC_STRETCH_DBG_DOCKERS += $(DOCKER_PDE_DBG)
SONIC_DOCKER_DBG_IMAGES += $(DOCKER_PDE_DBG)
SONIC_INSTALL_DOCKER_DBG_IMAGES += $(DOCKER_PDE_DBG)

$(DOCKER_PDE)_CONTAINER_NAME = pde
$(DOCKER_PDE)_RUN_OPT += --net=host --privileged -t
$(DOCKER_PDE)_RUN_OPT += -v /etc/sonic:/etc/sonic:ro
$(DOCKER_PDE)_RUN_OPT += -v /host/machine.conf:/host/machine.conf:ro
$(DOCKER_PDE)_RUN_OPT += -v /usr/lib/python2.7/dist-packages:/usr/share/sonic/classes:ro
$(DOCKER_PDE)_RUN_OPT += -v /var/log/syslog:/var/log/syslog:ro
$(DOCKER_PDE)_RUN_OPT += -v /lib/modules:/lib/modules:ro
$(DOCKER_PDE)_RUN_OPT += -v /boot:/boot:ro
$(DOCKER_PDE)_BASE_IMAGE_FILES += pde-test-host:/usr/bin/pde-test-host
$(DOCKER_PDE)_BASE_IMAGE_FILES += port_breakout.py:/usr/local/bin/port_breakout.py


endif
