KBUILD_PATH ?= /lib/modules/$(KVERSION)/build
KBUILD_SRC_PATH ?= /lib/modules/$(KVERSION)/source
LLC ?= llc-6.0
CLANG ?= clang-6.0


SRCS          := ebpftest.c ebpf_timer.c
EBPFOBJS      := $(SRCS:.c=.bpf)
BYTEOBJS      := $(SRCS:.c=.o)
EXTRA_CFLAGS  += -I$(PWD)/../../libutil \
				 -I$(KBUILD_SRC_PATH)/include/uapi -I$(KBUILD_SRC_PATH)/include \
				 -I$(objtree)/usr/include -Wno-unused-variable 


# Tell kbuild to always build the programs
always := $(hostprogs-y)
always += $(EBPFOBJS)


# Trick to allow make to be run from this directory
all:
	$(MAKE) -C $(KBUILD_PATH) M=$$PWD/

clean:
	$(MAKE) -C $(KBUILD_PATH) M=$$PWD clean
	@rm -f *~ $(BYTEOBJS) $(EBPFOBJS)

distclean: clean

# Verify LLVM compiler tools are available and bpf target is supported by llc
.PHONY: verify_cmds verify_target_bpf $(CLANG) $(LLC)

verify_cmds: $(CLANG) $(LLC)
	@for TOOL in $^ ; do \
		if ! (which -- "$${TOOL}" > /dev/null 2>&1); then \
			echo "*** ERROR: Cannot find LLVM tool $${TOOL}" ;\
			exit 1; \
		else true; fi; \
	done

verify_target_bpf: verify_cmds
	@if ! (${LLC} -march=bpf -mattr=help > /dev/null 2>&1); then \
		echo "*** ERROR: LLVM (${LLC}) does not support 'bpf' target" ;\
		echo "   NOTICE: LLVM version >= 3.7.1 required" ;\
		exit 2; \
	else true; fi

$(SRCS): verify_target_bpf

# asm/sysreg.h - inline assembly used by it is incompatible with llvm.
# But, there is no easy way to fix it, so just exclude it since it is
# useless for BPF samples.
$(addprefix $(obj)/,$(BYTEOBJS)):%.o:%.c
	$(CLANG) $(NOSTDINC_FLAGS) $(LINUXINCLUDE) $(EXTRA_CFLAGS) \
	-D__KERNEL__ -D__ASM_SYSREG_H -Wno-unused-value -Wno-pointer-sign \
		-Wno-compare-distinct-pointer-types \
		-O2 -emit-llvm -c $< -o $@

$(addprefix $(obj)/,$(EBPFOBJS)):%.bpf:%.o
	cat $^ | $(LLC) -march=bpf -filetype=obj -o $@ 

install:
	cp *.bpf   $(DESTDIR)/usr/lib
