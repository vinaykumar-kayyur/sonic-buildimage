# mellanox cpld firmware
MLNX_SN2700_CPLD_ARCHIVE = msn2700_cpld.tar.gz
$(MLNX_SN2700_CPLD_ARCHIVE)_PATH = platform/mellanox/cpld/
SONIC_COPY_FILES += $(MLNX_SN2700_CPLD_ARCHIVE)
MLNX_CPLD_ARCHIVES += $(MLNX_SN2700_CPLD_ARCHIVE)
export MLNX_CPLD_ARCHIVES