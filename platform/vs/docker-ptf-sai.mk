# docker image for docker-ptf-sai

DOCKER_PTF_SAI = docker-ptf-sai.gz
DOCKER_PTF_BASE = docker-ptf.gz
$(DOCKER_PTF_SAI)_PATH = $(DOCKERS_PATH)/docker-ptf-sai
$(DOCKER_PTF_SAI)_DEPENDS += $(LIBTHRIFT_0_13_0) $(PYTHON3_THRIFT_0_13_0)
$(DOCKER_PTF_SAI)_LOAD_DOCKERS += $(DOCKER_PTF_BASE)
SONIC_DOCKER_IMAGES += $(DOCKER_PTF_SAI)
SONIC_BUSTER_DOCKERS += $(DOCKER_PTF_SAI)
