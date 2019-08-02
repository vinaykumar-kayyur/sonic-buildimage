PWD		= $(shell pwd)
EXTRA_CFLAGS:= -I$(M)/include
EXTRA_CFLAGS+= -Wall
SUB_BUILD_DIR = $(PWD)/build
INSTALL_DIR = $(SUB_BUILD_DIR)/$(KERNEL_SRC)/$(INSTALL_MOD_DIR)
INSTALL_SCRIPT_DIR = $(SUB_BUILD_DIR)/usr/local/bin
INSTALL_LIB_DIR = $(SUB_BUILD_DIR)/usr/lib/python2.7/dist-packages

all:
	@if [ ! -d ${INSTALL_LIB_DIR} ]; then mkdir -p ${INSTALL_LIB_DIR} ;fi
	@if [ -d $(PWD)/lib/ ]; then cp -r $(PWD)/lib/* ${INSTALL_LIB_DIR} ;fi
clean:
	rm -rf $(SUB_BUILD_DIR)
	

