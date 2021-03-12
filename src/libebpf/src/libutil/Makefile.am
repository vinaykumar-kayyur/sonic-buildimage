
KBUILD_PATH ?= /lib/modules/$(KVERSION)/build
KBUILD_SRC_PATH ?= /lib/modules/$(KVERSION)/source


INCLUDES = -I$(KBUILD_SRC_PATH)/include/uapi -I$(KBUILD_SRC_PATH)/include
INCLUDES += -I $(top_srcdir)/utils

nobase_include_HEADERS = ebpf/bpf_load.h ebpf/bpf_helpers.h ebpf/libebpf.h ebpf/libbpf.h 
lib_LIBRARIES = libebpf.a
bin_PROGRAMS = ebpftest

if DEBUG
DBGFLAGS = -ggdb -DDEBUG -O0
else
DBGFLAGS = -g -DNDEBUG -O0
endif

libebpf_a_CFLAGS = -Wno-unused-variable -D__EXPORTED_HEADERS__ $(COV_CFLAGS) $(ASAN_CFLAGS) $(DBGFLAGS)
libebpf_a_SOURCES =  bpf_load.c libbpf.c libebpf.c
ebpftest_CFLAGS  =  -Wno-unused-variable -D__EXPORTED_HEADERS__ $(COV_CFLAGS) $(ASAN_CFLAGS) $(DBGFLAGS)
ebpftest_SOURCES = ebpftest.c
ebpftest_LDFLAGS = -L. -lebpf -lbpf -lebpf -lelf
