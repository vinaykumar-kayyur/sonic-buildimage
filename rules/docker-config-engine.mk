# docker image for sonic config engine

DOCKER_CONFIG_ENGINE = docker-config-engine.gz
$(DOCKER_CONFIG_ENGINE)_PATH = $(DOCKERS_PATH)/docker-config-engine
$(DOCKER_CONFIG_ENGINE)_PYTHON_WHEELS += $(SONIC_CONFIG_ENGINE)
$(DOCKER_CONFIG_ENGINE)_LOAD_DOCKERS += $(DOCKER_BASE)
SONIC_DOCKER_IMAGES += $(DOCKER_CONFIG_ENGINE)
