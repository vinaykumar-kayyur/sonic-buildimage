# sonic-yang-mgmt python wheel

SONIC_YANG_MGMT_PY = sonic_yang_mgmt-1.0-py-none-any.whl
$(SONIC_YANG_MGMT_PY)_SRC_PATH = $(SRC_PATH)/sonic-yang-mgmt
$(SONIC_YANG_MGMT_PY)_PYTHON_VERSION = 2
$(SONIC_YANG_MGMT_PY)_DEBS_DEPENDS = $(LIBYANG)

SONIC_PYTHON_WHEELS += $(SONIC_YANG_MGMT_PY)
