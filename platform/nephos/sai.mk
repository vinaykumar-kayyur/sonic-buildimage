SDK_VERSION = 3.0.4
SAI_VERSION = 1.6.1
SAI_COMMIT_ID = 54b056

# Place here URL where SAI deb exist
NEPHOS_SAI_DEB_LOCAL_URL = 
export NEPHOS_SAI_DEB_LOCAL_URL
#
ifneq ($(NEPHOS_SAI_DEB_LOCAL_URL), )
SAI_FROM_LOCAL = y
else
SAI_FROM_LOCAL = n
endif

NEPHOS_SAI = libsainps_$(SDK_VERSION)_sai_$(SAI_VERSION)_$(SAI_COMMIT_ID)_amd64.deb
ifeq ($(SAI_FROM_LOCAL), y)
$(NEPHOS_SAI)_PATH = $(NEPHOS_SAI_DEB_LOCAL_URL)
else
$(NEPHOS_SAI)_URL = "https://github.com/NephosInc/SONiC/raw/master/sai/libsainps_$(SDK_VERSION)_sai_$(SAI_VERSION)_$(SAI_COMMIT_ID)_amd64.deb"
endif


ifeq ($(SAI_FROM_LOCAL), y)
SONIC_COPY_DEBS += $(NEPHOS_SAI) 
else
SONIC_ONLINE_DEBS += $(NEPHOS_SAI) 
endif
