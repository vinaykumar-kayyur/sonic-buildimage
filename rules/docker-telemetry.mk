# docker image for telemetry agent

DOCKER_TELEMETRY = docker-sonic-telemetry.gz
$(DOCKER_TELEMETRY)_PATH = $(DOCKERS_PATH)/docker-sonic-telemetry
$(DOCKER_TELEMETRY)_DEPENDS += $(REDIS_TOOLS) $(SONIC_TELEMETRY)
$(DOCKER_TELEMETRY)_LOAD_DOCKERS += $(DOCKER_CONFIG_ENGINE)
SONIC_DOCKER_IMAGES += $(DOCKER_TELEMETRY)
ifeq ($(ENABLE_SYSTEM_TELEMETRY), y)
SONIC_INSTALL_DOCKER_IMAGES += $(DOCKER_TELEMETRY)
endif

$(DOCKER_TELEMETRY)_CONTAINER_NAME = telemetry
$(DOCKER_TELEMETRY)_RUN_OPT += --net=host --privileged -t
$(DOCKER_TELEMETRY)_RUN_OPT += -v /etc/sonic:/etc/sonic:ro

$(DOCKER_TELEMETRY)_RUN_OPT += -v /var/log/wtmp:/var/log/wtmp:ro

# enable docker cmd inside the telemetry container
$(DOCKER_TELEMETRY)_RUN_OPT += -v /var/run/docker.sock:/var/run/docker.sock:rw
$(DOCKER_TELEMETRY)_RUN_OPT += -v /usr/bin/docker:/usr/bin/docker
$(DOCKER_TELEMETRY)_RUN_OPT += -v /usr/lib/x86_64-linux-gnu/libapparmor.so.1:/usr/lib/x86_64-linux-gnu/libapparmor.so.1
$(DOCKER_TELEMETRY)_RUN_OPT += -v /usr/lib/x86_64-linux-gnu/libltdl.so.7:/usr/lib/x86_64-linux-gnu/libltdl.so.7
