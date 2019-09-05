# pde test host package

PDE_TEST_HOST_VERSION=1.0.0
PDE_TEST_HOST_VERSION_FULL=$(PDE_TEST_HOST_VERSION)-1

PDE_TEST_HOST = pde-test-host_$(PDE_TEST_HOST_VERSION_FULL)_amd64.deb
$(PDE_TEST_HOST)_SRC_PATH = $(SRC_PATH)/sonic-platform-pdk-pde/pde-test-host
$(PDE_TEST_HOST)_DEPENDS = $(BRCM_SAI)

$(eval $(call add_derived_package,$(PDE_TEST_HOST)))

SONIC_MAKE_DEBS += $(PDE_TEST_HOST)

export PDE_TEST_HOST
export PDE_TEST_HOST_VERSION
export PDE_TEST_HOST_VERSION_FULL
