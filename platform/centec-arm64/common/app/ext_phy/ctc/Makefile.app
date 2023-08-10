ifndef PHY_DIR
PHY_DIR := $(CURDIR)
endif
ifndef SDK_DIR
SDK_DIR := $(PHY_DIR)/..
endif
CROSS_COMPILE = aarch64-linux-gnu-
CHIPNAME=tsingma
ARCH=arm64
CPU=tsingma
M64=TRUE
TGT=app

MK_DIR := $(PHY_DIR)/app_phy/mk
DRV_DIR := $(PHY_DIR)/driver
OBJ_DIR=$(PHY_DIR)/out.$(TGT)/obj
LIB_DIR=$(PHY_DIR)/out.$(TGT)/lib
BIN_DIR=$(PHY_DIR)/out.$(TGT)/bin
SRC_TOP_DIR=$(PHY_DIR)

SUPPORT_PHY_MARS = y
#SUPPORT_PHY_MV88E1680 = y
#SUPPORT_PHY_RTL8218B = y
#SUPPORT_PHY_VSC8512 = y
include $(MK_DIR)/sys.mk

#TGT=app
#/*SYSTEM MODIFY, Added by weij for update SDK, 2017-09-11*/
LIB=phy
PROG=phydemo
###################### for target sdk
ifeq ($(TGT),sdk)
SRCS += $(wildcard $(DRV_DIR)/../sdk_phy/*.c)
CPPFLAGS += -DSDK_PHY
endif

################# for target app
ifeq ($(TGT),app)
SRCS += $(wildcard $(DRV_DIR)/../app_phy/*.c)
CPPFLAGS += -DAPP_PHY
endif

########################### for phy driver ###############################
SRCS += $(DRV_DIR)/src/phy_drv_common.c
SRCS += $(DRV_DIR)/src/phy_drv_interface.c
SRCS += $(DRV_DIR)/src/phy_drv_api.c
ifeq ($(SUPPORT_PHY_MARS),y)
SRCS += $(DRV_DIR)/src/phy_drv_mars8p.c
SRCS += $(DRV_DIR)/src/phy_drv_mars1s.c
SRCS += $(DRV_DIR)/src/phy_drv_mars4c.c
CPPFLAGS += -DSUPPORT_PHY_MARS
endif
ifeq ($(SUPPORT_PHY_MV88E1680),y)
SRCS += $(DRV_DIR)/src/phy_drv_mv88e1680.c
### for 88e1680 phy drivers
SRCS += $(wildcard $(DRV_DIR)/src/mad_3.21b/phy/src/driver/*.c)
SRCS += $(wildcard $(DRV_DIR)/src/mad_3.21b/phy/src/platform/*.c)
SRCS += $(wildcard $(DRV_DIR)/src/mad_3.21b/phy/src/madapi/*.c)
SRCS += $(wildcard $(DRV_DIR)/src/mad_3.21b/phy/src/madapi/88E1548P/*.c)
SRCS += $(wildcard $(DRV_DIR)/src/mad_3.21b/phy/src/madapi/88E1680/*.c)
SRCS += $(wildcard $(DRV_DIR)/src/mad_3.21b/phy/src/madapi/88E1780/*.c)
SRCS += $(wildcard $(DRV_DIR)/src/mad_3.21b/phy/src/macfunc/151xP_ptp/*.c)
SRCS += $(wildcard $(DRV_DIR)/src/mad_3.21b/phy/src/macfunc/1_step_ptp/*.c)
SRCS += $(wildcard $(DRV_DIR)/src/mad_3.21b/phy/src/macfunc/macsec/*.c)
SRCS += $(wildcard $(DRV_DIR)/src/mad_3.21b/phy/src/macfunc/util/*.c)
### for 88e1680 phy drivers
CPPFLAGS += -I$(DRV_DIR)/src/mad_3.21b/phy/src/macfunc/1_step_ptp
CPPFLAGS += -I$(DRV_DIR)/src/mad_3.21b/phy/src/macfunc/151xP_ptp
CPPFLAGS += -I$(DRV_DIR)/src/mad_3.21b/phy/Include
CPPFLAGS += -I$(DRV_DIR)/src/mad_3.21b/phy/Include/h/madApi
CPPFLAGS += -I$(DRV_DIR)/src/mad_3.21b/phy/Include/h/driver
CPPFLAGS += -I$(DRV_DIR)/src/mad_3.21b/phy/Include/h/macsec
CPPFLAGS += -I$(DRV_DIR)/src/mad_3.21b/phy/Include/h/platform
## can set or unset, spi_cpm also use DDEBUG
CPPFLAGS += -DDEBUG=1 -DDEBUG_MAD
CPPFLAGS += -DSUPPORT_PHY_MV88E1680
endif

ifeq ($(SUPPORT_PHY_RTL8218B),y)
SRCS += $(DRV_DIR)/src/phy_drv_rtl8218b.c
### for rtl8218b phy drivers
SRCS += $(wildcard $(DRV_DIR)/src/rtk_sdk_phy/phy/*.c)
SRCS += $(wildcard $(DRV_DIR)/src/rtk_sdk_phy/common/*.c)
### for rtl8218b phy drivers
CPPFLAGS += -I$(DRV_DIR)/src/rtk_sdk_phy
CPPFLAGS += -I$(DRV_DIR)/src/rtk_sdk_phy/include
CPPFLAGS += -I$(DRV_DIR)/src/rtk_sdk_phy/include/phy
CPPFLAGS += -DSUPPORT_PHY_RTL8218B
endif

ifeq ($(SUPPORT_PHY_VSC8512),y)
SRCS += $(DRV_DIR)/src/phy_drv_vsc8512.c
CPPFLAGS += -DSUPPORT_PHY_VSC8512
endif

ifeq ($(PHY_ID_REVERSE),y)
CPPFLAGS += -DPHY_ID_REVERSE
endif

CPPFLAGS += -I$(DRV_DIR)/inc

############################### for target compile ##############
ifeq ($(TGT),app)
CPPFLAGS += -I$(DRV_DIR)/../app_phy
CPPFLAGS += -I$(DRV_DIR)/../app_phy/ctc
CPPFLAGS += -I$(DRV_DIR)/../app_phy/sal
endif

ifeq ($(TGT),sdk)
CPPFLAGS += -I$(SDK_DIR)/sal/include
CPPFLAGS += -I$(SDK_DIR)/core/
CPPFLAGS += -I$(SDK_DIR)/core/api/include
CPPFLAGS += -I$(SDK_DIR)/core/common/include
CPPFLAGS += -I$(SDK_DIR)/libctccli/include
CPPFLAGS += -I$(SDK_DIR)/libctccli/ctc_shell/include
CPPFLAGS += -I$(SDK_DIR)/ctccli/sdkcli/
CPPFLAGS += -I$(SDK_DIR)/app
CPPFLAGS += -I$(SDK_DIR)/app/config
CPPFLAGS += $(foreach n, $(COMPATIBAL_CHIP), -I$(SDK_DIR)/ctccli/sdkcli/$(n))
CPPFLAGS += $(foreach n, $(COMPATIBAL_CHIP), -I$(SDK_DIR)/core/$(n)/include)
CPPFLAGS += $(foreach n, $(COMPATIBAL_CHIP), -I$(SDK_DIR)/core/$(n)/include/ctc)
CPPFLAGS += $(foreach n, $(COMPATIBAL_CHIP), -I$(SDK_DIR)/core/$(n)/include/sys)
CPPFLAGS += -I$(SDK_DIR)/driver
CPPFLAGS += -I$(SDK_DIR)/driver/api
endif
include $(MK_DIR)/lib.mk
#include $(MK_DIR)/prog.mk
