# only used for non-vs platforms

ifneq ($(CONFIGURED_PLATFORM),vs)

SYNCD = syncd_1.0.0_$(CONFIGURED_ARCH).deb
$(SYNCD)_RDEPENDS += $(LIBSAIREDIS) $(LIBSAIMETADATA)
$(SYNCD)_DPKG_TARGET = binary-syncd
$(SYNCD)_SRC_PATH = $(SRC_PATH)/sonic-sairedis
$(SYNCD)_DEPENDS += $(LIBSWSSCOMMON_DEV) $(LIBSAIREDIS)
$(SYNCD)_RDEPENDS += $(LIBSWSSCOMMON)
$(SYNCD)_DEB_BUILD_OPTIONS = nocheck
SONIC_DPKG_DEBS += $(SYNCD)

ifeq ($(ENABLE_SYNCD_RPC),y)
SYNCD_RPC = syncd-rpc_1.0.0_$(CONFIGURED_ARCH).deb
$(SYNCD_RPC)_RDEPENDS += $(LIBSAIREDIS) $(LIBSAIMETADATA)
$(eval $(call add_derived_package,$(SYNCD),$(SYNCD_RPC)))

# Inject libthrift build dependency for RPC build
# Support two different versions of thrift
ifeq ($(SAITHRIFT_V2),y)
$(SYNCD)_DEPENDS += $(LIBTHRIFT_DEV_0_13_0)
else
$(SYNCD)_DEPENDS += $(LIBTHRIFT_DEV)
endif
$(SYNCD)_DEPENDS += $(LIBSWSSCOMMON_DEV)
$(SYNCD)_DPKG_TARGET = binary-syncd-rpc
endif

SYNCD_DBG = syncd-dbg_1.0.0_$(CONFIGURED_ARCH).deb
$(SYNCD_DBG)_DEPENDS += $(SYNCD)
$(SYNCD_DBG)_RDEPENDS += $(SYNCD)
$(eval $(call add_derived_package,$(SYNCD),$(SYNCD_DBG)))

ifeq ($(ENABLE_SYNCD_RPC),y)
SYNCD_RPC_DBG = syncd-rpc-dbg_1.0.0_$(CONFIGURED_ARCH).deb
$(SYNCD_RPC_DBG)_DEPENDS += $(SYNCD_RPC)
$(SYNCD_RPC_DBG)_RDEPENDS += $(SYNCD_RPC)
$(eval $(call add_derived_package,$(SYNCD),$(SYNCD_RPC_DBG)))
endif

endif
