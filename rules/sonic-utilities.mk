# sonic utilities package

SONIC_UTILS = python-sonic-utilities_1.2-1_all.deb
$(SONIC_UTILS)_SRC_PATH = $(SRC_PATH)/sonic-utilities
$(SONIC_UTILS)_WHEEL_DEPENDS = $(SONIC_CONFIG_ENGINE)
SONIC_PYTHON_STDEB_DEBS += $(SONIC_UTILS)
