DIR=$(shell pwd)
BUILD_OUTPUT=$(DIR)/tmp
PROGRAM=libextphy.so

ifndef CTC_MAKE
export CTC_MAKE = make
endif

all:
	@echo "pass ext_phy"

# all_targets += librtkphy libctcphy

# all: $(all_targets)
# 	$(CC)  -shared -fPIC -Wl,--whole-archive $(wildcard $(BUILD_OUTPUT)/*.a)  -Wl,--no-whole-archive -ldl -Wl,-soname  -o $(BUILD_OUTPUT)/$(PROGRAM)
# 	@if [ ! -d ${common_out_put_dir} ]; then mkdir -p ${common_out_put_dir} ;fi
# 	cp -p $(BUILD_OUTPUT)/$(PROGRAM) $(common_out_put_dir)/../

# librtkphy:
# 	@echo "GEN => $@"
# 	$(CTC_MAKE) phy-a -C rtk
# 	@if [ ! -d ${BUILD_OUTPUT} ]; then mkdir -p ${BUILD_OUTPUT} ;fi
# 	cp rtk/module/phy/a/libphy.a $(BUILD_OUTPUT)/librtkphy.a

# libctcphy:
# 	@echo "GEN => $@"
# 	$(CTC_MAKE) -C ctc -f Makefile.app
# 	@if [ ! -d ${BUILD_OUTPUT} ]; then mkdir -p ${BUILD_OUTPUT} ;fi
# 	cp ctc/out.app/lib/libphy.a $(BUILD_OUTPUT)/libctcphy.a