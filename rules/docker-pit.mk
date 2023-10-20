# docker image for docker-pit

ifeq ($(SONIC_INCLUDE_PIT), y)

DOCKER_PIT = docker-pit.gz
$(DOCKER_PIT)_PATH = $(DOCKERS_PATH)/docker-pit
$(DOCKER_PIT)_PYTHON_WHEELS += $(SONIC_PLATFORM_COMMON_PY2) $(SONIC_PIT_PY3) $(SONIC_PY_COMMON_PY3)

$(DOCKER_PIT)_DBG_DEPENDS = $($(DOCKER_CONFIG_ENGINE_BUSTER)_DBG_DEPENDS)

$(DOCKER_PIT)_LOAD_DOCKERS += $(DOCKER_CONFIG_ENGINE_BUSTER)

SONIC_DOCKER_IMAGES += $(DOCKER_PIT)
SONIC_INSTALL_DOCKER_IMAGES += $(DOCKER_PIT)

$(DOCKER_PIT)_CONTAINER_NAME = pit
$(DOCKER_PIT)_RUN_OPT += --privileged -t
$(DOCKER_PIT)_RUN_OPT += -v /etc/sonic:/etc/sonic:rw
$(DOCKER_PIT)_RUN_OPT += -v /var/log/wtmp:/var/log/wtmp:ro
$(DOCKER_PIT)_RUN_OPT += -v /var/run/frr:/var/run/frr:rw
$(DOCKER_PIT)_RUN_OPT += -v /usr/share/sonic/device:/usr/share/sonic/device:rw
$(DOCKER_PIT)_RUN_OPT += -v /host:/host:rw
$(DOCKER_PIT)_RUN_OPT += -v /root/.ssh:/usr/share/host_ssh:rw
$(DOCKER_PIT)_RUN_OPT += -v /etc/default/locale:/etc/default/locale:ro

# enable docker cmd inside the alinos-monitor container
$(DOCKER_PIT)_RUN_OPT += -v /var/run/docker.sock:/var/run/docker.sock:rw
$(DOCKER_PIT)_RUN_OPT += -v /usr/bin/docker:/usr/bin/docker
$(DOCKER_PIT)_RUN_OPT += -v /usr/lib/x86_64-linux-gnu/libapparmor.so.1:/usr/lib/x86_64-linux-gnu/libapparmor.so.1
$(DOCKER_PIT)_RUN_OPT += -v /usr/lib/x86_64-linux-gnu/libltdl.so.7:/usr/lib/x86_64-linux-gnu/libltdl.so.7
endif
