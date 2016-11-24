# redis package

REDIS_TOOLS = redis-tools_3.0.7-2_amd64.deb
$(REDIS_TOOLS)_SRC_PATH = $(SRC_PATH)/redis
SONIC_MAKE_DEBS += $(REDIS_TOOLS)

REDIS_SERVER = redis-server_3.0.7-2_amd64.deb
$(eval $(call add_derived_package,$(REDIS_TOOLS),$(REDIS_SERVER)))

REDIS_SENTINEL = redis-sentinel_3.0.7-2_amd64.deb
$(REDIS_SENTINEL)_DEPENDS += $(REDIS_SERVER)
$(REDIS_SENTINEL)_RDEPENDS += $(REDIS_SERVER)
$(eval $(call add_derived_package,$(REDIS_TOOLS),$(REDIS_SENTINEL)))
