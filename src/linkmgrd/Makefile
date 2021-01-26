-include ../makefile.init

RM := rm -rf
LINKMGRD_TARGET := linkmgrd
LINKMGRD_TEST_TARGET := linkmgrd-test
CP := cp
MKDIR := mkdir
CC := g++
MV := mv
CPP_FLAGS := -O3 -Wall -c -fmessage-length=0 -fPIC
TOPDIR := $(dir $(firstword $(MAKEFILE_LIST)))

INCLUDES := \
    -I"$(TOPDIR)/src" \
    -I"/usr/include/libnl3/"

# All of the sources participating in the build are defined here
-include sources.mk
-include test/subdir.mk
-include src/mux_state/subdir.mk
-include src/link_state/subdir.mk
-include src/link_prober/subdir.mk
-include src/link_manager/subdir.mk
-include src/common/subdir.mk
-include src/subdir.mk
-include subdir.mk
-include objects.mk

ifneq ($(MAKECMDGOALS),clean)
ifneq ($(strip $(CC_DEPS)),)
-include $(CC_DEPS)
endif
ifneq ($(strip $(C++_DEPS)),)
-include $(C++_DEPS)
endif
ifneq ($(strip $(C_UPPER_DEPS)),)
-include $(C_UPPER_DEPS)
endif
ifneq ($(strip $(CXX_DEPS)),)
-include $(CXX_DEPS)
endif
ifneq ($(strip $(CPP_DEPS)),)
-include $(CPP_DEPS)
endif
ifneq ($(strip $(C_DEPS)),)
-include $(C_DEPS)
endif
endif

-include ../makefile.defs

# Add inputs and outputs from these tool invocations to the build variables 

# All Target
all: sonic-linkmgrd

# Tool invocations
sonic-linkmgrd: $(OBJS) $(USER_OBJS) $(OBJS_LINKMGRD)
	@echo 'Building target: $@'
	@echo 'Invoking: GCC C++ Linker'
	$(CC) -pthread -o "$(LINKMGRD_TARGET)" $(OBJS) $(OBJS_LINKMGRD) $(USER_OBJS) $(LIBS)
	@echo 'Finished building target: $@'
	@echo ' '

# Other Targets
test: $(OBJS) $(USER_OBJS) $(OBJS_LINKMGRD_TEST)
	@echo 'Building target: $@'
	@echo 'Invoking: GCC C++ Linker'
	$(CC) -pthread -o "$(LINKMGRD_TEST_TARGET)" $(OBJS) $(OBJS_LINKMGRD_TEST) $(USER_OBJS) $(LIBS) $(LIBS_TEST)
	@echo 'Executing test target: $@'
	LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libasan.so.5 ./$(LINKMGRD_TEST_TARGET)
	@echo 'Finished building target: $@'
	@echo ' '
	
install:
	$(MKDIR) -p $(DESTDIR)/usr/sbin
	$(MV) $(LINKMGRD_TARGET) $(DESTDIR)/usr/sbin
	$(RM) $(CC_DEPS) $(C++_DEPS) $(EXECUTABLES) $(C_UPPER_DEPS) $(CXX_DEPS) $(OBJS) $(CPP_DEPS) $(C_DEPS) \
		$(LINKMGRD_TARGET) $(LINKMGRD_TEST_TARGET) $(OBJS_LINKMGRD) $(OBJS_LINKMGRD_TEST)

deinstall:
	$(RM) $(DESTDIR)/usr/sbin/$(LINKMGRD_TARGET)
	$(RM) -rf $(DESTDIR)/usr/sbin

clean:
	-$(RM) $(CC_DEPS) $(C++_DEPS) $(EXECUTABLES) $(C_UPPER_DEPS) $(CXX_DEPS) $(OBJS) $(CPP_DEPS) $(C_DEPS) \
		$(LINKMGRD_TARGET) $(LINKMGRD_TEST_TARGET) $(OBJS_LINKMGRD) $(OBJS_LINKMGRD_TEST)
	-@echo ' '

.PHONY: all clean dependents

-include ../makefile.targets
