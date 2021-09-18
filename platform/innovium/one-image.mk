# sonic innovium ONE image installer

SONIC_ONE_IMAGE = sonic-innovium.bin
$(SONIC_ONE_IMAGE)_MACHINE = innovium
$(SONIC_ONE_IMAGE)_IMAGE_TYPE = onie
$(SONIC_ONE_IMAGE)_INSTALLS += $(SYSTEMD_SONIC_GENERATOR)
$(SONIC_ONE_IMAGE)_LAZY_INSTALLS += $(CEL_MIDSTONE_200I_PLATFORM_MODULE)
$(SONIC_ONE_IMAGE)_LAZY_INSTALLS += $(CEL_MIDSTONE_100X_PLATFORM_MODULE)
$(SONIC_ONE_IMAGE)_LAZY_INSTALLS += $(CEL_SILVERSTONE_X_PLATFORM_MODULE)
$(SONIC_ONE_IMAGE)_LAZY_INSTALLS += $(DELTA_ETC032IF_PLATFORM_MODULE)
$(SONIC_ONE_IMAGE)_LAZY_INSTALLS += $(DELTA_EVSA32Q56_PLATFORM_MODULE)
$(SONIC_ONE_IMAGE)_LAZY_INSTALLS += $(CAMEO_ESC601_32Q_PLATFORM_MODULE) $(CAMEO_ESC600_128Q_PLATFORM_MODULE) $(CAMEO_ESQC610_56SQ_PLATFORM_MODULE) $(CAMEO_ESC602_32Q_PLATFORM_MODULE) $(CAMEO_ESCC601_32Q_PLATFORM_MODULE)
$(SONIC_ONE_IMAGE)_LAZY_INSTALLS += $(WISTRON_PLATFORM_MODULE)
$(SONIC_ONE_IMAGE)_INSTALLS += $(INVM_DRV)
ifeq ($(INSTALL_DEBUG_TOOLS),y)
$(SONIC_ONE_IMAGE)_DOCKERS += $(SONIC_INSTALL_DOCKER_DBG_IMAGES)
$(SONIC_ONE_IMAGE)_DOCKERS += $(filter-out $(patsubst %-$(DBG_IMAGE_MARK).gz,%.gz, $(SONIC_INSTALL_DOCKER_DBG_IMAGES)), $(SONIC_INSTALL_DOCKER_IMAGES))
else
$(SONIC_ONE_IMAGE)_DOCKERS = $(SONIC_INSTALL_DOCKER_IMAGES)
endif
SONIC_INSTALLERS += $(SONIC_ONE_IMAGE)
