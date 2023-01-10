# libsaithrift-dev package

SAI_VER = 0.9.4

LIBSAITHRIFT_DEV = libsaithrift$(SAITHRIFT_VER)-dev_$(SAI_VER)_$(CONFIGURED_ARCH).deb
$(LIBSAITHRIFT_DEV)_SRC_PATH = $(SRC_PATH)/sonic-sairedis/SAI

#Support two different versions of thrift
ifeq ($(SAITHRIFT_V2),y)
$(LIBSAITHRIFT_DEV)_DEPENDS += $(LIBTHRIFT_0_14_1) $(LIBTHRIFT_0_14_1_DEV) $(PYTHON3_THRIFT_0_14_1) $(THRIFT_0_14_1_COMPILER)
$(LIBSAITHRIFT_DEV)_RDEPENDS += $(LIBTHRIFT_0_14_1)
$(LIBSAITHRIFT_DEV)_BUILD_ENV = SAITHRIFTV2=true SAITHRIFT_VER=v2 GEN_SAIRPC_OPTS="--adapter_logger"
else
$(LIBSAITHRIFT_DEV)_DEPENDS += $(LIBTHRIFT) $(LIBTHRIFT_DEV) $(PYTHON_THRIFT) $(THRIFT_COMPILER)
$(LIBSAITHRIFT_DEV)_RDEPENDS += $(LIBTHRIFT)
endif
$(LIBSAITHRIFT_DEV)_DEPENDS += $(MRVL_FPA) $(MRVL_SAI)
$(LIBSAITHRIFT_DEV)_RDEPENDS += $(MRVL_SAI)
SONIC_DPKG_DEBS += $(LIBSAITHRIFT_DEV)

PYTHON_SAITHRIFT = python-saithrift$(SAITHRIFT_VER)_$(SAI_VER)_$(CONFIGURED_ARCH).deb
$(eval $(call add_extra_package,$(LIBSAITHRIFT_DEV),$(PYTHON_SAITHRIFT)))

SAISERVER = saiserver$(SAITHRIFT_VER)_$(SAI_VER)_$(CONFIGURED_ARCH).deb
$(SAISERVER)_RDEPENDS += $(LIBTHRIFT) $(MRVL_SAI)
$(eval $(call add_extra_package,$(LIBSAITHRIFT_DEV),$(SAISERVER)))

SAISERVER_DBG = saiserver-dbg_$(SAI_VER)_$(CONFIGURED_ARCH).deb
$(SAISERVER_DBG)_RDEPENDS += $(SAISERVER)
$(eval $(call add_extra_package,$(LIBSAITHRIFT_DEV),$(SAISERVER_DBG)))
