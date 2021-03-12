KBUILD_PATH ?= /lib/modules/$(KVERSION)/build
KBUILD_SRC_PATH ?= /lib/modules/$(KVERSION)/source
LLC ?= llc-6.0
CLANG ?= clang-6.0
LLVM_OBJDUMP ?= llvm-objdump-6.0
INC_FLAGS = -nostdinc -isystem $(shell $(CLANG) -print-file-name=include)
EXTRA_CFLAGS ?= -O2  -Wall -emit-llvm -DEBPF_MAPS=shared

# In case up-to-date headers are not installed locally in /usr/include,
# use source build.

LINUXINCLUDE =	\
		-I../../libutil/ \
		-I$(KBUILD_PATH)/include \
		-I$(KBUILD_PATH)/arch/x86/include \
		-I$(KBUILD_SRC_PATH)/include \
		-I$(KBUILD_SRC_PATH)/arch/x86/include/ \
		-I$(KBUILD_PATH)/include/uapi \
		-I$(KBUILD_SRC_PATH)/include/uapi \
		-I$(KBUILD_SRC_PATH)/arch/x86/include/uapi/ \
		-I$(KBUILD_PATH)/include/generated/uapi \
		-I$(KBUILD_PATH)/arch/x86/include/uapi \
		-I$(KBUILD_PATH)/arch/x86/include/generated/ \
		-I$(KBUILD_PATH)/arch/x86/include/generated/uapi \
		-I/usr/include \


KERNELBPF =	ebpftest.bpf 
KERNELOBJ = $(KERNELBPF:%.bpf=%.obj)
KERNELOBJDUMPS = $(KERNELBPF:%.bpf=%.objdump)

prefix ?= $(DESTDIR)
INSTALLPATH = $(prefix)/lib/ebpf

all: $(KERNELBPF)

debug: DEBUG_FLAGS = -DBPFDEBUG
debug: all
	
.PHONY: clean

clean:
	rm -f $(KERNELBPF) $(KERNELOBJ) $(KERNELOBJDUMPS)

distclean: clean

test:
	

install_PROGRAM = install
install_DIR = install -dv


$(KERNELOBJ):  %.obj:%.c

	$(CLANG) $(INC_FLAGS) \
                -D__KERNEL__ -D__ASM_SYSREG_H \
		$(DEBUG_FLAGS) \
		-Wno-unused-value -Wno-pointer-sign \
                -Wno-compare-distinct-pointer-types \
                -Wno-gnu-variable-sized-type-not-at-end \
                -Wno-address-of-packed-member -Wno-tautological-compare \
                -Wno-unknown-warning-option \
		-I../include $(LINUXINCLUDE) \
		$(EXTRA_CFLAGS) -c $< -o $@

$(KERNELBPF):  %.bpf:%.obj
	cat $^ | $(LLC) -march=bpf -filetype=obj -o $@


$(KERNELOBJDUMPS): %.objdump:%.bpf
	$(LLVM_OBJDUMP) -S -no-show-raw-insn $< > $@

objdump: $(KERNELOBJDUMPS)
	
install: $(KERNELBPF)
	$(install_DIR) -d $(INSTALLPATH) ; \
	$(install_PROGRAM) $^ -t $(INSTALLPATH)
	#Comment the below line if the filter has to be disabled
	touch $(INSTALLPATH)/$^.enable


uninstall: $(KERNELBPF)
	rm -rf $(INSTALLPATH)
