# Docker image for SONiC platform monitoring tools

DOCKER_PLATFORM_MONITOR_STEM = docker-platform-monitor
DOCKER_PLATFORM_MONITOR = $(DOCKER_PLATFORM_MONITOR_STEM).gz
DOCKER_PLATFORM_MONITOR_DBG = $(DOCKER_PLATFORM_MONITOR_STEM)-$(DBG_IMAGE_MARK).gz

$(DOCKER_PLATFORM_MONITOR)_PATH = $(DOCKERS_PATH)/$(DOCKER_PLATFORM_MONITOR_STEM)

$(DOCKER_PLATFORM_MONITOR)_DEPENDS += $(LIBSENSORS) $(LM_SENSORS) $(FANCONTROL) $(SENSORD) $(LIBSWSSCOMMON) $(PYTHON_SWSSCOMMON) $(SMARTMONTOOLS)
ifeq ($(CONFIGURED_PLATFORM),barefoot)
$(DOCKER_PLATFORM_MONITOR)_DEPENDS += $(PYTHON_THRIFT)
endif
$(DOCKER_PLATFORM_MONITOR)_PYTHON_WHEELS += $(SONIC_PLATFORM_COMMON_PY2)
$(DOCKER_PLATFORM_MONITOR)_PYTHON_WHEELS += $(SONIC_PLATFORM_COMMON_PY3)
$(DOCKER_PLATFORM_MONITOR)_PYTHON_WHEELS += $(SWSSSDK_PY2)
$(DOCKER_PLATFORM_MONITOR)_PYTHON_WHEELS += $(SWSSSDK_PY3)
$(DOCKER_PLATFORM_MONITOR)_PYTHON_WHEELS += $(SONIC_PY_COMMON_PY2)
$(DOCKER_PLATFORM_MONITOR)_PYTHON_WHEELS += $(SONIC_PY_COMMON_PY3)
$(DOCKER_PLATFORM_MONITOR)_PYTHON_WHEELS += $(SONIC_PLATFORM_API_PY2)
$(DOCKER_PLATFORM_MONITOR)_PYTHON_WHEELS += $(SONIC_LEDD)
$(DOCKER_PLATFORM_MONITOR)_PYTHON_WHEELS += $(SONIC_PCIED)
$(DOCKER_PLATFORM_MONITOR)_PYTHON_WHEELS += $(SONIC_PSUD)
$(DOCKER_PLATFORM_MONITOR)_PYTHON_WHEELS += $(SONIC_SYSEEPROMD)
$(DOCKER_PLATFORM_MONITOR)_PYTHON_WHEELS += $(SONIC_THERMALCTLD)
$(DOCKER_PLATFORM_MONITOR)_PYTHON_WHEELS += $(SONIC_XCVRD)

$(DOCKER_PLATFORM_MONITOR)_DBG_DEPENDS = $($(DOCKER_CONFIG_ENGINE_BUSTER)_DBG_DEPENDS)
$(DOCKER_PLATFORM_MONITOR)_DBG_DEPENDS += $(LIBSWSSCOMMON_DBG) $(LIBSENSORS_DBG)
$(DOCKER_PLATFORM_MONITOR)_DBG_DEPENDS += $(LM_SENSORS_DBG) $(SENSORD_DBG)

$(DOCKER_PLATFORM_MONITOR)_DBG_IMAGE_PACKAGES = $($(DOCKER_CONFIG_ENGINE_BUSTER)_DBG_IMAGE_PACKAGES)

$(DOCKER_PLATFORM_MONITOR)_LOAD_DOCKERS = $(DOCKER_CONFIG_ENGINE_BUSTER)

SONIC_DOCKER_IMAGES += $(DOCKER_PLATFORM_MONITOR)
SONIC_INSTALL_DOCKER_IMAGES += $(DOCKER_PLATFORM_MONITOR)

SONIC_DOCKER_DBG_IMAGES += $(DOCKER_PLATFORM_MONITOR_DBG)
SONIC_INSTALL_DOCKER_DBG_IMAGES += $(DOCKER_PLATFORM_MONITOR_DBG)

$(DOCKER_PLATFORM_MONITOR)_CONTAINER_NAME = pmon
$(DOCKER_PLATFORM_MONITOR)_RUN_OPT += --privileged -t
$(DOCKER_PLATFORM_MONITOR)_RUN_OPT += -v /etc/sonic:/etc/sonic:ro
$(DOCKER_PLATFORM_MONITOR)_RUN_OPT += -v /usr/share/sonic/scripts:/usr/share/sonic/scripts:ro
$(DOCKER_PLATFORM_MONITOR)_RUN_OPT += -v /var/run/platform_cache:/var/run/platform_cache:ro

# Mount Arista python library on Aboot images to be used by plugins
$(DOCKER_PLATFORM_MONITOR)_aboot_RUN_OPT += -v /usr/lib/python2.7/dist-packages/arista:/usr/lib/python2.7/dist-packages/arista:ro
$(DOCKER_PLATFORM_MONITOR)_aboot_RUN_OPT += -v /usr/lib/python3/dist-packages/arista:/usr/lib/python3/dist-packages/arista:ro
$(DOCKER_PLATFORM_MONITOR)_aboot_RUN_OPT += -v /usr/lib/python2.7/dist-packages/sonic_platform:/usr/lib/python2.7/dist-packages/sonic_platform:ro
$(DOCKER_PLATFORM_MONITOR)_aboot_RUN_OPT += -v /usr/lib/python3/dist-packages/sonic_platform:/usr/lib/python3/dist-packages/sonic_platform:ro

$(DOCKER_PLATFORM_MONITOR)_BASE_IMAGE_FILES += cmd_wrapper:/usr/bin/sensors
$(DOCKER_PLATFORM_MONITOR)_BASE_IMAGE_FILES += cmd_wrapper:/usr/sbin/smartctl
$(DOCKER_PLATFORM_MONITOR)_BASE_IMAGE_FILES += cmd_wrapper:/usr/sbin/iSmart
$(DOCKER_PLATFORM_MONITOR)_BASE_IMAGE_FILES += cmd_wrapper:/usr/sbin/SmartCmd
$(DOCKER_PLATFORM_MONITOR)_FILES += $(SUPERVISOR_PROC_EXIT_LISTENER_SCRIPT)
$(DOCKER_PLATFORM_MONITOR)_FILES += $(CONTAINER_MONITOR_SCRIPT)
