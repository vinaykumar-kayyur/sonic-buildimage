.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

RM := rm -rf
CP := cp -rf
MKDIR := mkdir
MV := mv
LIBDASHAPI := libdashapi.so
BUILD_DIR := build
DESTDIR := 
DASH_API_PROTO_DIR := sonic-dash-api/proto
INSTALLED_HEADER_DIR := $(DESTDIR)/usr/include/dash_api
INSTALLED_LIB_DIR := $(DESTDIR)/usr/lib
INSTALLED_PY_DIR := $(DESTDIR)/usr/lib/python3/dist-packages/dash_api

all: compile_proto dashapi.so

compile_proto:
	$(MKDIR) -p $(BUILD_DIR)
	protoc -I=$(DASH_API_PROTO_DIR) --cpp_out=$(BUILD_DIR) $(DASH_API_PROTO_DIR)/*.proto
	protoc -I=$(DASH_API_PROTO_DIR) --python_out=$(BUILD_DIR) $(DASH_API_PROTO_DIR)/*.proto

dashapi.so:
	g++ -std=c++14 -fPIC -shared -o $(BUILD_DIR)/$(LIBDASHAPI) $(wildcard $(BUILD_DIR)/*.pb.cc) -lprotobuf

clean:
	$(RM) $(BUILD_DIR)

install:
	$(MKDIR) -p $(INSTALLED_HEADER_DIR)
	$(CP) $(BUILD_DIR)/*.pb.h $(INSTALLED_HEADER_DIR)
	$(MKDIR) -p $(INSTALLED_LIB_DIR)
	$(CP) $(BUILD_DIR)/$(LIBDASHAPI) $(INSTALLED_LIB_DIR)
	$(MKDIR) -p $(INSTALLED_PY_DIR)
	touch $(INSTALLED_PY_DIR)/__init__.py
	$(CP) $(BUILD_DIR)/*_pb2.py $(INSTALLED_PY_DIR)

uninstall:
	$(RM) $(INSTALLED_HEADER_DIR)
	$(RM) $(INSTALLED_LIB_DIR)/$(LIBDASHAPI)
	$(RM) $(INSTALLED_PY_DIR)

.PHONY: uninstall clean
