CC = $(CROSS_COMPILE)gcc
AR = $(CROSS_COMPILE)ar cru
RANLIB = $(CROSS_COMPILE)ranlib

export COMPATIBAL_CHIP

ifeq ($(findstring goldengate, $(CHIPNAME)),goldengate)
COMPATIBAL_CHIP += goldengate
endif

ifeq ($(findstring greatbelt, $(CHIPNAME)),greatbelt)
COMPATIBAL_CHIP += greatbelt
endif

ifeq ($(ARCH),powerpc)
CPPFLAGS += -DHOST_IS_LE=0
endif

ifeq ($(ARCH),x86)
CPPFLAGS += -DHOST_IS_LE=1
endif

ifeq ($(ARCH),mips)
ifeq ($(CPU),ls2f)
CPPFLAGS += -DHOST_IS_LE=1
else
CPPFLAGS += -DHOST_IS_LE=0
CPPFLAGS += -mabi=n32
endif
endif

ifeq ($(ARCH),arm)
CPPFLAGS += -DHOST_IS_LE=1
endif

ifeq ($(ARCH),arm64)
CPPFLAGS += -DHOST_IS_LE=1
endif

ifeq ($(ARCH),um)
CPPFLAGS += -DHOST_IS_LE=1
endif

ifeq ($(M64),TRUE)
ifeq ($(ARCH), arm64)
CPPFLAGS += -fPIC -Wno-long-long -Wformat
else
LD_FLAGS += -m64
CPPFLAGS += -fPIC -Wno-long-long -Wformat -m64
endif
else
ifeq ($(CPU),ls2f)
LD_FLAGS += -mabi=n32
CPPFLAGS += -DDAL_USE_MMAP2
else
ifneq ($(ARCH),arm)
CPPFLAGS += -m32
LD_FLAGS += -m32
endif
endif
endif

ifeq ($(findstring greatbelt, $(CHIPNAME)),greatbelt)
CPPFLAGS += -DGREATBELT
endif

ifeq ($(findstring goldengate, $(CHIPNAME)),goldengate)
CPPFLAGS += -DGOLDENGATE
endif

ifeq ($(findstring duet2, $(CHIPNAME)),duet2)
CPPFLAGS += -DDUET2
CPPFLAGS += -DUSW
endif

ifeq ($(findstring tsingma, $(CHIPNAME)),tsingma)
CPPFLAGS += -DTSINGMA
CPPFLAGS += -DUSW
endif

CPPFLAGS += -DSDK_IN_USERMODE
CPPFLAGS += -DSDK_WORK_PLATFORM=0
CFLAGS += -fno-strict-aliasing
CFLAGS += $(CTC_CFLAGS)

