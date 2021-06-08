##############################################################
## Top level platform rules.mk
##############################################################

CISCO_PLATFORM_BRANCH := cisco-8000/master
CISCO_PLATFORM_URL := https://github.com/Cisco-8000-sonic/platform-cisco-8000.git
CISCO_PLATFORM_SRC=$(PLATFORM_PATH)/src

$(shell if [ ! -d $(CISCO_PLATFORM_SRC) ]; then git clone -b $(CISCO_PLATFORM_BRANCH) $(CISCO_PLATFORM_URL) $(CISCO_PLATFORM_SRC); fi)
$(shell if [ -d $(CISCO_PLATFORM_SRC) ]; then $(CISCO_PLATFORM_SRC)/platform_setup.sh; fi)

include $(CISCO_PLATFORM_SRC)/rules.dep
