# Ruijie platform modules
ifndef CUSTOM_CONFIG
    CUSTOM_CONFIG := all
    export CUSTOM_CONFIG
endif
ifeq ($(CUSTOM_CONFIG),all) 
    include $(PLATFORM_PATH)/platform-modules-ruijie-all.mk
endif







