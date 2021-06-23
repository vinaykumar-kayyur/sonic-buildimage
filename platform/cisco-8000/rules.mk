##############################################################
## Top level platform rules.mk
##############################################################
CISCO_PLATFORM_BRANCH := cisco-8000/master
CISCO_PLATFORM_URL := https://$(GITUSER):$(GITTOKEN)@Cisco-sonic-8000/platform-cisco-8000.git
CISCO_PLATFORM_SRC=$(PLATFORM_PATH)/src
CISCO_8000_SHA1 := f224715

$(shell if [ ! -d $(CISCO_PLATFORM_SRC) ]; then git clone -b $(CISCO_PLATFORM_BRANCH) $(CISCO_PLATFORM_URL) $(CISCO_PLATFORM_SRC); fi)
$(shell if [ -d $(CISCO_PLATFORM_SRC) ]; then cd $(CISCO_PLATFORM_SRC) && git checkout $(CISCO_8000_SHA1))
$(shell if [ -d $(CISCO_PLATFORM_SRC) ]; then $(CISCO_PLATFORM_SRC)/platform_setup.sh; fi)

include $(CISCO_PLATFORM_SRC)/rules.dep

