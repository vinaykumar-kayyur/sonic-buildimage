# sonic-pit package

ifeq ($(SONIC_INCLUDE_PIT), y)
SONIC_PIT = sonic_pit

SONIC_PIT_PY3 = $(SONIC_PIT)-1.0-py3-none-any.whl
$(SONIC_PIT_PY3)_SRC_PATH = $(SRC_PATH)/sonic-pit
$(SONIC_PIT_PY3)_PYTHON_VERSION = 3
$(SONIC_PIT_PY3)_TEST = n
SONIC_PYTHON_WHEELS += $(SONIC_PIT_PY3)

endif
