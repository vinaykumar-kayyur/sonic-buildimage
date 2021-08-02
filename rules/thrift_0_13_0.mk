# thrift package

THRIFT_VERSION_0_13_0 = 0.13.0

LIBTHRIFT_0_13_0 = libthrift_$(THRIFT_VERSION_0_13_0)_$(CONFIGURED_ARCH).deb
$(LIBTHRIFT_0_13_0)_SRC_PATH = $(SRC_PATH)/thrift_0_13_0
SONIC_MAKE_DEBS += $(LIBTHRIFT_0_13_0)

LIBTHRIFT_DEV_0_13_0 = libthrift-dev_$(THRIFT_VERSION_0_13_0)_$(CONFIGURED_ARCH).deb
$(eval $(call add_derived_package,$(LIBTHRIFT_0_13_0),$(LIBTHRIFT_DEV_0_13_0)))

PYTHON_THRIFT_0_13_0 = python-thrift_$(THRIFT_VERSION_0_13_0)_$(CONFIGURED_ARCH).deb
$(eval $(call add_derived_package,$(LIBTHRIFT_0_13_0),$(PYTHON_THRIFT_0_13_0)))

THRIFT_COMPILER_0_13_0 = thrift-compiler_$(THRIFT_VERSION_0_13_0)_$(CONFIGURED_ARCH).deb
$(eval $(call add_derived_package,$(LIBTHRIFT_0_13_0),$(THRIFT_COMPILER_0_13_0)))
