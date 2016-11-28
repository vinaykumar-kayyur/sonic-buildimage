###############################################################################
## Presettings
###############################################################################

# Select bash for commands
.ONESHELL:
SHELL = /bin/bash

.SECONDEXPANSION:

SPACE := 
SPACE += 

###############################################################################
## General definitions
###############################################################################

SRC_PATH = src
RULES_PATH = rules
TARGET_PATH = target
DOCKERS_PATH = dockers
DEBS_PATH = $(TARGET_PATH)/debs
PROJECT_ROOT = $(shell pwd)

CONFIGURED_PLATFORM := $(shell [ -f .platform ] && cat .platform || echo undefined)
PLATFORM_PATH = platform/$(CONFIGURED_PLATFORM)

###############################################################################
## Utility rules
## Define configuration, help etc.
###############################################################################

.platform :
	@echo Build system is not configured, please run make configure
	@exit 1

configure :
	@mkdir -p target/debs
	@echo $(PLATFORM) > .platform

distclean : .platform clean
	@rm -f .platform

###############################################################################
## Include other rules
###############################################################################

include $(RULES_PATH)/config
include $(RULES_PATH)/functions
include $(RULES_PATH)/*.mk
ifneq ($(CONFIGURED_PLATFORM), undefined)
include $(PLATFORM_PATH)/rules.mk
endif

###############################################################################
## Generic rules section
## All rules must go after includes for propper targets expansion
###############################################################################

###############################################################################
## Online targets
###############################################################################

# Download debian packages from online location
# Add new package for download:
#     SOME_NEW_DEB = some_new_deb.deb
#     $(SOME_NEW_DEB)_URL = https://url/to/this/deb.deb
#     SONIC_ONLINE_DEBS += $(SOME_NEW_DEB)
$(addprefix $(DEBS_PATH)/, $(SONIC_ONLINE_DEBS)) : $(DEBS_PATH)/% : .platform
	$(HEADER)
	$(foreach deb,$* $($*_DERIVED_DEBS), \
	    { wget -O $(DEBS_PATH)/$(deb) $($(deb)_URL) $(LOG) || exit 1 ; } ; )
	$(FOOTER)

# Download regular files from online location
# Files are stored in deb packages directory for convenience
# Add new file for download:
#     SOME_NEW_FILE = some_new_file
#     $(SOME_NEW_FILE)_URL = https://url/to/this/file
#     SONIC_ONLINE_FILES += $(SOME_NEW_FILE)
$(addprefix $(DEBS_PATH)/, $(SONIC_ONLINE_FILES)) : $(DEBS_PATH)/% : .platform
	$(HEADER)
	wget -O  $@ $($*_URL) $(LOG) || exit 1
	$(FOOTER)

# Copy debian packages from local directory
# Add new package for copy:
#     SOME_NEW_DEB = some_new_deb.deb
#     $(SOME_NEW_DEB)_PATH = path/to/some_new_deb.deb
#     SONIC_COPY_DEBS += $(SOME_NEW_DEB)
$(addprefix $(DEBS_PATH)/, $(SONIC_COPY_DEBS)) : $(DEBS_PATH)/% : .platform
	$(HEADER)
	$(foreach deb,$* $($*_DERIVED_DEBS), \
	    { cp $($(deb)_PATH) $(DEBS_PATH)/ $(LOG) || exit 1 ; } ; )
	$(FOOTER)

###############################################################################
## Debian package related targets
###############################################################################

# Build project using build.sh script
# They are essentially a one-time build projects that get sources from some URL
# and compile them
# Add new package for build:
#     SOME_NEW_DEB = some_new_deb.deb
#     $(SOME_NEW_DEB)_SRC_PATH = $(SRC_PATH)/project_name
#     $(SOME_NEW_DEB)_DEPENDS = $(SOME_OTHER_DEB1) $(SOME_OTHER_DEB2) ...
#     SONIC_MAKE_DEBS += $(SOME_NEW_DEB)
$(addprefix $(DEBS_PATH)/, $(SONIC_MAKE_DEBS)) : $(DEBS_PATH)/% : .platform $$(addsuffix -install,$$(addprefix $(DEBS_PATH)/,$$($$*_DEPENDS)))
	$(HEADER)
	# remove target to force rebuild
	rm -f $(addprefix $(DEBS_PATH)/, $* $($*_DERIVED_DEBS))
	# build project and take package
	make DEST=$(shell pwd)/$(DEBS_PATH) -C $($*_SRC_PATH) $(shell pwd)/$(DEBS_PATH)/$* $(LOG) || exit 1
	$(FOOTER)

# Build project with dpkg-buildpackage
# Add new package for build:
#     SOME_NEW_DEB = some_new_deb.deb
#     $(SOME_NEW_DEB)_SRC_PATH = $(SRC_PATH)/project_name
#     $(SOME_NEW_DEB)_DEPENDS = $(SOME_OTHER_DEB1) $(SOME_OTHER_DEB2) ...
#     SONIC_DPKG_DEBS += $(SOME_NEW_DEB)
$(addprefix $(DEBS_PATH)/, $(SONIC_DPKG_DEBS)) : $(DEBS_PATH)/% : .platform $$(addsuffix -install,$$(addprefix $(DEBS_PATH)/,$$($$*_DEPENDS)))
	$(HEADER)
	# Build project and take package
	rm -f $($*_SRC_PATH)/debian/*.debhelper.log
	pushd $($*_SRC_PATH) $(LOG)
	[ ! -f ./autogen.sh ] || ./autogen.sh $(LOG)
	dpkg-buildpackage -rfakeroot -b -us -uc $(LOG)
	popd $(LOG)
	mv $(addprefix $($*_SRC_PATH)/../, $* $($*_DERIVED_DEBS)) $(DEBS_PATH) $(LOG)
	$(FOOTER)

# Rules for derived debian packages (dev, dbg, etc.)
# All noise takes place in main deb recipe, so we are just telling that
# we depend on it and move our deb to other targets
# Add new dev package:
#     $(eval $(call add_derived_package,$(ORIGINAL_DEB),derived_deb_file.deb))
$(addprefix $(DEBS_PATH)/, $(SONIC_DERIVED_DEBS)) : $(DEBS_PATH)/% : .platform $$(addsuffix -install,$$(addprefix $(DEBS_PATH)/,$$($$*_DEPENDS)))
	$(HEADER)
	# All noise takes place in main deb recipe, so we are just telling that
	# we depend on it
	# Put newer timestamp
	[ -f $@ ] && touch $@
	$(FOOTER)

# Targets for installing debian packages prior to build one that depends on them
SONIC_INSTALL_TARGETS = $(addsuffix -install,$(addprefix $(DEBS_PATH)/, \
			$(SONIC_ONLINE_DEBS) \
			$(SONIC_COPY_DEBS) \
			$(SONIC_MAKE_DEBS) \
			$(SONIC_DPKG_DEBS) \
			$(SONIC_DERIVED_DEBS)))
$(SONIC_INSTALL_TARGETS) : $(DEBS_PATH)/%-install : .platform $$(addsuffix -install,$$(addprefix $(DEBS_PATH)/,$$($$*_DEPENDS))) $(DEBS_PATH)/$$*
	$(HEADER)
	[ -f $(DEBS_PATH)/$* ] || { echo $(DEBS_PATH)/$* does not exist $(LOG) && exit 1; }
	# put a lock here because dpkg does not allow installing packages in parallel
	while true; do
	if mkdir $(DEBS_PATH)/dpkg_lock &> /dev/null; then
	{ sudo dpkg -i $(DEBS_PATH)/$* $(LOG) && rm -d $(DEBS_PATH)/dpkg_lock && break; } || { rm -d $(DEBS_PATH)/dpkg_lock && exit 1 ; }
	fi
	done
	$(FOOTER)

###############################################################################
## Docker images related targets
###############################################################################

# start docker daemon
docker-start :
	@sudo service docker start &> /dev/null && sleep 1

# targets for building simple docker images that do not depend on any debian packages
$(addprefix $(TARGET_PATH)/, $(SONIC_SIMPLE_DOCKER_IMAGES)) : $(TARGET_PATH)/%.gz : .platform docker-start $$(addsuffix -load,$$(addprefix $(TARGET_PATH)/,$$($$*.gz_LOAD_DOCKERS)))
	$(HEADER)
	docker build --no-cache -t $* $($*.gz_PATH) $(LOG) || { rm -f $@ && exit 1 ; }
	docker save $* | gzip -c > $@
	$(FOOTER)

# Targets for building docker images
$(addprefix $(TARGET_PATH)/, $(SONIC_DOCKER_IMAGES)) : $(TARGET_PATH)/%.gz : .platform docker-start $$(addprefix $(DEBS_PATH)/,$$($$*.gz_DEPENDS) $$($$*.gz_FILES)) $$(addsuffix -load,$$(addprefix $(TARGET_PATH)/,$$($$*.gz_LOAD_DOCKERS)))
	$(HEADER)
	mkdir -p $($*.gz_PATH)/deps $(LOG)
	sudo mount --bind $(DEBS_PATH) $($*.gz_PATH)/deps $(LOG)
	sed 's/SED_DPKG/RUN cd deps \&\& dpkg -i $(shell printf "$(subst $(SPACE),\n,$(call expand,$($*.gz_DEPENDS),RDEPENDS))\n" | awk '!a[$$0]++')/g' $($*.gz_PATH)/Dockerfile.template > $($*.gz_PATH)/Dockerfile
	docker build --no-cache -t $* $($*.gz_PATH) $(LOG) || { rm -f $@ && exit 1 ; }
	docker save $* | gzip -c > $@
	$(FOOTER)

DOCKER_LOAD_TARGETS = $(addsuffix -load,$(addprefix $(TARGET_PATH)/, \
		      $(SONIC_SIMPLE_DOCKER_IMAGES) \
		      $(SONIC_DOCKER_IMAGES)))
$(DOCKER_LOAD_TARGETS) : $(TARGET_PATH)/%.gz-load : .platform docker-start $$(TARGET_PATH)/$$*.gz
	$(HEADER)
	docker load -i $(TARGET_PATH)/$*.gz $(LOG) || exit 1
	$(FOOTER)

###############################################################################
## Installers
###############################################################################

# targets for building installers with base image
$(addprefix $(TARGET_PATH)/, $(SONIC_INSTALLERS)) : $(TARGET_PATH)/% : .platform $$(addprefix $(DEBS_PATH)/,$$($$*_DEPENDS))
	$(HEADER)
	{ ./build_debian.sh "$(USERNAME)" "$(PASSWORD_ENCRYPTED)" $(LOG) && TARGET_MACHINE=$($*_MACHINE) ./build_image.sh $(LOG) ; } || exit 1
	$(FOOTER)

###############################################################################
## Clean targets
###############################################################################

SONIC_CLEAN_DEBS = $(addsuffix -clean,$(addprefix $(DEBS_PATH)/, \
		   $(SONIC_ONLINE_DEBS) \
		   $(SONIC_ONLINE_FILES) \
		   $(SONIC_COPY_DEBS) \
		   $(SONIC_MAKE_DEBS) \
		   $(SONIC_DPKG_DEBS) \
		   $(SONIC_DERIVED_DEBS)))
$(SONIC_CLEAN_DEBS) : $(DEBS_PATH)/%-clean : .platform $$(addsuffix -clean,$$(addprefix $(DEBS_PATH)/,$$($$*_DERIVED_FROM)))
	# remove derived targets if main one is removed, because we treat them
	# as part of one package
	@rm -f $(addprefix $(DEBS_PATH)/, $* $($*_DERIVED_DEBS))

SONIC_CLEAN_TARGETS += $(addsuffix -clean,$(addprefix $(TARGET_PATH)/, \
		       $(SONIC_DOCKER_IMAGES) \
		       $(SONIC_SIMPLE_DOCKER_IMAGES)))
$(SONIC_CLEAN_TARGETS) : $(TARGET_PATH)/%-clean : .platform
	@rm -f $(TARGET_PATH)/$*

clean-logs : .platform
	@rm -f $(TARGET_PATH)/*.log $(DEBS_PATH)/*.log

clean : .platform clean-logs $$(SONIC_CLEAN_DEBS) $$(SONIC_CLEAN_TARGETS)

###############################################################################
## all
###############################################################################

all : .platform $$(addprefix $(TARGET_PATH)/,$$(SONIC_ALL))

###############################################################################
## Standard targets
###############################################################################

.PHONY : $(SONIC_CLEAN_DEBS) $(SONIC_CLEAN_TARGETS) clean distclean configure

.INTERMEDIATE : $(SONIC_INSTALL_TARGETS) $(DOCKER_LOAD_TARGETS) docker-start
