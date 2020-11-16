# sonic-chassisd (SONiC Chassis mgmt daemon) wheel package

SONIC_CHASSISD = sonic_chassisd-1.0-py2-none-any.whl
$(SONIC_CHASSISD)_SRC_PATH = $(SRC_PATH)/sonic-platform-daemons/sonic-chassisd
$(SONIC_CHASSISD)_DEPENDS = $(SONIC_PY_COMMON_PY2)
$(SONIC_CHASSISD)_PYTHON_VERSION = 2
SONIC_PYTHON_WHEELS += $(SONIC_CHASSISD)
