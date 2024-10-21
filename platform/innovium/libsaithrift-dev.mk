# libsaithrift-dev package
SAI_VER = 0.9.4

LIBSAITHRIFT_DEV = libsaithrift$(SAITHRIFT_VER)-dev_$(SAI_VER)_$(CONFIGURED_ARCH).deb
$(LIBSAITHRIFT_DEV)_SRC_PATH = $(SRC_PATH)/sonic-sairedis/SAI
ifeq ($(SAITHRIFT_V2),y)
$(LIBSAITHRIFT_DEV)_DEPENDS += $(INVM_LIBSAI) $(INVM_HSAI) $(INVM_SHELL) $(LIBSAIMETADATA) $(LIBSAIMETADATA_DEV)
$(LIBSAITHRIFT_DEV)_RDEPENDS += $(INVM_LIBSAI) $(INVM_HSAI) $(INVM_SHELL) $(LIBSAIMETADATA)
$(LIBSAITHRIFT_DEV)_BUILD_ENV = SAITHRIFTV2=true SAITHRIFT_VER=v2
else
$(LIBSAITHRIFT_DEV)_DEPENDS += $(INVM_LIBSAI) $(INVM_HSAI) $(INVM_SHELL)
$(LIBSAITHRIFT_DEV)_RDEPENDS += $(INVM_LIBSAI) $(INVM_HSAI) $(INVM_SHELL)
endif
SONIC_DPKG_DEBS += $(LIBSAITHRIFT_DEV)

PYTHON_SAITHRIFT = python-saithrift$(SAITHRIFT_VER)_$(SAI_VER)_$(CONFIGURED_ARCH).deb
$(eval $(call add_extra_package,$(LIBSAITHRIFT_DEV),$(PYTHON_SAITHRIFT)))

SAISERVER = saiserver$(SAITHRIFT_VER)_$(SAI_VER)_$(CONFIGURED_ARCH).deb
$(SAISERVER)_RDEPENDS += $(LIBSAITHRIFT_DEV) $(INVM_LIBSAI) $(INVM_HSAI) $(INVM_SHELL)
$(eval $(call add_extra_package,$(LIBSAITHRIFT_DEV),$(SAISERVER)))

SAISERVER_DBG = saiserver$(SAITHRIFT_VER)-dbg_$(SAI_VER)_$(CONFIGURED_ARCH).deb
$(SAISERVER_DBG)_RDEPENDS += $(SAISERVER)
$(eval $(call add_extra_package,$(LIBSAITHRIFT_DEV),$(SAISERVER_DBG)))
