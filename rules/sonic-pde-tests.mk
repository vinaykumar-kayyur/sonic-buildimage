# sonic pdk package
#
# NOTE: sonic-config-engine is a build-time dependency of sonic-utilities
# due to unit tests which are run during the build. However,
# sonic-platform-common and swsssdk are runtime dependencies, and should be
# added here also. However, the current build system assumes all runtime
# dependencies are .deb packages.
#
# TODO: Create a way to specify both .deb and .whl runtime dependencies
#       then add the aforementioned runtime dependencies here.
#

SONIC_PDE_TESTS = python-sonic-pde-tests_1.0-1_all.deb
$(SONIC_PDE_TESTS)_SRC_PATH = $(SRC_PATH)/sonic-platform-pdk-pde/sonic-pde-tests
$(SONIC_PDE_TESTS)_WHEEL_DEPENDS = $(SONIC_CONFIG_ENGINE)
SONIC_PYTHON_STDEB_DEBS += $(SONIC_PDE_TESTS)
