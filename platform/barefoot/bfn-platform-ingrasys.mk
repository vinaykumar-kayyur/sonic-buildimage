ifdef BLDENV
BFN_INGRASYS_PLATFORM = bfnplatform-ingrasys_8.8.1_docker_amd64.deb
$(BFN_INGRASYS_PLATFORM)_URL = "https://github.com/Ingrasys-sonic/packages/raw/master/lib/bfnplatform-ingrasys_8.8.1_amd64.deb"
endif

SONIC_ONLINE_DEBS += $(BFN_INGRASYS_PLATFORM) # $(BFN_SAI_DEV)
$(BFN_SAI_DEV)_DEPENDS += $(BFN_INGRASYS_PLATFORM)
