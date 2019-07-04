# redis package

REDIS_VERSION = 5.0.3-3~bpo9+2

REDIS_TOOLS = redis-tools_$(REDIS_VERSION)_$(CONFIGURED_ARCH).deb
$(REDIS_TOOLS)_SRC_PATH = $(SRC_PATH)/redis
$(REDIS_TOOLS)_DEPENDS += $(LIBHIREDIS_DEV)
$(REDIS_TOOLS)_RDEPENDS += $(LIBHIREDIS)
SONIC_MAKE_DEBS += $(REDIS_TOOLS)

REDIS_SERVER = redis-server_$(REDIS_VERSION)_$(CONFIGURED_ARCH).deb
$(eval $(call add_derived_package,$(REDIS_TOOLS),$(REDIS_SERVER)))

<<<<<<< HEAD
REDIS_SENTINEL = redis-sentinel_$(REDIS_VERSION)_$(CONFIGURED_ARCH).deb
=======
REDIS_SERVER_DBG = redis-server-dbgsym_$(REDIS_VERSION)_amd64.deb
$(eval $(call add_derived_package,$(REDIS_SERVER),$(REDIS_SERVER_DBG)))

REDIS_SENTINEL = redis-sentinel_$(REDIS_VERSION)_amd64.deb
>>>>>>> upstream/master
$(REDIS_SENTINEL)_DEPENDS += $(REDIS_SERVER)
$(REDIS_SENTINEL)_RDEPENDS += $(REDIS_SERVER)
$(eval $(call add_derived_package,$(REDIS_TOOLS),$(REDIS_SENTINEL)))

# The .c, .cpp, .h & .hpp files under src/{$DBG_SRC_ARCHIVE list}
# are archived into debug one image to facilitate debugging.
#
DBG_SRC_ARCHIVE += redis

