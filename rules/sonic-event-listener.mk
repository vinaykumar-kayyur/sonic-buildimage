# sonic-event-listener (SONiC Pmon supervisord event listener) Debian package

SONIC_EVENT_LISTENER = python-sonic-event-listener_1.0-1_all.deb
$(SONIC_EVENT_LISTENER)_SRC_PATH = $(SRC_PATH)/sonic-platform-daemons/sonic-event-listener
SONIC_PYTHON_STDEB_DEBS += $(SONIC_EVENT_LISTENER)
