# sonic-ledd (SONiC Front-panel LED control daemon) Debian package

SONIC_LEDD = sonic_ledd-1.1-py3-none-any.whl
$(SONIC_LEDD)_SRC_PATH = $(SRC_PATH)/sonic-platform-daemons/sonic-ledd
$(SONIC_LEDD)_DEPENDS = $(SONIC_PY_COMMON_PY3)
$(SONIC_LEDD)_PYTHON_VERSION = 3
SONIC_PYTHON_WHEELS += $(SONIC_LEDD)
