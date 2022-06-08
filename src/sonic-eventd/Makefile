RM := rm -rf
EVENTD_TARGET := eventd
EVENTD_TEST := tests/tests
CP := cp
MKDIR := mkdir
CC := g++
MV := mv
LIBS := -levent -lhiredis -lswsscommon -lpthread -lboost_thread -lboost_system -lzmq -lboost_serialization -luuid
TEST_LIBS := -L/usr/src/gtest -lgtest -lgtest_main -lgmock -lgmock_main

CFLAGS += -Wall -std=c++17 -fPIE -I$(PWD)/../sonic-swss-common/common
PWD := $(shell pwd)

ifneq ($(MAKECMDGOALS),clean)
ifneq ($(strip $(C_DEPS)),)
-include $(C_DEPS) $(OBJS)
endif
endif

-include src/subdir.mk
-include tests/subdir.mk
 
all: sonic-eventd eventd-tests

sonic-eventd: $(OBJS)
	@echo 'Building target: $@'
	@echo 'Invoking: G++ Linker'
	$(CC) $(LDFLAGS) -o $(EVENTD_TARGET) $(OBJS) $(LIBS)
	@echo 'Finished building target: $@'
	@echo ' '

eventd-tests: $(TEST_OBJS)
	@echo 'Building target: $@'
	@echo 'Invoking: G++ Linker'
	$(CC) $(LDFLAGS) -o $(EVENTD_TEST) $(TEST_OBJS) $(LIBS) $(TEST_LIBS)
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


