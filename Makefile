###############################################################################
## Wrapper for starting make inside sonic-slave container
###############################################################################

USER := $(shell id -un)
PWD := $(shell pwd)

MAKEFLAGS += -B

DOCKER_RUN := docker run --privileged \
    -v $(PWD):/sonic \
    -it sonic-slave-$(USER)

DOCKER_BUILD = docker build --no-cache \
	       --build-arg user=$(USER) \
	       --build-arg uid=$(shell id -u) \
	       --build-arg guid=$(shell id -g) \
	       -t sonic-slave-$(USER) \
	       sonic-slave

include rules/config

%::
	@[ ! -z "`docker images | grep sonic-slave-$(USER)`" ] || $(DOCKER_BUILD)
	@$(DOCKER_RUN) make \
	    -C sonic \
	    -f slave.mk \
	    -j $(SONIC_CONFIG_BUILD_JOBS) \
	    PLATFORM=$(PLATFORM) \
	    $@

sonic-slave-build :
	@$(DOCKER_BUILD)

sonic-slave-bash :
	@$(DOCKER_RUN) bash
