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

SONIC_PLATFORM_PDE = sonic-platform-pde_1.0_amd64.deb
$(SONIC_PLATFORM_PDE)_SRC_PATH = $(SRC_PATH)/sonic-platform-pdk-pde
$(SONIC_PLATFORM_PDE)_DEPENDS += $(BRCM_SAI) $(BRCM_SAI_DEV) $(SWIG)

SONIC_DPKG_DEBS += $(SONIC_PLATFORM_PDE)
