.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = $(FRR)
DERIVED_TARGET = $(FRR_PYTHONTOOLS) $(FRR_DBG) $(FRR_SNMP) $(FRR_SNMP_DBG)
SUFFIX = $(shell date +%Y%m%d\.%H%M%S)
STG_BRANCH = stg_temp.$(SUFFIX)

FRR_EXTRA_FLAGS = ""
ifeq ($(INCLUDE_FRR_BGP), n)
FRR_EXTRA_FLAGS += --disable-bgpd --disable-bgp-bmp
endif
ifeq ($(INCLUDE_FRR_BFD), n)
FRR_EXTRA_FLAGS += --disable-bfdd
endif
ifeq ($(INCLUDE_FRR_PBR), n)
FRR_EXTRA_FLAGS += --disable-pbrd
endif
ifeq ($(INCLUDE_FRR_VRRP), n)
FRR_EXTRA_FLAGS += --disable-vrrpd
endif
ifeq ($(INCLUDE_FRR_OSPF), n)
FRR_EXTRA_FLAGS += --disable-ospfd
FRR_EXTRA_FLAGS += --disable-ospf6d
endif

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	# Build the package
	pushd ./frr
	git checkout -b $(FRR_BRANCH) origin/$(FRR_BRANCH) || git checkout $(FRR_BRANCH)
	stg branch --create $(STG_BRANCH) $(FRR_TAG)
	stg repair
	stg import -s ../patch/series
	gbp dch --ignore-branch --new-version=$(FRR_VERSION)-sonic-$(FRR_SUBVERSION) --dch-opt="--force-bad-version" --commit --git-author
	if [[ $(INCLUDE_FRR_BGP) == n ]]; then
	    stg repair
		stg import -s ../patch/adv1/series
	fi
	DEB_CONFIGURE_EXTRA_FLAGS="$(FRR_EXTRA_FLAGS)" \
	DEB_BUILD_OPTIONS=nocheck \
	dpkg-buildpackage -rfakeroot -b -us -uc -Ppkg.frr.nortrlib -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
	stg undo || true
	git clean -xfdf
	git checkout $(FRR_BRANCH)
	stg branch --delete --force $(STG_BRANCH)
	git rev-parse --short HEAD | xargs git checkout
	git checkout master
	git branch -D $(FRR_BRANCH)
	popd
	mv $(DERIVED_TARGET) $* $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGET)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
