RM := rm -rf
EVENTD_TARGET := eventd
CP := cp
MKDIR := mkdir
CC := g++
MV := mv
LIBS := -levent -lhiredis -lswsscommon -pthread -lboost_thread -lboost_system
CFLAGS += -Wall -std=c++17 -fPIE -I$(PWD)/../sonic-swss-common/common
PWD := $(shell pwd)

ifneq ($(MAKECMDGOALS),clean)
ifneq ($(strip $(C_DEPS)),)
-include $(C_DEPS) $(OBJS)
endif
endif

-include src/subdir.mk
 
all: sonic-eventd

sonic-eventd: $(OBJS)
	@echo 'Building target: $@'
	@echo 'Invoking: G++ Linker'
	$(CC) $(LDFLAGS) -o $(EVENTD_TARGET) $(OBJS) $(LIBS)
	@echo 'Finished building target: $@'
	@echo ' '

install:
	$(MKDIR) -p $(DESTDIR)/usr/sbin
	$(MV) $(EVENTD_TARGET) $(DESTDIR)/usr/sbin

deinstall:
	$(RM) $(DESTDIR)/usr/sbin/$(EVENTD_TARGET)
	$(RM) -rf $(DESTDIR)/usr/sbin

clean:
	-@echo ' '

.PHONY: all clean dependents


