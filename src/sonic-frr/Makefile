.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = $(FRR)
DERIVED_TARGET = $(FRR_PYTHONTOOLS) $(FRR_DBG) $(FRR_SNMP) $(FRR_SNMP_DBG)

patch1 = 0001-Add-support-of-bgp-tcp-DSCP-value.patch
patch2 = 0002-Reduce-severity-of-Vty-connected-from-message.patch
patch3 = 0003-ignore-nexthop-attribute-when-NLRI-is-present.patch
patch4 = 0004-Allow-BGP-attr-NEXT_HOP-to-be-0.0.0.0-due-to-allevia.patch
patch5 = 0005-Support-VRF.patch

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	# Build the package
	pushd ./frr
	for frr_patch in $patch1 $patch2 $patch3 $patch4 $patch5; do
		if patch -sfp1 --dry-run < ../patch/$$frr_patch; then
			patch -sfp1 < ../patch/$$frr_patch
		else
			if ! patch -Rsfp1 --dry-run < ../patch/$$frr_patch; then
				echo "Patch $$frr_patch failure"
				exit 1
			fi
		fi
	done
	tools/tarsource.sh -V -e '-sonic'
	dpkg-buildpackage -rfakeroot -b -us -uc -Ppkg.frr.nortrlib -j$(SONIC_CONFIG_MAKE_JOBS)
	popd
	mv $(DERIVED_TARGET) $* $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGET)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
